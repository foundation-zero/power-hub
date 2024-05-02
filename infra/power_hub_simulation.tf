resource "kubernetes_secret" "artifact_registry" {
  metadata {
    name = "artifact-registry"
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "europe-west1-docker.pkg.dev" = {
          "username" = "_json_key"
          "password" = file("/Users/sietsehuisman/Documents/Work/Zero/energy-box-control/infra/gkey.json")
          "email"    = "power-hub@code-zero-zem.iam.gserviceaccount.com"
        }
      }
    })
  }
}

resource "helm_release" "power_hub_simulation" {
  name       = "power-hub-simulation"
  chart      = "./charts/python-app"
  values = [file("power_hub_simulation.values.yaml")]
  depends_on = [ 
    google_container_cluster.primary,
    kubernetes_secret.artifact_registry, 
    helm_release.telegraf
    ]

  # TODO create secret out of this?
  set {
    name  = "container.env.MQTT_PASSWORD"
    value = var.vernemq_power_hub_password
  }
}
