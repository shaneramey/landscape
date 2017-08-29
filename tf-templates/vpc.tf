# Terraform Kubernetes cluster
# Single region
# Installs
#  - Network for GKE cluster
#  - Firewalls
#  - External IPs
#  - Forwarding Rules
#  - Routes
#  - VPN Gateway with 2 connections
#
# Uses Vault for secrets, keyed on this repo's branch name
#
# For use with https://github.com/shaneramey/landscaper/, first populate Vault:
# Step 1
# terraform GCE credentials json pulled from ServiceAccount in GCE IAM
# vault write /secret/terraform/myproject-12345/master/base \
#   credentials=@staging-b9af628162e8.json \
#   project=myproject-12345 \
#   region=us-west1 \
#
#
# Step 2
# run:
# terraform plan
#
# Step 3
# run:
# terraform apply
#

variable "gce_project_id" {
  description = "The GCE project name to apply these resources"
}

variable "gke_cluster1_name" {
  description = "The first GKE cluster's name"
}

# unused but planning to support once Terraform does
# see below and https://github.com/hashicorp/terraform/issues/12435
variable "gke_cluster1_version" {
  description = "The first GKE cluster's kubernetes version"
}

# example for below arguments
#terraform init  -backend-config 'bucket=something-something-1234' \
#                -backend-config 'path=tfstate-dev-123456/master.tfstate' \
#                -backend-config 'project=dev-123456'
terraform {
  backend "gcs" {
    bucket  = "specify-with--backend-config-bucket"
    path    = "specify-with--backend-config-path"
    project = "specify-with--backend-config-project"
  }
}

# Variable values stored in Vault
provider "vault" {
  # settings configured via environment variables:
  #  - VAULT_ADDR
  #  - VAULT_TOKEN
  #  - VAULT_CACERT
  #  - TERRAFORM_VAULT_MAX_TTL
}

# GCE secrets:
# - credentials
# - region
data "vault_generic_secret" "gce_project_secrets" {
  path = "secret/landscape/clouds/${var.gce_project_id}"
}

# An example of how to connect two GCE networks with a VPN
provider "google" {
  project      = "${var.gce_project_id}"
  region       = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
}

# Create the two networks we want to join. They must have separate, internal
# ranges.
resource "google_compute_network" "networkA" {
  name                    = "gke"
  auto_create_subnetworks = "false"
}

resource "google_compute_subnetwork" "gke_cluster1" {
  name       = "gke-master"
  ip_cidr_range = "${data.vault_generic_secret.gce_project_secrets.data["gke_network1_ipv4_cidr"]}"
  network = "${google_compute_network.networkA.self_link}"
  region  = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
}

# Attach a VPN gateway to each network.
resource "google_compute_vpn_gateway" "target_gateway1" {
  name    = "vpn1"
  network = "${google_compute_network.networkA.self_link}"
  region  = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
}

resource "google_compute_vpn_gateway" "target_gateway2" {
  name    = "vpn2"
  network = "${google_compute_network.networkA.self_link}"
  region  = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
}

# Create an outward facing static IP for each VPN that will be used by the
# other VPN to connect.
resource "google_compute_address" "vpn_static_ip1" {
  name   = "vpn-static-ip1"
  region = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
}

resource "google_compute_address" "vpn_static_ip2" {
  name   = "vpn-static-ip2"
  region = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
}

# Forward IPSec traffic coming into our static IP to our VPN gateway.
resource "google_compute_forwarding_rule" "fr1_esp" {
  name        = "fr1-esp"
  region      = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  ip_protocol = "ESP"
  ip_address  = "${google_compute_address.vpn_static_ip1.address}"
  target      = "${google_compute_vpn_gateway.target_gateway1.self_link}"
}

resource "google_compute_forwarding_rule" "fr2_esp" {
  name        = "fr2-esp"
  region      = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  ip_protocol = "ESP"
  ip_address  = "${google_compute_address.vpn_static_ip2.address}"
  target      = "${google_compute_vpn_gateway.target_gateway2.self_link}"
}

# The following two sets of forwarding rules are used as a part of the IPSec
# protocol
resource "google_compute_forwarding_rule" "fr1_udp500" {
  name        = "fr1-udp500"
  region      = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  ip_protocol = "UDP"
  port_range  = "500"
  ip_address  = "${google_compute_address.vpn_static_ip1.address}"
  target      = "${google_compute_vpn_gateway.target_gateway1.self_link}"
}

resource "google_compute_forwarding_rule" "fr2_udp500" {
  name        = "fr2-udp500"
  region      = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  ip_protocol = "UDP"
  port_range  = "500"
  ip_address  = "${google_compute_address.vpn_static_ip2.address}"
  target      = "${google_compute_vpn_gateway.target_gateway2.self_link}"
}

resource "google_compute_forwarding_rule" "fr1_udp4500" {
  name        = "fr1-udp4500"
  region      = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  ip_protocol = "UDP"
  port_range  = "4500"
  ip_address  = "${google_compute_address.vpn_static_ip1.address}"
  target      = "${google_compute_vpn_gateway.target_gateway1.self_link}"
}

resource "google_compute_forwarding_rule" "fr2_udp4500" {
  name        = "fr2-udp4500"
  region      = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  ip_protocol = "UDP"
  port_range  = "4500"
  ip_address  = "${google_compute_address.vpn_static_ip2.address}"
  target      = "${google_compute_vpn_gateway.target_gateway2.self_link}"
}

# Each tunnel is responsible for encrypting and decrypting traffic exiting
# and leaving its associated gateway
resource "google_compute_vpn_tunnel" "tunnel1" {
  name               = "tunnel1"
  region             = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  peer_ip            = "${data.vault_generic_secret.gce_project_secrets.data["gce_vpn1_ipsec_remote_ip"]}"
  shared_secret      = "${data.vault_generic_secret.gce_project_secrets.data["gce_vpn1_ipsec_secret_key"]}"
  target_vpn_gateway = "${google_compute_vpn_gateway.target_gateway1.self_link}"
  local_traffic_selector  = ["${google_compute_subnetwork.gke_cluster1.ip_cidr_range}", "${google_container_cluster.cluster1.cluster_ipv4_cidr}"]
  remote_traffic_selector = ["${data.vault_generic_secret.gce_project_secrets.data["gce_vpn1_ipsec_tunneled_net1"]}"]
  ike_version        = "1"

  depends_on = ["google_compute_forwarding_rule.fr1_udp500",
    "google_compute_forwarding_rule.fr1_udp4500",
    "google_compute_forwarding_rule.fr1_esp",
  ]
}

resource "google_compute_vpn_tunnel" "tunnel2" {
  name               = "tunnel2"
  region             = "${data.vault_generic_secret.gce_project_secrets.data["region"]}"
  peer_ip            = "${data.vault_generic_secret.gce_project_secrets.data["gce_vpn2_ipsec_remote_ip"]}"
  shared_secret      = "${data.vault_generic_secret.gce_project_secrets.data["gce_vpn2_ipsec_secret_key"]}"
  target_vpn_gateway = "${google_compute_vpn_gateway.target_gateway2.self_link}"
  local_traffic_selector  = ["${google_compute_subnetwork.gke_cluster1.ip_cidr_range}", "${google_container_cluster.cluster1.cluster_ipv4_cidr}"]
  remote_traffic_selector = ["${data.vault_generic_secret.gce_project_secrets.data["gce_vpn2_ipsec_tunneled_net1"]}"]
  ike_version        = "1"

  depends_on = ["google_compute_forwarding_rule.fr2_udp500",
    "google_compute_forwarding_rule.fr2_udp4500",
    "google_compute_forwarding_rule.fr2_esp",
  ]
}

# Each route tells the associated network to send all traffic in the dest_range
# through the VPN tunnel
resource "google_compute_route" "route1" {
  name                = "route1"
  network             = "${google_compute_network.networkA.name}"
  next_hop_vpn_tunnel = "${google_compute_vpn_tunnel.tunnel1.self_link}"
  dest_range          = "${data.vault_generic_secret.gce_project_secrets.data["gce_vpn1_ipsec_tunneled_net1"]}"
  priority            = 1000
}

resource "google_compute_route" "route2" {
  name                = "route2"
  network             = "${google_compute_network.networkA.name}"
  next_hop_vpn_tunnel = "${google_compute_vpn_tunnel.tunnel2.self_link}"
  dest_range          = "${data.vault_generic_secret.gce_project_secrets.data["gce_vpn2_ipsec_tunneled_net1"]}"
  priority            = 1000
}

resource "google_container_cluster" "cluster1" {
  name               = "${var.gke_cluster1_name}"
  network            = "${google_compute_network.networkA.name}"
  subnetwork         = "${google_compute_subnetwork.gke_cluster1.name}"
  cluster_ipv4_cidr  = "${data.vault_generic_secret.gce_project_secrets.data["gke_cluster1_pod_ipv4_cidr"]}"
  zone               = "${data.vault_generic_secret.gce_project_secrets.data["region"]}-a"
  additional_zones = [
    "${data.vault_generic_secret.gce_project_secrets.data["region"]}-b",
    "${data.vault_generic_secret.gce_project_secrets.data["region"]}-c",
  ]
  initial_node_count = 1
# node_version doesn't work on initial clujster creation
# more info: https://github.com/hashicorp/terraform/issues/12435
# node_version       = "${var.gke_cluster1_version}"

  master_auth {
    username = "${data.vault_generic_secret.gce_project_secrets.data["gke_cluster1_master_auth_username"]}"
    password = "${data.vault_generic_secret.gce_project_secrets.data["gke_cluster1_master_auth_password"]}"
  }

  node_config {
    oauth_scopes = [
      "https://www.googleapis.com/auth/compute",
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }
}
