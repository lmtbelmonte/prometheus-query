import requests
import pandas as pd

# Replace with your Openshift Prometheus API endpoint
PROMETHEUS_API_ENDPOINT = "http://prometheus.openshift.example.com/api/v1/query"

def get_metrics(query, start_time, end_time):
    params = {
        "query": query,
        "start": start_time,
        "end": end_time,
        "step": "30d"  # Modify the step size based on your needs
    }
    response = requests.get(PROMETHEUS_API_ENDPOINT, params=params)
    data = response.json()
    return data["data"]["result"]

def extract_metrics(start_time, end_time):
    metrics = [
        ("memory_usage_total", "sum(container_memory_usage_bytes{container_name!=\"POD\"}) by (namespace, pod)"),
        ("cpu_usage", "sum(rate(container_cpu_usage_seconds_total{container_name!=\"POD\"}[1m])) by (namespace, pod)"),
        ("memory_requests", "sum(kube_pod_container_resource_requests_memory_bytes) by (namespace, pod)"),
        ("cpu_requests", "sum(kube_pod_container_resource_requests_cpu_cores) by (namespace, pod)"),
        ("memory_limits", "sum(kube_pod_container_resource_limits_memory_bytes) by (namespace, pod)"),
        ("cpu_limits", "sum(kube_pod_container_resource_limits_cpu_cores) by (namespace, pod)")
    ]

    metrics_data = {}
    for metric_name, query in metrics:
        data = get_metrics(query, start_time, end_time)
        for result in data:
            labels = result["metric"]
            namespace = labels["namespace"]
            pod = labels["pod"]
            value = result["value"][1]
            if namespace not in metrics_data:
                metrics_data[namespace] = {}
            metrics_data[namespace][pod] = metrics_data[namespace].get(pod, {})
            metrics_data[namespace][pod][metric_name] = value

    return metrics_data

def save_to_excel(metrics_data, filename):
    df = pd.DataFrame.from_dict({(i, j): metrics_data[i][j]
                                 for i in metrics_data.keys()
                                 for j in metrics_data[i].keys()}, orient='index')
    df.index = pd.MultiIndex.from_tuples(df.index, names=['Namespace', 'Pod'])
    df.reset_index(inplace=True)
    df.to_excel(filename, index=False)

if __name__ == "__main__":
    start_time = "2023-01-01T00:00:00Z"
    end_time = "2023-02-01T00:00:00Z"
    filename = "metrics.xlsx"

    metrics_data = extract_metrics(start_time, end_time)
    save_to_excel(metrics_data, filename)

