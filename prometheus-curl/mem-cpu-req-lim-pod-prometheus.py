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

