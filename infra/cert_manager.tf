resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  chart      = "cert-manager"
  repository = "https://charts.jetstack.io/"

  set {
    name  = "installCRDs"
    value = "\"true\""
  }

  create_namespace = true
}

locals {
  cluster_certificate_issuer  = "letsencrypt"
  cloudflare_api_token_secret = "cloudflare-api-token-secret"
}

resource "kubernetes_secret" "cloudflare_api_token" {
  metadata {
    name = local.cloudflare_api_token_secret
  }
  type = "Opaque"
  data = {
    "api-token" = var.cloudflare_api_token
  }
}

resource "kubernetes_manifest" "letsencrypt" {
  manifest = {
    "apiVersion" = "cert-manager.io/v1"
    "kind"       = "ClusterIssuer"
    "metadata" = {
      "name" = local.cluster_certificate_issuer
    }
    "spec" = {
      "acme" = {
        "email"  = "boudewijn.vangroos@foundationzero.org"
        "server" = "https://acme-v02.api.letsencrypt.org/directory"
        "privateKeySecretRef" = {
          "name" = "letsencrypt-key"
        }
        "solvers" = [
          {
            "dns01" : {
              "cloudflare" = {
                "apiTokenSecretRef" = {
                  "name" = local.cloudflare_api_token_secret
                  "key"  = "api-token"
                }
              }
            }
          }
        ]
      }
    }
  }
  depends_on = [helm_release.cert_manager, kubernetes_secret.cloudflare_api_token]
}
