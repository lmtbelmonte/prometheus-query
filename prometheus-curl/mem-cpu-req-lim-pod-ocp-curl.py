# exportamos la variable PROMETHEUS_URL con la ruta que expone el OCP (en mi caso para pruebas)
export URL=https://prometheus-k8s-openshift-monitoring.apps.cluster-crh57.crh57.sandbox944.opentlc.com/

# extraemos las metricas y formatemaos en json con jq

curl -s -G -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' -H 'Content-Type: application/json' "$PROMETHEUS_URL/query"  --data-urlencode 'query=avg_over_time(container_memory_max_usage_bytes{image!="",container!=""}[1d])' --data-urlencode 'step=15m' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .values[]] | @csv' > memory.csv


curl -s -G -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' -H 'Content-Type: application/json' \
"$PROMETHEUS_URL/api/v1/query_range" \
--data-urlencode 'query=avg_over_time(container_memory_max_usage_bytes{image!="",container!=""})' \
--data-urlencode 'start=2023-06-26T07:00:00.000Z' \
--data-urlencode 'end=2023-06-26T09:00:00.000Z' \
--data-urlencode 'step=15m' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .values[]] | @csv' > memory.csv

curl -s -G "PROMETHEUS_URL/api/v1/query_range" \
  --data-urlencode 'query=avg_over_time(container_cpu_usage_seconds_total{image!="",container!=""}[30d])' \
  --data-urlencode 'step=1d' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .values[]] | @csv' > cpu.csv

curl -s -G "PROMETHEUS_URL/api/v1/query" \
  --data-urlencode 'query=kube_pod_container_resource_requests' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .value] | @csv' > requests.csv

curl -s -G "PROMETHEUS_URL/api/v1/query" \
  --data-urlencode 'query=kube_pod_container_resource_limits' | jq -r '.data.result[] | [.metric.pod, .metric.namespace, .metric.container, .value] | @csv' > limits.csv

# Utilizamos csvstack para combinar los datos en un solo csv
csvstack memory.csv cpu.csv requests.csv limits.csv | csvformat -T > metrics.csv

# Con csvformat convertimos a excel el CSV 
csvformat -T -U 1 metrics.csv > metrics-$(date +%d-%m-%Y).xlsx

