from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import List


@dataclass
class MonitorTarget:
    hostname: str
    ip_address: str
    metrics: List[str]


def ask_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty. Try again.")


def ask_ip(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError:
            print("Invalid IP address. Example: 10.10.20.30")


def ask_metrics() -> List[str]:
    print("\nEnter metric names one by one (press Enter on an empty line to finish).")
    metrics: List[str] = []

    while True:
        metric = input("Metric name: ").strip()
        if metric == "":
            break
        metrics.append(metric)

    if not metrics:
        print("No metrics entered. A default list will be used.")
        return ["cpu_usage", "memory_usage"]

    return metrics


def print_summary(target: MonitorTarget) -> None:
    print("\n" + "=" * 50)
    print("Monitoring Target Summary")
    print("=" * 50)
    print(f"Hostname   : {target.hostname}")
    print(f"IP Address : {target.ip_address}")
    print("Metrics    :")
    for idx, metric in enumerate(target.metrics, start=1):
        print(f"  {idx}. {metric}")
    print("=" * 50 + "\n")


def main() -> None:
    print("Knowledge Hub - Monitoring Setup (Phase 1 Script)\n")

    hostname = ask_non_empty("Enter the system hostname: ")
    ip_addr = ask_ip("Enter the system IP address: ")
    metrics = ask_metrics()

    target = MonitorTarget(hostname=hostname, ip_address=ip_addr, metrics=metrics)
    print_summary(target)


if __name__ == "__main__":
    main()