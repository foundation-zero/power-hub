variable "python_app_image_tag" {
  default = "latest"
}

variable "pagerduty_mqtt_checker_key" {
  description = "PagerDuty key"
}

resource "helm_release" "power_hub_mqtt_checker" {
  name   = "power-hub-mqtt_checker"
  chart  = "./charts/python-app"
  values = [file("power_hub_mqtt_checker.values.yaml")]
  depends_on = [
    google_container_cluster.primary,
    helm_release.telegraf
  ]

  set {
    name  = "image.repository"
    value = "${local.power_hub_repo}/python-app"
  }

  set {
    name = "image.tag"
    value = var.python_app_image_tag
  }

  set {
    name = "container.env.PAGERDUTY_MQTT_CHECKER_KEY"
    value = var.pagerduty_mqtt_checker_key
  } 

  set {
    name = "container.env.SEND_NOTIFICATIONS"
    value = var.send_notifications
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
    value = kubernetes_service.vernemq_internal.metadata.0.name
  }
}
