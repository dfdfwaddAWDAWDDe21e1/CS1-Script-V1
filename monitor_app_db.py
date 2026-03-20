from __future__ import annotations

import argparse
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import psutil


DB_FILE = Path("data/measurements.db")
RECOGNIZED_METRICS = {"cpu_usage", "memory_usage", "disk_usage"}


def ensure_database(db_path: Path) -> None:
    """Create the database and table if they do not exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            target_name TEXT NOT NULL,
            target_ip TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def measure_metric(metric_name: str) -> float:
    """Measure a supported system metric."""
    if metric_name == "cpu_usage":
        return round(psutil.cpu_percent(interval=1), 2)

    if metric_name == "memory_usage":
        return round(psutil.virtual_memory().percent, 2)

    if metric_name == "disk_usage":
        return round(psutil.disk_usage("/").percent, 2)

    raise ValueError(f"Unsupported metric: {metric_name}")


def validate_metrics(metrics: list[str]) -> list[str]:
    """Validate that all provided metrics are supported."""
    invalid_metrics = [metric for metric in metrics if metric not in RECOGNIZED_METRICS]

    if invalid_metrics:
        supported = ", ".join(sorted(RECOGNIZED_METRICS))
        invalid = ", ".join(invalid_metrics)
        raise argparse.ArgumentTypeError(
            f"Unsupported metric(s): {invalid}. Supported: {supported}"
        )

    return metrics


def collect_measurements(
    db_path: Path,
    target_name: str,
    target_ip: str,
    metrics: list[str],
    duration: int,
    interval: int,
) -> None:
    """Collect measurements and store them in the SQLite database."""
    ensure_database(db_path)

    if interval < 1:
        raise ValueError("Interval must be at least 1 second.")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    start_time = time.monotonic()
    cycles = 0
    rows_added = 0

    while True:
        timestamp = datetime.now().isoformat(timespec="seconds")

        for metric in metrics:
            value = measure_metric(metric)
            cursor.execute(
                """
                INSERT INTO measurements (timestamp, target_name, target_ip, metric, value)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, target_name, target_ip, metric, value),
            )
            rows_added += 1

        connection.commit()
        cycles += 1

        if duration <= 0:
            break

        elapsed = time.monotonic() - start_time
        remaining = duration - elapsed

        if remaining <= 0:
            break

        time.sleep(min(interval, remaining))

    connection.close()

    print("Measurements collected successfully.")
    print(f"Target name : {target_name}")
    print(f"Target IP   : {target_ip}")
    print(f"Cycles run  : {cycles}")
    print(f"Rows added  : {rows_added}")
    print(f"Saved to    : {db_path}")


def parse_timestamp(timestamp_text: str) -> datetime:
    """Parse timestamps in ISO format."""
    try:
        return datetime.fromisoformat(timestamp_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS"
        ) from exc


def show_measurements(
    db_path: Path,
    metric: str | None,
    start: datetime | None,
    end: datetime | None,
    stats: bool,
) -> None:
    """Read measurements from the database and display them."""
    ensure_database(db_path)

    query = """
        SELECT timestamp, target_name, target_ip, metric, value
        FROM measurements
        WHERE 1=1
    """
    parameters: list[object] = []

    if metric:
        query += " AND metric = ?"
        parameters.append(metric)

    if start:
        query += " AND timestamp >= ?"
        parameters.append(start.isoformat(timespec="seconds"))

    if end:
        query += " AND timestamp <= ?"
        parameters.append(end.isoformat(timespec="seconds"))

    query += " ORDER BY timestamp ASC, id ASC"

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(query, parameters)
    rows = cursor.fetchall()
    connection.close()

    if not rows:
        print("No measurements found for the selected filters.")
        return

    print("=" * 80)
    print(
        f"{'Timestamp':<22} {'Target':<15} {'IP Address':<15} "
        f"{'Metric':<15} {'Value':>8}"
    )
    print("=" * 80)

    for row in rows:
        timestamp_value, target_name, target_ip, metric_name, metric_value = row
        print(
            f"{timestamp_value:<22} {target_name:<15} {target_ip:<15} "
            f"{metric_name:<15} {metric_value:>8.2f}"
        )

    print("=" * 80)

    if stats:
        numeric_values = [row[4] for row in rows]
        average_value = sum(numeric_values) / len(numeric_values)
        total_value = sum(numeric_values)

        print("Statistics")
        print("-" * 20)
        print(f"Count   : {len(numeric_values)}")
        print(f"Average : {average_value:.2f}")
        print(f"Total   : {total_value:.2f}")


def reset_database(db_path: Path) -> None:
    """Delete all measurement data and recreate the database structure."""
    if db_path.exists():
        db_path.unlink()

    ensure_database(db_path)
    print(f"Database reset: {db_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Knowledge Hub Monitoring Application - Task 11"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser(
        "collect",
        help="Measure recognized metrics and store them in SQLite",
    )
    collect_parser.add_argument("--target-name", required=True, help="System hostname")
    collect_parser.add_argument("--target-ip", required=True, help="System IP address")
    collect_parser.add_argument(
        "--metrics",
        nargs="+",
        required=True,
        help="Metrics to collect",
    )
    collect_parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Total collection time in seconds. Use 0 for one collection cycle.",
    )
    collect_parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Seconds between collection cycles.",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="Display stored measurements from SQLite",
    )
    show_parser.add_argument(
        "--metric",
        choices=sorted(RECOGNIZED_METRICS),
        help="Filter by one metric",
    )
    show_parser.add_argument(
        "--start",
        type=parse_timestamp,
        help="Start datetime in format YYYY-MM-DDTHH:MM:SS",
    )
    show_parser.add_argument(
        "--end",
        type=parse_timestamp,
        help="End datetime in format YYYY-MM-DDTHH:MM:SS",
    )
    show_parser.add_argument(
        "--stats",
        action="store_true",
        help="Show average, total, and count",
    )

    reset_parser = subparsers.add_parser(
        "reset",
        help="Clear all stored measurements",
    )
    reset_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm database reset",
    )

    return parser


def main() -> None:
    """Main program execution."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "collect":
        metrics = validate_metrics(args.metrics)
        collect_measurements(
            db_path=DB_FILE,
            target_name=args.target_name,
            target_ip=args.target_ip,
            metrics=metrics,
            duration=args.duration,
            interval=args.interval,
        )
        return

    if args.command == "show":
        show_measurements(
            db_path=DB_FILE,
            metric=args.metric,
            start=args.start,
            end=args.end,
            stats=args.stats,
        )
        return

    if args.command == "reset":
        if not args.confirm:
            print("Use --confirm to reset the database.")
            return

        reset_database(DB_FILE)
        return


if __name__ == "__main__":
    main()