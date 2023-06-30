import requests
import pandas as pd

# Prometheus API endpoint
prometheus_url = "https://prometheus-k8s-openshift-monitoring.apps.cluster-crh57.crh57.sandbox944.opentlc.com/ token= sha256~rpsHkivZN5yyYuto-F6C2hI-ICoisUZEQt74uZRPXj0"

# Prometheus query for extracting metrics
query = '''
    sum(container_memory_usage_bytes{job="kubelet", image!="", container!="POD"})
        by (container_name, namespace)
    /
    sum(kube_pod_container_resource_limits_memory_bytes)
        by (container_name, namespace)
'''

# Request parameters
params = {
    "query": query,
    "time": "1m",
}

# Make a GET request to Prometheus
response = requests.get(prometheus_url, params=params)

# Parse the JSON response
data = response.json()

# Extract the values from the response
values = data["data"]["result"]

# Create a DataFrame to store the metrics
metrics_df = pd.DataFrame(columns=["Container", "Namespace", "Memory Usage", "CPU Usage"])

# Iterate over the values and extract the required data
for value in values:
    container = value["metric"]["container_name"]
    namespace = value["metric"]["namespace"]
    memory_usage = float(value["value"][1])
    cpu_usage = float(value["value"][1])
    metrics_df = metrics_df.append({
        "Container": container,
        "Namespace": namespace,
        "Memory Usage": memory_usage,
        "CPU Usage": cpu_usage
    }, ignore_index=True)

# Export the metrics to an Excel file
metrics_df.to_excel("metrics.xlsx", index=False)
