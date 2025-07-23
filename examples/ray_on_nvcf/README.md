## Deploying a RayCluster on NVCF
This document describes the process of deploying a `RayCluster` on NVCF using a helm chart. The helm chart starts the Ray `head node` and multiple `worker node` replicas. In addition, it deploys `Redis` for fault tolerance.

For deployment, follow the steps described below.

### Push the helm chart to your NGC Private Registry.

```bash
ngc registry chart push <ngc-org-id>/ray-cluster:0.1.0
```

More details about this can be found [here](https://docs.nvidia.com/ngc/gpu-cloud/ngc-private-registry-user-guide/index.html#managing-helm-charts-using-ngc-cli).


### Creating a Helm-based function

```bash
ngc cf function create --name ray-test-func --helm-chart <ngc-org-id>/ray-cluster:0.1.0 --helm-chart-service ray-head-svc --health-protocol HTTP --health-uri / --inference-url / --inference-port 8265 --health-port 8265 --health-expected-status-code 200 --health-timeout PT10S
```

`8265` is the port for the dashboard and can also be used for submitting RayJobs via the SDK.

### Deploy the created function.
For deploying use the NVCF Rest API.

Identify the `FUNCTION_ID` and `FUNCTION_VERSION_ID` for the deployed function. These are returned after the function creation.

```bash
export FUNCTION_ID=<id>
export FUNCTION_VERSION_ID=<version-id>
export API_KEY=<API-KEY>
```

In the following, replace `instanceType`, `gpu`, and `clusters` with your configured backend values.

```bash
curl --location "https://api.ngc.nvidia.com/v2/nvcf/deployments/functions/$FUNCTION_ID/versions/$FUNCTION_VERSION_ID" \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--header "Authorization: Bearer $API_KEY" \
--data '{
    "deploymentSpecifications": [
        {
            "instanceType": "GPU.L40_4x",
            "gpu": "L40",
            "minInstances": 1,
            "maxInstances": 1,
            "maxRequestConcurrency": 1,
            "regions": ["us-east-1"],
            "clusters": ["dgxc"],
            "configuration": {
                "worker": {
                    "replicas": 3
                }
            }
        }
    ]
}'
```

### Accessing the Dashboard

After the deployment is active, you should be able to access the `Ray` dashboard using the url: `https://<function-id>.invocation.api.nvcf.nvidia.com`. You can use the `Requestly` Chrome extension to intercept and add `Bearer` token to the request.

## Submitting a RayJob

The [example](./example/) folder contains a simple matrix multiplication job that can be submitted to the deployed `RayCluster`.

```bash
cd example
sudo docker build -f Dockerfile -t test:v1 .
sudo docker run test:v1
```

Following this, you should see something like:

```bash
2025-07-23 15:13:10,795 INFO dashboard_sdk.py:338 -- Uploading package gcs://_ray_pkg_f05cf1179ea93cc4.zip.
2025-07-23 15:13:10,796 INFO packaging.py:518 -- Creating a file package for local directory './'.
raysubmit_sE3n7Q8QYJxrmYLK
status: PENDING
status: PENDING
status: RUNNING
status: RUNNING
status: RUNNING
2025-07-23 08:13:17,379 INFO worker.py:1313 -- Using address 10.244.53.35:6380 set in the environment variable RAY_ADDRESS
2025-07-23 08:13:17,379 INFO worker.py:1431 -- Connecting to existing Ray cluster at address: 10.244.53.35:6380...
2025-07-23 08:13:17,419 INFO worker.py:1612 -- Connected to Ray cluster. View the dashboard at http://10.244.53.35:8265
2025-07-23 08:13:17,445 - INFO - Creating two 2048x2048 matrices on the CPU.
2025-07-23 08:13:17,506 - INFO - Placing large matrices into the Ray object store.
2025-07-23 08:13:17,581 - INFO - Submitting the PyTorch matrix multiplication task to Ray.
```

The jobs can also be tracked via the dashboard.
