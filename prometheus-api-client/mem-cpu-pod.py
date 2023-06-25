#
# Acceso via libreria directa de openshift
#

from openshift import client, config
import pandas as pd

# Connect to the OpenShift cluster
config.load_kube_config()

# Create an OpenShift API client
v1 = client.CoreV1Api()

# Get all pods in the cluster
pods = v1.list_pod_for_all_namespaces(watch=False)

# Initialize lists to store data
data = []
headers = ['Namespace', 'Pod', 'Container', 'CPU Request', 'CPU Limit', 'Memory Request', 'Memory Limit']

# Iterate over the pods and extract the required information
for pod in pods.items:
    namespace = pod.metadata.namespace
    pod_name = pod.metadata.name

    for container in pod.spec.containers:
        container_name = container.name
        cpu_request = container.resources.requests.get('cpu', 'N/A')
        cpu_limit = container.resources.limits.get('cpu', 'N/A')
        mem_request = container.resources.requests.get('memory', 'N/A')
        mem_limit = container.resources.limits.get('memory', 'N/A')

        data.append([namespace, pod_name, container_name, cpu_request, cpu_limit, mem_request, mem_limit])

# Create a pandas DataFrame from the extracted data
df = pd.DataFrame(data, columns=headers)

# Write the DataFrame to an Excel file
output_file = 'pod_stats.xlsx'
df.to_excel(output_file, index=False)
print(f"Data exported to {output_file} successfully.")

