# autor : Luis Merino Troncoso
# Fecha : 05/06/2023
#
# Descripcion : Extraccion de metricas(mem, cpu, requests, limits de Openshift a traves del REST Api de prometheus utilizando
#               libreria requests y openpyxl para generar libo excel.
#               Genera una listado agregado combinando las 4 metricas  
# Ejecucion   : Hay que crear las variables de entorno despues de hacer el oc login al cluster
#               TOKEN: `oc whoami -t`
#               PROMETHEUS_URL: <route a prometheus-k8s>/api/v1/query/ 

import requests
import os
from openpyxl import Workbook

# cargamos la url de la ruta prometheus de la variable de entorno 
prometheus_url_ocp = os.environ['PROMETHEUS']

# cargamos la url de la ruta prometheus de la variable de entorno 
token = os.environ['TOKEN']

# prepapramos la cabecera con el TOKEN
headers = {
    "Authorization": "Bearer "+token
}    

# Creamos el workbook excel inicial 
workbook = Workbook()

# Creamos la worksheet 
memory_sheet = workbook.create_sheet('Consumo Memoria-Cpu')
memory_sheet.append(['Namespace', 'Pod', 'Container','Memory Usage','Cpu Usage','Memory Requests %', 'Memory Limits %'])

def prometheus_query(query):
    prometheus_url = prometheus_url_ocp
    params = {'query': query}
    response = requests.get(prometheus_url, params=params, headers=headers, verify=False))
    if response.status_code == 200:
        data = response.json()
        return data['data']['result']
    else:
        return None

def get_resource_usage(namespace):
    # Query for memory and CPU consumption
    memory_query = 'sum(container_memory_working_set_bytes) by (namespace, pod, container)'
    cpu_query = 'sum(rate(container_cpu_usage_seconds_total[5m])) by (namespace, pod, container)'

    # Query for percentage of requests and limits used
    requests_query = 'sum(container_cpu_request) by (namespace, pod, container) / sum(container_cpu_limit) by (namespace, pod, container) * 100'
    limits_query = 'sum(container_memory_limit_bytes) by (namespace, pod, container) / sum(container_memory_working_set_bytes) by (namespace, pod, container) * 100'

    # Combine all queries using 'or' operator
    query = f'({memory_query}) or ({cpu_query}) or ({requests_query}) or ({limits_query})'

    # Add namespace filter to the query
    query += f' and (namespace="{namespace}")'

    # Execute the Prometheus query
    results = prometheus_query(query)

    if results:
        for result in results:
            namespace = result['metric']['namespace']
            pod = result['metric']['pod']
            container = result['metric']['container']
            memory_usage = result['value'][1]
            cpu_usage = result['value'][1]
            requests_percentage = result['value'][1]
            limits_percentage = result['value'][1]

            print(f"Namespace: {namespace}, Pod: {pod}, Container: {container}")
            print(f"Memory Usage: {memory_usage}")
            print(f"CPU Usage: {cpu_usage}")
            print(f"Requests Percentage: {requests_percentage}")
            print(f"Limits Percentage: {limits_percentage}")
            print("")

# Specify the namespace you want to query
namespace = "your-namespace"

get_resource_usage(namespace)

# Cargamos los datos de consumo CPU en la worksheet
for result in cpu_results:
    namespace = result['metric']['namespace']
    pod = result['metric']['pod']
    container = result['metric']['container']
    cpu_requests = result['value'][1]
    cpu_limits = result['value'][1]
    cpu_sheet.append([namespace, pod, container, cpu_requests, cpu_limits])

# Grabamos la hoja excel 
workbook.save('/tmp/openshift_metrics.xlsx')
