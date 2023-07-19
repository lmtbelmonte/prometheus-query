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
#               de Openshift a traves del REST Api y generar un libro excel          
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

def get_metrics(query, start_time, end_time):
    params = {
        "query": query,
        "start": start_time,
        "end": end_time,
        "step": "1d"           # intervalo de tiempo para la consulta (max30d)
    }
   
    headers = {
        "Authorization": "Bearer "+token
    }
    response = requests.get(prometheus_url, params=params, headers=headers, verify=False)
    data = response.json()
    return data["data"]["result"]

# Funcion para cargar las metricas que queremos ejecutar

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
            labels = result['metric']
            namespace = labels['namespace']
#           namespace = result['metric']['namespace']
            pod = labels['pod']
            value = result['value'][1]
            if namespace not in metrics_data:
                metrics_data[namespace] = {}
            metrics_data[namespace][pod] = metrics_data[namespace].get(pod, {})
            metrics_data[namespace][pod][metric_name] = value
            print(f"{metrics_data[namespace][pod][metric_name]}") 
    return metrics_data

# Funcion formatear los datos con pandas y grabar una excel 
def save_to_excel(metrics_data, filename):
    df = pd.DataFrame.from_dict({(i, j): metrics_data[i][j]
                                 for i in metrics_data.keys()
                                 for j in metrics_data[i].keys()}, orient='index')
    df.index = pd.MultiIndex.from_tuples(df.index, names=['Namespace', 'Pod'])
    df.reset_index(inplace=True)
    df.to_excel(filename, index=False)

if __name__ == "__main__":
    start_time = "2023-07-18T08:00:00Z"
    end_time = "2023-07-19T08:00:00Z"
    filename = "metrics-pandas.xlsx"

    metrics_data = extract_metrics(start_time, end_time)
    save_to_excel(metrics_data, filename)