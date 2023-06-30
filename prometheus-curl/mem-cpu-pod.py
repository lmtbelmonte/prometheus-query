from kubernetes import client, config

def get_resource_consumption(api_client, namespace):
    v1_api = client.CoreV1Api(api_client)
    pod_list = v1_api.list_namespaced_pod(namespace)

    for pod in pod_list.items:
        pod_name = pod.metadata.name
        containers = pod.spec.containers
        for container in containers:
            container_name = container.name
            container_resource = container.resources
            if container_resource and container_resource.requests:
                cpu_request = container_resource.requests.get('cpu', None)
                memory_request = container_resource.requests.get('memory', None)
                if cpu_request:
                    print(f"Namespace: {namespace}, Pod: {pod_name}, Container: {container_name}")
                    print(f"CPU Request: {cpu_request}")
                if memory_request:
                    print(f"Namespace: {namespace}, Pod: {pod_name}, Container: {container_name}")
                    print(f"Memory Request: {memory_request}")

def main():
    # Load the cluster configuration from the kubeconfig file
    config.load_kube_config()

    # Create an API client
    api_client = client.ApiClient()

    # Get all namespaces in the cluster
    v1_api = client.CoreV1Api(api_client)
    namespaces = v1_api.list_namespace().items

    # Iterate over each namespace and extract resource consumption
    for namespace in namespaces:
        namespace_name = namespace.metadata.name
        get_resource_consumption(api_client, namespace_name)

if __name__ == '__main__':
    main()

