import psutil
import time

def get_system_info():
    hostname = input("Enter the hostname of the system: ")
    ip_address = input("Enter the IP address of the system: ")
    return {"Hostname": hostname, "IP Address": ip_address}

def get_metrics_list():
    print("Enter system metrics to monitor (e.g., cpu-usage, disk-usage). Type 'done' to finish.")
    supported_metrics = ['cpu-usage', 'disk-usage', 'memory-usage']
    print(f"Supported metrics: {', '.join(supported_metrics)}")
    metrics = []
    while True:
        metric = input("Metric name (or 'done'): ").strip()
        if metric.lower() == "done":
            break
        if metric in supported_metrics:
            metrics.append(metric)
        elif metric:
            print("Unsupported metric. Try again.")
    return metrics

def get_metric_value(metric):
    if metric == 'cpu-usage':
        return f"{psutil.cpu_percent(interval=1)}%"
    elif metric == 'disk-usage':
        disk = psutil.disk_usage('/')
        return f"{disk.percent}% (used {disk.used // (1024 ** 3)}GB of {disk.total // (1024 ** 3)}GB)"
    elif metric == 'memory-usage':
        mem = psutil.virtual_memory()
        return f"{mem.percent}% (used {mem.used // (1024 ** 3)}GB of {mem.total // (1024 ** 3)}GB)"
    else:
        return "N/A"

def display_info(system_info, metrics):
    print("\n--- System Monitoring Setup ---")
    print(f"Hostname    : {system_info['Hostname']}")
    print(f"IP Address  : {system_info['IP Address']}")
    print("\nMetrics to monitor:")
    for i, metric in enumerate(metrics, 1):
        print(f"  {i}. {metric}")

def monitor(system_info, metrics):
    print("\n--- Monitoring Started ---")
    output = []
    # Monitor once (you can loop for continuous monitoring)
    stats = {}
    for metric in metrics:
        stats[metric] = get_metric_value(metric)
        print(f"{metric}: {stats[metric]}")
    output.append(f"Hostname: {system_info['Hostname']}")
    output.append(f"IP Address: {system_info['IP Address']}")
    output.append("Monitoring Results:")
    for metric in metrics:
        output.append(f"{metric}: {stats[metric]}")
    with open("output.txt", "w") as f:
        f.write("\n".join(output))
    print("\nResults saved to output.txt")

def main():
    system_info = get_system_info()
    metrics = get_metrics_list()
    display_info(system_info, metrics)
    monitor(system_info, metrics)

if __name__ == "__main__":
    main()