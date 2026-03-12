def get_system_info():
    hostname = input("Enter the hostname of the system: ")
    ip_address = input("Enter the IP address of the system: ")
    return {"Hostname": hostname, "IP Address": ip_address}

def get_metrics_list():
    print("Enter system metrics to monitor (e.g., cpu-usage, disk-usage). Type 'done' to finish.")
    metrics = []
    while True:
        metric = input("Metric name (or 'done'): ").strip()
        if metric.lower() == "done":
            break
        if metric:
            metrics.append(metric)
    return metrics

def display_info(system_info, metrics):
    print("\n--- System Monitoring Setup ---")
    print(f"Hostname    : {system_info['Hostname']}")
    print(f"IP Address  : {system_info['IP Address']}")
    print("\nMetrics to monitor:")
    for i, metric in enumerate(metrics, 1):
        print(f"  {i}. {metric}")

def main():
    system_info = get_system_info()
    metrics = get_metrics_list()
    display_info(system_info, metrics)

if __name__ == "__main__":
    main()