locals {
  simulation_replica_count = var.env == "staging" ? 1 : 0
  influxdb_persistence     = var.env == "staging" ? "false" : "true"
}
