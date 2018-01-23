resource "helm_release" "auto_approve_csrs" {
  name      = "auto_approve_csrs"
  chart     = "chartmuseum/auto-approve-csrs:0.1.9"

  set {
    name  = "clusterDomain"
    value = "cluster.local"
  }
}
