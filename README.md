# Extracción de datos de metricas de Prometheus en Openshift 412 con python3

De la carpeta prometheus-requests-py ejecutamos capacity-lmt-xlsx.py

El python atacando al aAPI prometheus de una cluster de Openshift 4.12 extrae en una excel

- memory_usage_total 
- cpu_usage_total 
- memory_requests 
- cpu_requests
- memory_limits
- cpu_limits
- Memory y CPU infrautilizada

Ejecucion: Hay que crear las variables de entorno despues de hacer el oc login al cluster
           TOKEN: `oc whoami -t`
           prometheus_url: export PROMETHEUS_URL: <route a prometheus-k8s>/api/v1/query/ 
         ( se pueden mejorar varias cosas entre ellas , poner el intervalo de tiempo en fecha inicio y fin asi como el step ( en dd,hh, mm, ss) )

