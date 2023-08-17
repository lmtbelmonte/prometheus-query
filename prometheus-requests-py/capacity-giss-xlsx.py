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
#                 - Memory y CPU infrautilizada
#               de Openshift a traves del Api de openshift y del de Prometheus generando un unico csv          
# Ejecucion   : Hay que crear las variables de entorno despues de hacer el oc login al cluster
#                  TOKEN: `oc whoami -t`
#                  prometheus_url: export PROMETHEUS_URL: <route a prometheus-k8s>/api/v1/query/ 
#               Hay que poner el intervalo de tiempo en fecha inicio y fin asi como el step ( en dd,hh, mm, ss) 

import requests
import urllib3
urllib3.disable_warnings()
import time
import os
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
quotas_df = pd.DataFrame(quota_data,columns=['Namespaces sin Quota'])

# Numero de CPU/cores infrautilizadas en el cluster
cores_infrautilizadas_query = (f'sum((rate(container_cpu_usage_seconds_total{{container!="POD", container!=""}}[30m])'
                               f'- on (namespace, pod, container) group_left avg by (namespace, pod, container) '
                               f'(kube_pod_container_resource_requests{{resource="cpu"}})) * -1 >0)')
cores_infrautilizadas = fetch_metrics(cores_infrautilizadas_query)
cores_infrautilizadas_data = []

# extraemos los valores de data iterando con values
for value in cores_infrautilizadas:
    cores = value["value"][1]
    cores_infrautilizadas_data.append(["{:.4f}".format(float(cores))])

print("En proceso: Carga del número de cores infrautilizadas a nivel de cluster " )

# Convertimos la info recogida en un DataFrame
cores_df = pd.DataFrame(cores_infrautilizadas_data, columns=['Numero de cores Infrautilizadas'])

# Numero de CPU/cores infrautilizadas por namespace
cores_infrautilizadas_ns_query = (f'sum by (namespace)((rate(container_cpu_usage_seconds_total{{container!="POD",container!=""}}[30m])'
                                  f' - on (namespace,pod,container) group_left avg by (namespace,pod,container)'
                                  f'(kube_pod_container_resource_requests{{resource="cpu"}})) * -1 >0)')
cores_infrautilizadas_ns = fetch_metrics(cores_infrautilizadas_ns_query)
cores_infrautilizadas_ns_data = []

# extraemos los valores de data iterando con values
for value_ns in cores_infrautilizadas_ns:
    namespace = value_ns["metric"]["namespace"]
    cores = value_ns["value"][1]
    cores_infrautilizadas_ns_data.append([namespace,"{:.4f}".format(float(cores))])

print("En proceso: Carga del número de cores infrautilizadas a nivel de namespace: " )

# Convertimos la info recogida en un DataFrame
cores_ns_df = pd.DataFrame(cores_infrautilizadas_ns_data, columns=['Namespace','Número de cores Infrautilizadas NS'])

# Total Memoria infrautilizada en el cluster
memoria_infrautilizada_query = (f'sum((container_memory_usage_bytes{{container!="POD", container!=""}} '
                                f'- on (namespace, pod, container) avg by (namespace, pod, container) '
                                f'(kube_pod_container_resource_requests{{resource="memory"}})) * -1 >0) / (1024*1024*1024)')
memoria_infrautilizada = fetch_metrics(memoria_infrautilizada_query)
memoria_infrautilizada_data = []

# extraemos los valores de data iterando con values
for value_mem in memoria_infrautilizada:
    memoria = value_mem["value"][1]
    memoria_infrautilizada_data.append(["{:.4f}".format(float(memoria))])

print("En proceso: Carga del Total Memoria infrautilizada a nivel de cluster " )

# Convertimos la info recogida en un DataFrame
memoria_df = pd.DataFrame(memoria_infrautilizada_data, columns=['Memoria en GB Infrautilizada Cluster'])

# Total Memoria infrautilizada en el cluster por namespace
memoria_infrautilizada_ns_query = (f'sum by (namespace) ((container_memory_usage_bytes{{container!="POD", container!=""}}'
                                   f' - on (namespace, pod, container) avg by (namespace, pod, container) '
                                   f'(kube_pod_container_resource_requests{{resource="memory"}})) * -1 >0) / (1024*1024*1024)')
memoria_infrautilizada_ns = fetch_metrics(memoria_infrautilizada_ns_query)
memoria_infrautilizada_ns_data = []

# extraemos los valores de data iterando con values
for value_mem_ns in memoria_infrautilizada_ns:
    namespace = value_mem_ns["metric"]["namespace"]
    memoria_ns = value_mem_ns["value"][1]
    memoria_infrautilizada_ns_data.append([namespace, "{:.4f}".format(float(memoria_ns))])

print("En proceso: Carga del Total Memoria infrautilizada a nivel de Namespace " )

# Convertimos la info recogida en un DataFrame
memoria_ns_df = pd.DataFrame(memoria_infrautilizada_ns_data, columns=['Namespace','Memoria en GB Infrautilizada NS'])

# Top 10 containers con memoria infrautilizada
top10_containers_infra_query = (f'topk(10,sum by (namespace,pod,container)((container_memory_usage_bytes{{container!="POD",container!=""}}'
                                f' - on (namespace,pod,container) avg by (namespace,pod,container)'
                                f'(kube_pod_container_resource_requests{{resource="memory"}})) * -1 >0 ) / (1024*1024*1024)')
top10_containers_infra = fetch_metrics(top10_containers_infra_query)
top10_containers_infra_data = []

# extraemos los valores de data iterando con values
for value_top in top10_containers_infra:
    container_top = value_top["metric"]["container"]
    namespace_top = value_top["metric"]["namespace"]
    pod_top = value_top["metric"]["pod"]
    memory_top = value_top["value"][1]
    top10_containers_infra_data.append([container_top,namespace_top,pod_top,"{:.4f}".format(float(memory_top))])

print("En proceso: Carga de los Top 10 containers sobredimensionados:")

# Convertimos la info recogida en un DataFrame
top10_df = pd.DataFrame(top10_containers_infra_data, columns=['Container','Namespace','Pod', 'memoria sobrediimensionada'])

# Función para cargar primero los namespaces y despues las metricas que queremos ejecutar
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
            all_data.append([namespace, pod, container, "{:,}".format(float(memory_usage_total)), "{:.4f}".format(float(cpu_usage_total)),
                             "{:,}".format(float(memory_requests)), "{:,}".format(float(memory_limits)), float(cpu_requests), float(cpu_limits)])

    # Convertimos la info recogida en un DataFrame
    df = pd.DataFrame(all_data, columns=['Namespace', 'Pod', 'Container', 'Memory Usage Total', 'CPU Usage Total',
                                         'Memory Requests', 'Memory Limits', 'CPU Requests', 'CPU Limits'])
    df2 = df.drop_duplicates()

    print("En proceso: Creacion y carga de la hoja Excel")

    # Escribimos directamente a CSV y excel
    with pd.ExcelWriter('/tmp/metrics_data.xlsx') as writer:
        df2.to_excel(writer, sheet_name='Total Metricas Req y limits')
        quotas_df.to_excel(writer, sheet_name='Ns sin Quota')
        cores_df.to_excel(writer, sheet_name='Nº Cores Infrautilizadas')
        cores_ns_df.to_excel(writer, sheet_name='Nº Cores Infrautilizadas NS')
        memoria_df.to_excel(writer, sheet_name='Total Memoria Infrautilizada')
        memoria_ns_df.to_excel(writer, sheet_name='Total Memoria Infrautilizada NS')
        top10_df.to_excel(writer, sheet_name='TOP 10 Containers Sobredimensinados')

if __name__ == '__main__':
    main()