variable "pagerduty_gke_key" {
  description = "GKE PagerDuty integration key"
}

resource "google_monitoring_notification_channel" "pagerduty_power_hub_gke" {
  display_name = "PagerDuty Power Hub GKE ${var.env}"
  user_labels  = { created_by = "tofu" }
  type         = "pagerduty"

  labels = {
    "service_key" = var.pagerduty_gke_key
  }
}

resource "google_monitoring_alert_policy" "cloud_logs_error" {
  display_name = "Cloud ${var.env} errors"
  user_labels  = { created_by = "tofu" }
  combiner     = "OR"
  severity     = "ERROR"
  project      = var.project_id
  depends_on = [
    google_monitoring_notification_channel.pagerduty_power_hub_gke
  ]

  conditions {
    display_name = "Error condition"
    condition_matched_log {
      filter = "severity=ERROR\n-resource.labels.container_name=\"gke-metrics-agent\"\nNOT textPayload:[INFO]"
      label_extractors = {
        "Message" = "EXTRACT(textPayload)"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.pagerduty_power_hub_gke.id]

  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }
    auto_close = "21600s"
  }
}
