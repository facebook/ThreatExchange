#! /bin/bash
# Copyright (c) Meta Platforms, Inc. and affiliates.

# Add all the values from terraform/outputs.tf to the local env (call upcase with prefix HMA_)
# usage:
#    $ source scripts/set_tf_outputs_in_local_env.sh

[[ $_ != $0 ]] && echo "Error: this script needs to be 'source'd not run." && exit
for s in $(terraform -chdir=terraform output -json | jq -r "to_entries|map(\"HMA_\(.key|ascii_upcase)=\(.value.value|tostring)\")|.[]"); do
    export $s
done
