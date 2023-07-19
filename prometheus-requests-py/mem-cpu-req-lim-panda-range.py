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
#                  prometheus_url: export PROMETHEUS_URL: <route a prometheus-k8s>/api/v1/query_range 
#               Hay que poner el intervalo de tiempo en fecha inicio y fin asi como el step ( en dd,hh, mm, ss) 

import requests
import os
import pandas as pd

# cargamos la url de la ruta prometheus de la variable de entorno 

prometheus_url = os.environ['PROMETHEUS_URL_RANGE']

# cargamos la url de la ruta prometheus de la variable de entorno 

token = os.environ['TOKEN']

# Funcion para hacer la llamada al API con los parametros 

def get_prometheus_data(query, start_time, end_time, step='1d'):
    params = {
        "query": query,
        "start": start_time,
        "end": end_time,
        "step": step           # intervalo de tiempo para la consulta (max30d)
    }
  
    headers = {
        "Authorization": "Bearer "+token
    }
    response = requests.get(prometheus_url, params=params, headers=headers, verify=False)
    data = response.json()
    return data["data"]["result"]

# Funcion para cargar las metricas que queremos ejecutar

def extract_metrics_by_day(start_time, end_time):
   # memory_total_query = 'sum(container_memory_usage_bytes) by (namespace, pod, container_name)'
    memory_total_query = 'sum(kube_pod_container_resource_requests_memory_bytes) by (namespace, pod, container)'
    cpu_total_query = 'sum(rate(container_cpu_usage_seconds_total[1m])) by (namespace, pod, container_name)'
    memory_requests_query = 'sum(kube_pod_container_resource_requests_memory_bytes) by (namespace, pod, container)'
    cpu_requests_query = 'sum(kube_pod_container_resource_requests_cpu_cores) by (namespace, pod, container)'
    memory_limits_query = 'sum(kube_pod_container_resource_limits_memory_bytes) by (namespace, pod, container)'
    cpu_limits_query = 'sum(kube_pod_container_resource_limits_cpu_cores) by (namespace, pod, container)'

    memory_total_data = get_prometheus_data(memory_total_query, start_time, end_time)
    cpu_total_data = get_prometheus_data(cpu_total_query, start_time, end_time)
    memory_requests_data = get_prometheus_data(memory_requests_query, start_time, end_time)
    cpu_requests_data = get_prometheus_data(cpu_requests_query, start_time, end_time)
    memory_limits_data = get_prometheus_data(memory_limits_query, start_time, end_time)
    cpu_limits_data = get_prometheus_data(cpu_limits_query, start_time, end_time)

    return memory_total_data, cpu_total_data, memory_requests_data, cpu_requests_data, memory_limits_data, cpu_limits_data

def create_excel_file(data_dict, file_path):
    with pd.ExcelWriter(file_path) as writer:
        for sheet_name, df in data_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

if __name__ == "__main__":
    start_time = '2023-07-18T08:00:00Z'
    end_time = '2023-07-19T08:00:00Z'

    memory_total_data, cpu_total_data, memory_requests_data, cpu_requests_data, memory_limits_data, cpu_limits_data = extract_metrics_by_day(start_time, end_time)

    memory_total_df = pd.DataFrame(memory_total_data)
    cpu_total_df = pd.DataFrame(cpu_total_data)
    memory_requests_df = pd.DataFrame(memory_requests_data)
    cpu_requests_df = pd.DataFrame(cpu_requests_data)
    memory_limits_df = pd.DataFrame(memory_limits_data)
    cpu_limits_df = pd.DataFrame(cpu_limits_data)

    data_dict = {
        'Memory Total': memory_total_df,
        'CPU Total': cpu_total_df,
        'Memory Requests': memory_requests_df,
        'CPU Requests': cpu_requests_df,
        'Memory Limits': memory_limits_df,
        'CPU Limits': cpu_limits_df,
    }

    file_path = 'pod_metrics.xlsx'
    create_excel_file(data_dict, file_path)