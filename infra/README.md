# Terraform

## Bootstrap

Ensure you are logged in properly:
`gcloud auth application-default login`

For a new project, enable Cloud Key Management Service (KMS) API 

Run tofu in the bootstrap folder:

```
cd bootstrap
tofu apply -var-file="../terraform.tfvars"
```

## Create infra 

Create gke node pool (from `infra` directory):

`tofu apply --target=google_container_node_pool.primary_nodes`

We need to apply the cert manager before we can continue, because otherwise the planning of the ClusterIssuer will fail.

`tofu apply --target=helm_release.cert_manager`
`tofu apply --target=google_artifact_registry_repository.power_hub`

Add the latest docker image to the repo (from `energy-box-control` dir)

```
docker build \                                                                      
  --tag "europe-west1-docker.pkg.dev/{project_id}/power-hub/python-app:latest" --platform linux/amd64 \
  . -f python_script.Dockerfile
docker push europe-west1-docker.pkg.dev/{project_id}/power-hub/python-app:latest
```

`tofu apply`


# Troubleshooting
## On `tofu destroy`:
Error: Error waiting for Deleting Network: The network resource 'projects/code-zero-zem/global/networks/power-hub-staging-vpc' is already being used by 'projects/code-zero-zem/zones/europe-west1-b/networkEndpointGroups/k8s1-cd2fdbea-kube-system-default-http-backend-80-5e070d5e'

Manually delete the NEGs: https://stackoverflow.com/questions/75104116/how-to-make-network-endpoint-groups-disappear-automatically

## On:

```
│ Error: error loading state: Failed to open state file at gs://power-hub-bucket-tfstate/terraform/state/default.tfstate: googleapi: got HTTP response code 403 with body: <?xml version='1.0' encoding='UTF-8'?><Error><Code>UserProjectAccessDenied</Code><Message>Requester does not have serviceusage.services.use permissions on user project.</Message><Details><name@email.com> does not have serviceusage.services.use access to the Google Cloud project. Permission 'serviceusage.services.use' denied on resource (or it may not exist).</Details></Error>
```

`gcloud auth application-default login`
https://stackoverflow.com/a/68429291
