import requests
import pandas as pd

def get_thanos_metrics(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch Thanos metrics:", response.status_code)
        return None

def extract_pod_metrics(metrics):
    pod_metrics = []
    for metric in metrics:
        container = metric['metric']['container']
        namespace = metric['metric']['namespace']
        pod = metric['metric']['pod']
        month = metric['metric']['month']
        memory_usage = float(metric['values']['memory_usage'])
        cpu_usage = float(metric['values']['cpu_usage'])
        request_cpu = float(metric['values']['request_cpu'])
        request_memory = float(metric['values']['request_memory'])
        limit_cpu = float(metric['values']['limit_cpu'])
        limit_memory = float(metric['values']['limit_memory'])
        
        pod_metrics.append({
            'Container': container,
            'Namespace': namespace,
            'Pod': pod,
            'Month': month,
            'Memory Usage': memory_usage,
            'CPU Usage': cpu_usage,
            'Request CPU': request_cpu,
            'Request Memory': request_memory,
            'Limit CPU': limit_cpu,
            'Limit Memory': limit_memory
        })
    return pod_metrics

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print("Data saved to", filename)

if __name__ == '__main__':
    thanos_url = 'https://thanos-querier-openshift-monitoring.apps.cluster-crh57.crh57.sandbox944.opentlc.com/api'  # Replace with your Thanos metrics URL
    metrics = get_thanos_metrics(thanos_url)
    if metrics:
        pod_metrics = extract_pod_metrics(metrics)
        save_to_excel(pod_metrics, 'pod_metrics.xlsx')  # Replace with your desired filename
