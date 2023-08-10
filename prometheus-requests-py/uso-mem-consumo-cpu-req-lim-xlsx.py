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
import urllib3
urllib3.disable_warnings()
import os
import time
import pandas as pd

# cargamos la url de la ruta prometheus de la variable de entorno 
prometheus_url = os.environ['PROMETHEUS_URL']

# cargamos la url de la ruta prometheus de la variable de entorno 
token = os.environ['TOKEN']


# Funcion para hacer la llamada al API con los parametros
def fetch_metrics(query):
    global data
    params = {
        "query": query
    }
    headers = {
        "Authorization": "Bearer " + token
    }
    response = requests.get(prometheus_url, params=params, headers=headers, verify=False)

    # Comprobacion de llamada correcta al API
    if response.status_code == 200:
        data = response.json()
    return data["data"]["result"]


# Namespaces sin Resource Quota
namespaces_sin_quota_query = f"count by (namespace)(kube_namespace_labels) unless sum by (namespace)(kube_resourcequota)"
namespaces_sin_quota = fetch_metrics(namespaces_sin_quota_query)
quota_data = []

# extraemos los valores de data iterando con values
for value in namespaces_sin_quota:
    namespace = value["metric"]["namespace"]
    quota_data.append([namespace])

print("En proceso: Carga de los Namespaces sin quota: " )

# Convertimos la info recogida en un DataFrame
quotas_df = pd.DataFrame(quota_data, columns=['Namespaces sin Quota'])

# Numero de CPU/cores infrautilizadas en el cluster
cores_infrautilizadas_query = f'sum((rate(container_cpu_usage_seconds_total{{container!="POD", container!=""}}[30m])- on (namespace, pod, container) group_left avg by (namespace, pod, container) (kube_pod_container_resource_requests{{resource="cpu"}})) * -1 >0)'
cores_infrautilizadas = fetch_metrics(cores_infrautilizadas_query)
cores_infrautilizadas_data = []


# extraemos los valores de data iterando con values
for value in cores_infrautilizadas:
    print(f"Cores infrautilizadas: {value}" )
    cores = value
    cores_infrautilizadas_data.append([cores])

print("En proceso: Carga del numero de cores infrautilizadas: " )


# Convertimos la info recogida en un DataFrame
cores_df = pd.DataFrame(cores_infrautilizadas_data, columns=['Numero de cores Infrautilizadas'])


# Funcion para cargar primero los namespaces y despues las metricas que queremos ejecutar
def main():
    namespaces = fetch_metrics('label_replace(kube_pod_info, "namespace", "$1", "namespace", "(.*)")')
    all_data = []
    print("En proceso: Carga de las metricas CPU/MEM y req/limits")

    for ns in namespaces:
        namespace = ns['metric']['namespace']

        # Memory Usage Total y CPU Usage Total por Pods/Containers
        memory_usage_total_query = f'sum(container_memory_usage_bytes{{namespace="{namespace}", container!="POD", container!=""}}) by (pod, container)'
        cpu_usage_total_query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", container!="POD", container!=""}}[1d])) by (pod, container)'

        memory_usage_total_data = fetch_metrics(memory_usage_total_query)
        cpu_usage_total_data = fetch_metrics(cpu_usage_total_query)

        # Memory Requests, CPU Requests, Memory Limits, CPU Limits por Pods/Containers
        memory_requests_query = f'sum(kube_pod_container_resource_requests{{namespace="{namespace}", container!="POD",container!="",resource="memory"}}) by (pod, container)'
        cpu_requests_query = f'sum(kube_pod_container_resource_requests{{namespace="{namespace}", container!="POD",container!="", resource="cpu"}}) by (pod, container)'
        memory_limits_query = f'sum(kube_pod_container_resource_limits{{namespace="{namespace}", container!="POD",container!="",resource="memory"}}) by (pod, container)'
        cpu_limits_query = f'sum(kube_pod_container_resource_limits{{namespace="{namespace}", container!="POD",container!="",resource="cpu"}}) by (pod, container)'

        memory_requests_data = fetch_metrics(memory_requests_query)
        cpu_requests_data = fetch_metrics(cpu_requests_query)
        memory_limits_data = fetch_metrics(memory_limits_query)
        cpu_limits_data = fetch_metrics(cpu_limits_query)

        for data in memory_usage_total_data:
            pod = data['metric']['pod']
            container = data['metric']['container']
            memory_usage_total = data['value'][1]

            # Buscamos el correspondiente CPU Usage Total
            for cpu_data in cpu_usage_total_data:
                if cpu_data['metric']['pod'] == pod and cpu_data['metric']['container'] == container:
                    cpu_usage_total = cpu_data['value'][1]
                    break
            else:
                cpu_usage_total = 0

            # Buscamos el correspondiente Memory Requests, CPU Requests, Memory Limits, CPU Limits
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

            # Añadimos con la funcion append
            all_data.append([namespace, pod, container, memory_usage_total, cpu_usage_total, memory_requests, memory_limits, cpu_requests, cpu_limits])

    # Convertimos la info recogida en un DataFrame
    df = pd.DataFrame(all_data, columns=['Namespace', 'Pod', 'Container', 'Memory Usage Total', 'CPU Usage Total',
                                         'Memory Requests', 'Memory Limits', 'CPU Requests', 'CPU Limits'])
    df2 = df.drop_duplicates()

    print("En proceso: Creacion y carga de la hoja Excel")

    # Escribimos directamente a CSV y excel
    with pd.ExcelWriter('/tmp/metrics_data.xlsx') as writer:
        df2.to_excel(writer, sheet_name='Total Metricas')
        quotas_df.to_excel(writer, sheet_name='Ns sin Quota')
        cores_df.to_excel(writer, sheet_name='Nº Cores Infrautilizadas')

if __name__ == '__main__':
    main()