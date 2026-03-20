from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

import psutil


DATA_FILE = Path("data/measurements.csv")
RECOGNIZED_METRICS = {"cpu_usage", "memory_usage", "disk_usage"}


def ensure_data_file(file_path: Path) -> None:
    """Create the data directory and CSV header if needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        with file_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["timestamp", "target_name", "target_ip", "metric", "value"]
            )


def measure_metric(metric_name: str) -> float:
    """Return the current value of a recognized metric."""
    if metric_name == "cpu_usage":
        return round(psutil.cpu_percent(interval=1), 2)

    if metric_name == "memory_usage":
        return round(psutil.virtual_memory().percent, 2)

    if metric_name == "disk_usage":
        return round(psutil.disk_usage("/").percent, 2)

    raise ValueError(f"Unsupported metric: {metric_name}")


def collect_measurements(
    target_name: str,
    target_ip: str,
    metrics: Iterable[str],
    file_path: Path,
) -> None:
    """Measure metrics and append results to the CSV file."""
    ensure_data_file(file_path)
    timestamp = datetime.now().isoformat(timespec="seconds")

    rows_written = 0

    with file_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        for metric in metrics:
            value = measure_metric(metric)
            writer.writerow([timestamp, target_name, target_ip, metric, value])
            rows_written += 1

    print("Measurements collected successfully.")
    print(f"Timestamp   : {timestamp}")
    print(f"Target name : {target_name}")
    print(f"Target IP   : {target_ip}")
    print(f"Rows added  : {rows_written}")
    print(f"Saved to    : {file_path}")


def parse_timestamp(timestamp_text: str) -> datetime:
    """Parse ISO-like timestamps such as 2026-03-18T10:00:00."""
    try:
        return datetime.fromisoformat(timestamp_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS"
        ) from exc


def read_measurements(file_path: Path) -> list[dict[str, str]]:
    """Read all measurements from the CSV file."""
    if not file_path.exists():
        return []

    with file_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def filter_measurements(
    rows: list[dict[str, str]],
    metric: str | None,
    start: datetime | None,
    end: datetime | None,
) -> list[dict[str, str]]:
    """Filter measurements by metric and time range."""
    filtered_rows: list[dict[str, str]] = []

    for row in rows:
        row_time = datetime.fromisoformat(row["timestamp"])

        if metric and row["metric"] != metric:
            continue
        if start and row_time < start:
            continue
        if end and row_time > end:
            continue

        filtered_rows.append(row)

    return filtered_rows


def print_measurements(rows: list[dict[str, str]]) -> None:
    """Display measurements in a readable format."""
    if not rows:
        print("No measurements found for the selected filters.")
        return

    print("=" * 78)
    print(
        f"{'Timestamp':<22} {'Target':<15} {'IP Address':<15} "
        f"{'Metric':<15} {'Value':>6}"
    )
    print("=" * 78)

    for row in rows:
        print(
            f"{row['timestamp']:<22} "
            f"{row['target_name']:<15} "
            f"{row['target_ip']:<15} "
            f"{row['metric']:<15} "
            f"{row['value']:>6}"
        )

    print("=" * 78)


def print_statistics(rows: list[dict[str, str]]) -> None:
    """Display optional statistics for the selected rows."""
    if not rows:
        return

    numeric_values = [float(row["value"]) for row in rows]
    average_value = sum(numeric_values) / len(numeric_values)
    total_value = sum(numeric_values)

    print("Statistics")
    print("-" * 20)
    print(f"Count   : {len(numeric_values)}")
    print(f"Average : {average_value:.2f}")
    print(f"Total   : {total_value:.2f}")


def clear_data(file_path: Path) -> None:
    """Delete the existing data file and recreate it cleanly."""
    if file_path.exists():
        file_path.unlink()

    ensure_data_file(file_path)
    print(f"Data file reset: {file_path}")


def validate_metrics(metrics: list[str]) -> list[str]:
    """Validate the provided metric names."""
    invalid_metrics = [metric for metric in metrics if metric not in RECOGNIZED_METRICS]

    if invalid_metrics:
        raise argparse.ArgumentTypeError(
            f"Unsupported metric(s): {', '.join(invalid_metrics)}. "
            f"Supported: {', '.join(sorted(RECOGNIZED_METRICS))}"
        )

    return metrics


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Knowledge Hub Monitoring Application - Task 10"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser(
        "collect",
        help="Measure recognized metrics and append them to disk",
    )
    collect_parser.add_argument("--target-name", required=True, help="System hostname")
    collect_parser.add_argument("--target-ip", required=True, help="System IP address")
    collect_parser.add_argument(
        "--metrics",
        nargs="+",
        required=True,
        help="Metrics to collect",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="Display stored measurements with optional filtering",
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
        help="Show statistics such as average and total",
    )

    reset_parser = subparsers.add_parser(
        "reset",
        help="Clear stored measurements and start with a clean file",
    )
    reset_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm that the file should be reset",
    )

    return parser


def main() -> None:
    """Run the monitoring application."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "collect":
        metrics = validate_metrics(args.metrics)
        collect_measurements(
            target_name=args.target_name,
            target_ip=args.target_ip,
            metrics=metrics,
            file_path=DATA_FILE,
        )
        return

    if args.command == "show":
        rows = read_measurements(DATA_FILE)
        filtered_rows = filter_measurements(
            rows=rows,
            metric=args.metric,
            start=args.start,
            end=args.end,
        )
        print_measurements(filtered_rows)

        if args.stats:
            print_statistics(filtered_rows)
        return

    if args.command == "reset":
        if not args.confirm:
            print("Use --confirm to reset the data file.")
            return

        clear_data(DATA_FILE)
        return


if __name__ == "__main__":
    main()