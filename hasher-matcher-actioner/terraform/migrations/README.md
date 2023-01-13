# What are migrations

Migrations are commands to run when installing a new version of HMA. This includes both a fresh install or an upgrade of an older version. 

In both cases, there may be things that can't be done from within terraform, like creating some database entries, or running an hmalib.cli command, etc.

# How do I add a migration?

At the end of the `[migrations/main.tf](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/terraform/migrations/main.tf)` file, add a new resource like so:

```hcl
resource "null_resource" "some-name that identifies what this migration does" {
  provisioner "local-exec" {
    working_dir = "../../"
    command     = "<whatever command you want to run. eg.> python -m hmalib.scripts.cli.main migrate 2022_04_02_default_content_signal_type_configs --config-table ${var.config_table.name}"
  }
}
```

You have access to variable names defined in `[migrations/variables.tf](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/terraform/migrations/variables.tf)`

# Migrations are not working?

At present, their is an annoying bug. Any `python -m hmalib._foo_` command run during migration fails because terraform is not running the command from the appropriate directory. Editing the working_directory has not led to a solution. This is something we need to address. See [#1249](https://github.com/facebook/ThreatExchange/issues/1249)
