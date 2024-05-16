resource "helm_release" "power_hub_simulation" {
  name   = "power-hub-simulation"
  chart  = "./charts/python-app"
  values = [file("power_hub_simulation.values.yaml")]
  depends_on = [
    google_container_cluster.primary,
    helm_release.telegraf
  ]

  set {
    name  = "image.repository"
    value = "${local.power_hub_repo}/python-app"
  }

  set {
    name  = "container.envFromSecrets.MQTT_PASSWORD.secretName"
    value = kubernetes_secret.vernemq_auth.metadata.0.name
  }

  set {
    name  = "container.envFromSecrets.MQTT_PASSWORD.secretKey"
    value = "password"
  }

  set {
    name  = "container.env.MQTT_HOST"
    value = "${kubernetes_service.vernemq_internal.metadata.0.name}"
  }
}
