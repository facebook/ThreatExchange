#! /bin/bash
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# Add all the values from terraform/outputs.tf to the local env (call upcase with prefix HMA_)
# usage:
#    $ source scripts/set_tf_outputs_in_local_env.sh 

echo "Reminder: only works if you 'source' the file"
for s in $(terraform -chdir=terraform output -json | jq -r "to_entries|map(\"HMA_\(.key|ascii_upcase)=\(.value.value|tostring)\")|.[]"); do
    export $s
done 
