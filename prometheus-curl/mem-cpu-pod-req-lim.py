
from kubernetes import client, config

def get_resource_consumption(api_client, namespace):
    v1_api = client.CoreV1Api(api_client)
    pod_list = v1_api.list_namespaced_pod(namespace)

    for pod in pod_list.items:
        pod_name = pod.metadata.name
        containers = pod.spec.containers
        for container in containers:
            container_name = container.name
            container_resource = container.resources
            if container_resource and container_resource.requests:
                cpu_request = container_resource.requests.get('cpu', None)
                memory_request = container_resource.requests.get('memory', None)
                if cpu_request:
                    print(f"Namespace: {namespace}, Pod: {pod_name}, Container: {container_name}")
                    print(f"CPU Request: {cpu_request}")
                if memory_request:
                    print(f"Namespace: {namespace}, Pod: {pod_name}, Container: {container_name}")
                    print(f"Memory Request: {memory_request}")

def main():
    # Load the cluster configuration from the kubeconfig file
    config.load_kube_config()

    # Create an API client
    api_client = client.ApiClient()

    # Get all namespaces in the cluster
    v1_api = client.CoreV1Api(api_client)
    namespaces = v1_api.list_namespace().items

    # Iterate over each namespace and extract resource consumption
    for namespace in namespaces:
        namespace_name = namespace.metadata.name
        get_resource_consumption(api_client, namespace_name)

if __name__ == '__main__':
    main()

# exportamos la variable PROMETHEUS_URL con la ruta que expone el OCP (en mi caso para pruebas)
export URL=https://prometheus-k8s-openshift-monitoring.apps.cluster-crh57.crh57.sandbox944.opentlc.com/

# extraemos las metricas y formatemaos en json con jq

curl -s -G -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' -H 'Content-Type: application/json' "$PROMETHEUS_URL/query"  --data-urlencode 'query=avg_over_time(container_memory_max_usage_bytes{image!="",container!=""}[1d])' --data-urlencode 'step=15m' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .values[]] | @csv' > memory.csv


curl -s -G -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' -H 'Content-Type: application/json' \
"$PROMETHEUS_URL/api/v1/query_range" \
--data-urlencode 'query=avg_over_time(container_memory_max_usage_bytes{image!="",container!=""})' \
--data-urlencode 'start=2023-06-26T07:00:00.000Z' \
--data-urlencode 'end=2023-06-26T09:00:00.000Z' \
--data-urlencode 'step=15m' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .values[]] | @csv' > memory.csv

curl -s -G "PROMETHEUS_URL/api/v1/query_range" \
  --data-urlencode 'query=avg_over_time(container_cpu_usage_seconds_total{image!="",container!=""}[30d])' \
  --data-urlencode 'step=1d' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .values[]] | @csv' > cpu.csv

curl -s -G "PROMETHEUS_URL/api/v1/query" \
  --data-urlencode 'query=kube_pod_container_resource_requests' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .value] | @csv' > requests.csv

curl -s -G "PROMETHEUS_URL/api/v1/query" \
  --data-urlencode 'query=kube_pod_container_resource_limits' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .value] | @csv' > limits.csv

# Utilizamos csvstack para combinar los datos en un solo csv
csvstack memory.csv cpu.csv requests.csv limits.csv | csvformat -T > metrics.csv

# Con csvformat convertimos a excel el CSV 
csvformat -T -U 1 metrics.csv > metrics-$(date +%d-%m-%Y).xlsx

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


import pandas as pd
from prometheus_api_client import PrometheusConnect

# Prometheus server URL
prometheus_url = "https://prometheus-k8s-openshift-monitoring.apps.cluster-crh57.crh57.sandbox944.opentlc.com/api/v1/query"

# Query to fetch the required metrics
query = 'kube_pod_container_resource_requests_memory_bytes, kube_pod_container_resource_requests_cpu_cores, kube_pod_container_resource_limits_memory_bytes, kube_pod_container_resource_limits_cpu_cores, container_memory_usage_bytes, container_cpu_usage_seconds_total'

# Connect to Prometheus
prometheus = PrometheusConnect(url=prometheus_url)

# Get the metric data
data = prometheus.custom_query(query)

# Convert the data to a Pandas DataFrame
df = pd.DataFrame(data)

# Extract relevant information from the DataFrame
df['month'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m')
df['namespace'] = df['metric.namespace']
df['pod'] = df['metric.pod']
df['container'] = df['metric.container']
df['memory_requests'] = df['value'][0]
df['cpu_requests'] = df['value'][1]
df['memory_limits'] = df['value'][2]
df['cpu_limits'] = df['value'][3]
df['memory_usage'] = df['value'][4]
df['cpu_usage'] = df['value'][5]

# Filter and reorganize the DataFrame
df_filtered = df[['month', 'namespace', 'pod', 'container', 'memory_requests', 'cpu_requests', 'memory_limits', 'cpu_limits', 'memory_usage', 'cpu_usage']]

# Save the data to an Excel file
output_file = 'pod_metrics.xlsx'
df_filtered.to_excel(output_file, index=False)
print(f"Data saved to {output_file}")

import requests
import pandas as pd

def get_thanos_metrics(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch Thanos metrics:", response.status_code)
        return None

def extract_pod_metrics(metrics):
    pod_metrics = []
    for metric in metrics:
        container = metric['metric']['container']
        namespace = metric['metric']['namespace']
        pod = metric['metric']['pod']
        month = metric['metric']['month']
        memory_usage = float(metric['values']['memory_usage'])
        cpu_usage = float(metric['values']['cpu_usage'])
        request_cpu = float(metric['values']['request_cpu'])
        request_memory = float(metric['values']['request_memory'])
        limit_cpu = float(metric['values']['limit_cpu'])
        limit_memory = float(metric['values']['limit_memory'])
        
        pod_metrics.append({
            'Container': container,
            'Namespace': namespace,
            'Pod': pod,
            'Month': month,
            'Memory Usage': memory_usage,
            'CPU Usage': cpu_usage,
            'Request CPU': request_cpu,
            'Request Memory': request_memory,
            'Limit CPU': limit_cpu,
            'Limit Memory': limit_memory
        })
    return pod_metrics

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print("Data saved to", filename)

if __name__ == '__main__':
    thanos_url = 'https://thanos-querier-openshift-monitoring.apps.cluster-crh57.crh57.sandbox944.opentlc.com/api'  # Replace with your Thanos metrics URL
    metrics = get_thanos_metrics(thanos_url)
    if metrics:
        pod_metrics = extract_pod_metrics(metrics)
        save_to_excel(pod_metrics, 'pod_metrics.xlsx')  # Replace with your desired filename
