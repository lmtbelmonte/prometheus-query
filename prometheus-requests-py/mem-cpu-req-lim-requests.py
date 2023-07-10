# autor : Luis Merino Troncoso
# Fecha : 29/06/2023
#
# Descripcion : Extraccion de metricas de Openshift a traves del REST Api de prometheus utilizando
#               utilizando libreria requests y pandas para el formato tabular de salida en excel          
# Ejecucion   : Hay que crear las variables de entorno despues de hacer el oc login al cluster
#               TOKEN: `oc whoami -t`
#               PROMETHEUS_URL: <route a prometheus metrics> 

import requests
import os
import pandas as pd

# cargamos la url de la ruta prometheus de la variable de entorno 
prometheus_url = os.environ['PROMETHEUS_URL']

# cargamos la url de la ruta prometheus de la variable de entorno 
token = os.environ['TOKEN']

# Preparamos la query Prometheus 
query = '''
sum(kube_pod_container_resource_requests_memory_bytes) by (namespace, pod)
#     kube_pod_container_resource_requests
#    sum(container_memory_usage_bytes{job="kubelet", image!="", container!="POD"})
#    sum(container_memory_usage_bytes{job="kubelet", image!=""})
#        by (container_name, namespace)
#    /
#    sum(kube_pod_container_resource_limits_memory_bytes)
#        by (container_name, namespace)
'''

# Recogemos parametros para llamada al api
params = {
    "query": query,
#    "time": "1d"
}

headers = {
    "Authorization": "Bearer "+token
}

# Hacemos llamada con un  GET request a Prometheus con la cabecera y token
response = requests.get(prometheus_url, params=params, headers=headers, verify=False)


# Parseamos la respuesta a JSON
data = response.json()

print(f"{query}")

# Extraemos los valores de la respuesta
values = data["data"]["result"]

# Utilizando Pandas, creamos a dataframe para guardar las metricas
metrics_df = pd.DataFrame(columns=["Container", "Namespace", "Memory Usage", "CPU Usage"])

# extraemos los valores de data iterando con values 
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

# Exportamos a execl el resultado 
metrics_df.to_excel("metrics.xlsx", index=False)

