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

def monitor_continuously(system_info, metrics):
    print("\n--- Monitoring Started ---")
    print("Press Ctrl+C to stop monitoring.")
    with open("output.txt", "w") as f:
        f.write(f"Hostname: {system_info['Hostname']}\n")
        f.write(f"IP Address: {system_info['IP Address']}\n")
        f.write("Monitoring Results:\n")
        try:
            while True:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                stats = []
                for metric in metrics:
                    value = get_metric_value(metric)
                    stats.append(f"{metric}: {value}")
                line = f"{timestamp} | " + " | ".join(stats)
                print(line)
                f.write(line + "\n")
                f.flush()
                time.sleep(2)  # Sample every 2 seconds
        except KeyboardInterrupt:
            print("\nMonitoring stopped. Results saved to output.txt")

def main():
    system_info = get_system_info()
    metrics = get_metrics_list()
    display_info(system_info, metrics)
    monitor_continuously(system_info, metrics)

if __name__ == "__main__":
    main()