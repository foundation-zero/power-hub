variable "vernemq_power_hub_password" {
  description = "password for the power hub user in vernemq"
}

locals {
  vernemq_record_name      = "vernemq.${var.env}.${var.subdomain}"
  vernemq_certificate_name = "vernemq-certicate-secret"
  vernemq_certificate_path = "/etc/ssl/vernemq"
  vernemq_host             = "vernemq.${var.env}.${var.subdomain}.${var.root_hostname}"
  vernemq_auth_secret_name = "vernemq-auth"
}

resource "kubernetes_manifest" "vernemq_ssl" {
  manifest = {
    "apiVersion" = "cert-manager.io/v1"
    "kind"       = "Certificate"
    "metadata" = {
      "name"      = "vernemq-certificate"
      "namespace" = "default"
    }
    "spec" = {
      "secretName" = local.vernemq_certificate_name
      "issuerRef" = {
        "kind" = "ClusterIssuer"
        "name" = local.cluster_certificate_issuer
      }
      "commonName" = local.vernemq_host
      "dnsNames"   = [local.vernemq_host]
    }
  }
  depends_on = [kubernetes_manifest.letsencrypt]
}

resource "google_compute_address" "vernemq_ip" {
  name = "${var.name}-${var.env}-vernemq-address"
}



resource "kubernetes_secret" "vernemq_auth" {
  metadata {
    name = local.vernemq_auth_secret_name
  }

  data = {
    password = var.vernemq_power_hub_password
  }
}



resource "helm_release" "vernemq" {
  name       = "vernemq"
  chart      = "vernemq"
  repository = "https://vernemq.github.io/docker-vernemq/"


  depends_on = [
    google_container_cluster.primary,
    kubernetes_manifest.vernemq_ssl
  ]

  values = [file("vernemq.values.yaml")]

  set {
    name  = "service.loadBalancerIP"
    value = google_compute_address.vernemq_ip.address
  }

  set {
    name  = "secretMounts[0].name"
    value = "vernemq-certificate"
  }
  set {
    name  = "secretMounts[0].secretName"
    value = local.vernemq_certificate_name
  }
  set {
    name  = "secretMounts[0].path"
    value = local.vernemq_certificate_path
  }

  set {
    name  = "additionalEnv[0].name"
    value = "DOCKER_VERNEMQ_LISTENER__SSL__CAFILE"
  }
  set {
    name  = "additionalEnv[0].value"
    value = "${local.vernemq_certificate_path}/tls.crt"
  }
  set {
    name  = "additionalEnv[1].name"
    value = "DOCKER_VERNEMQ_LISTENER__SSL__CERTFILE"
  }
  set {
    name  = "additionalEnv[1].value"
    value = "${local.vernemq_certificate_path}/tls.crt"
  }
  set {
    name  = "additionalEnv[2].name"
    value = "DOCKER_VERNEMQ_LISTENER__SSL__KEYFILE"
  }
  set {
    name  = "additionalEnv[2].value"
    value = "${local.vernemq_certificate_path}/tls.key"
  }

  set {
    name  = "additionalEnv[3].name"
    value = "DOCKER_VERNEMQ_LISTENER__WSS__CAFILE"
  }
  set {
    name  = "additionalEnv[3].value"
    value = "${local.vernemq_certificate_path}/tls.crt"
  }
  set {
    name  = "additionalEnv[4].name"
    value = "DOCKER_VERNEMQ_LISTENER__WSS__CERTFILE"
  }
  set {
    name  = "additionalEnv[4].value"
    value = "${local.vernemq_certificate_path}/tls.crt"
  }
  set {
    name  = "additionalEnv[5].name"
    value = "DOCKER_VERNEMQ_LISTENER__WSS__KEYFILE"
  }
  set {
    name  = "additionalEnv[5].value"
    value = "${local.vernemq_certificate_path}/tls.key"
  }
  set {
    name  = "additionalEnv[6].name"
    value = "DOCKER_VERNEMQ_ALLOW_ANONYMOUS"
  }
  set {
    name  = "additionalEnv[6].value"
    value = "on"
    type  = "string"
  }
  set {
    name  = "additionalEnv[7].name"
    value = "DOCKER_VERNEMQ_ACCEPT_EULA"
  }
  set {
    name  = "additionalEnv[7].value"
    value = "yes"
    type  = "string"
  }
  set {
    name  = "additionalEnv[8].name"
    value = "DOCKER_VERNEMQ_USER_power-hub"
  }
  set {
    name  = "additionalEnv[8].valueFrom.secretKeyRef.name"
    value = kubernetes_secret.vernemq_auth.metadata.0.name
    type  = "string"
  }
  set {
    name  = "additionalEnv[8].valueFrom.secretKeyRef.key"
    value = "password"
  }

  set {
    name  = "persistentVolume.enabled"
    value = var.env == "staging" ? "false" : "true"
  }

  set {
    name  = "additionalEnv[9].name"
    value = "DOCKER_VERNEMQ_PLUGINS__VMQ_BRIDGE"
  }

  set {
    name  = "additionalEnv[9].value"
    value = "on"
    type  = "string"
  }

  set {
    name  = "additionalEnv[10].name"
    value = "DOCKER_VERNEMQ_LISTENER__SSL__ALLOWED_PROTOCOL_VERSIONS"
  }

  set {
    name  = "additionalEnv[10].value"
    value = "3,4,5,131,132"
    type  = "string"
  }
}

resource "kubernetes_service" "vernemq_internal" {
  metadata {
    name = "vernemq-internal"
  }
  spec {
    session_affinity = "ClientIP"
    selector = {
      "app.kubernetes.io/name"     = "vernemq"
      "app.kubernetes.io/instance" = "vernemq"
    }
    port {
      protocol    = "TCP"
      port        = 1883
      target_port = 1883
    }
  }

  depends_on = [helm_release.vernemq]
}

resource "cloudflare_record" "vernemq_record" {
  zone_id = data.cloudflare_zone.zone.id
  name    = local.vernemq_record_name
  value   = google_compute_address.vernemq_ip.address
  type    = "A"
  comment = "managed by power hub terraform"
}
