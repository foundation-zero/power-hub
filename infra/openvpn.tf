variable "openvpn_admin_password" {
  description = "openvpn admin password"
}

variable "openvpn_power_hub_password" {
  description = "openvpn power hub password"
}

variable "openvpn_developer_password" {
  description = "openvpn developer password"
}


resource "helm_release" "openvpn" {
  name       = "openvpn"
  chart      = "openvpn-as"
  repository = "https://stenic.github.io/helm-charts"

  values = [file("openvpn.values.yaml")]

  set {
    name  = "openvpn.admin.password"
    value = var.openvpn_admin_password
  }

  set {
    name = "openvpn.users"
    value = json_encode([{
      "user" : "power_hub",
      "password" : var.openvpn_power_hub_password
      },
      {
        "user" : "developer",
        "password" : var.openvpn_developer_password
    }])
  }
}
