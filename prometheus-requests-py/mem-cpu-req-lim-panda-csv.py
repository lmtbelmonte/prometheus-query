# autor : Luis Merino Troncoso
# Fecha : 12/07/2023
#
# Descripcion : Extraccion de datos de Prometheus metrics:
#                 - memory_usage_total 
#                 - cpu_usage_total 
#                 - memory_requests 
#                 - cpu_requests
#                 - memory_limits
#                 - cpu_limits
#               de Openshift a traves del Api de openshift y del de Prometheus generando un unico csv          
# Ejecucion   : Hay que crear las variables de entorno despues de hacer el oc login al cluster
#                  TOKEN: `oc whoami -t`
#                  prometheus_url: export PROMETHEUS_URL: <route a prometheus-k8s>/api/v1/query/ 
#               Hay que poner el intervalo de tiempo en fecha inicio y fin asi como el step ( en dd,hh, mm, ss) 

import requests
import os
import pandas as pd

# cargamos la url de la ruta prometheus de la variable de entorno 

prometheus_url = os.environ['PROMETHEUS_URL']

# cargamos la url de la ruta prometheus de la variable de entorno 

token = os.environ['TOKEN']

# Funcion para hacer la llamada al API con los parametros 

def fetch_metrics(query):
    response = requests.get(prometheus_url, params={'query': query}, headers={'Authorization': 'Bearer'+token},verify=False)
    data = response.json()
    return data['data']['result']

def main():
    namespaces = fetch_metrics('label_replace(kube_pod_info, "namespace", "$1", "namespace", "(.*)")')
    all_data = []

    for ns in namespaces:
        namespace = ns['metric']['namespace']

        # Memory Usage Total and CPU Usage Total by Pods and Containers
        memory_usage_total_query = f'sum(container_memory_usage_bytes{{namespace="{namespace}"}}) by (pod, container)'
        cpu_usage_total_query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[1m])) by (pod, container)'

        memory_usage_total_data = fetch_metrics(memory_usage_total_query)
        cpu_usage_total_data = fetch_metrics(cpu_usage_total_query)

        # Memory Requests, CPU Requests, Memory Limits, and CPU Limits by Pods and Containers
        memory_requests_query = f'sum(kube_pod_container_resource_requests_memory_bytes{{namespace="{namespace}"}}) by (pod, container)'
        cpu_requests_query = f'sum(kube_pod_container_resource_requests_cpu_cores{{namespace="{namespace}"}}) by (pod, container)'
        memory_limits_query = f'sum(kube_pod_container_resource_limits_memory_bytes{{namespace="{namespace}"}}) by (pod, container)'
        cpu_limits_query = f'sum(kube_pod_container_resource_limits_cpu_cores{{namespace="{namespace}"}}) by (pod, container)'

        memory_requests_data = fetch_metrics(memory_requests_query)
        cpu_requests_data = fetch_metrics(cpu_requests_query)
        memory_limits_data = fetch_metrics(memory_limits_query)
        cpu_limits_data = fetch_metrics(cpu_limits_query)

        for data in memory_usage_total_data:
            pod = data['metric']['pod']
            container = data['metric']['container']
            memory_usage_total = data['value'][1]

            # Find corresponding CPU Usage Total
            for cpu_data in cpu_usage_total_data:
                if cpu_data['metric']['pod'] == pod and cpu_data['metric']['container'] == container:
                    cpu_usage_total = cpu_data['value'][1]
                    break
            else:
                cpu_usage_total = 0

            # Find corresponding Memory Requests, CPU Requests, Memory Limits, and CPU Limits
            for req_data, lim_data in zip(memory_requests_data, memory_limits_data):
                if req_data['metric']['pod'] == pod and req_data['metric']['container'] == container:
                    memory_requests = req_data['value'][1]
                    memory_limits = lim_data['value'][1]
                    break
            else:
                memory_requests = 0
                memory_limits = 0

            for req_data, lim_data in zip(cpu_requests_data, cpu_limits_data):
                if req_data['metric']['pod'] == pod and req_data['metric']['container'] == container:
                    cpu_requests = req_data['value'][1]
                    cpu_limits = lim_data['value'][1]
                    break
            else:
                cpu_requests = 0
                cpu_limits = 0

            all_data.append([namespace, pod, container, memory_usage_total, cpu_usage_total, memory_requests, memory_limits, cpu_requests, cpu_limits])

    # Convert the collected data into a DataFrame
    df = pd.DataFrame(all_data, columns=['Namespace', 'Pod', 'Container', 'Memory Usage Total', 'CPU Usage Total',
                                         'Memory Requests', 'Memory Limits', 'CPU Requests', 'CPU Limits'])

    # Write to CSV
    df.to_csv('metrics_data.csv', index=False)

if __name__ == '__main__':
    main()
