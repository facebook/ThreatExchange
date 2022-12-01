# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# Chronologically add migration items that are necessary for a new version to
# operate. terraform is already doing the state-management of the HMA versions.
# It will suffice as way to record migrations between versions.

# AFTER v0.1.2 https://github.com/facebook/ThreatExchange/releases/tag/HMA-v0.1.2
resource "null_resource" "default_signal_content_type_configs" {
  provisioner "local-exec" {
    working_dir = "../../"
    command     = "python -m hmalib.scripts.cli.main migrate 2022_04_02_default_content_signal_type_configs --config-table ${var.config_table.name}"
  }
}

resource "null_resource" "default_signal_exchange_apis" {
  provisioner "local-exec" {
    working_dir = "../../"
    command     = "python -m hmalib.scripts.cli.main migrate 2022_07_24_default_signal_exchange_apis --config-table ${var.config_table.name}"
  }
}
