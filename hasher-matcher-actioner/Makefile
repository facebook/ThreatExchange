.PHONY: all docker upload_docker dev_create_configs dev_create_instance dev_test_instance dev_destroy_instance dev_clear_configs clean

shell-or-die = $\
	$(eval sod_out := $(shell $(1); echo $$?))$\
	$(if $(filter 0,$(lastword $(sod_out))),$\
		$(wordlist 1, $(shell echo $$(($(words $(sod_out)) - 1))), $(sod_out)),$\
		$(error $(1) exited with status $(lastword $(sod_out))))

USER ?= $(call shell-or-die,whoami)
REPOSITORY_NAME = hma-lambda-dev
DOCKER_TAG ?= ${USER}# todo - change to ${USER}-latest?
DOCKER_URI = $(call shell-or-die,docker images --filter=reference='*/${REPOSITORY_NAME}:${DOCKER_TAG}' --format='{{.Repository}}')

all:
	@echo >&2 "Must specify target. ${FAIL}"

docker:
	docker build -f Dockerfile -t ${REPOSITORY_NAME} .

upload_docker:
	@echo Using tag ${DOCKER_TAG}
	DOCKER_TAG=${DOCKER_TAG} ./scripts/update_lambda_docker_image.sh

terraform/terraform.tfvars:
	@echo ACTION REQUIRED: terraform/terraform.tfvars is needed to deploy and cannot be created automatically. 
	@echo However as a staring point, you can copy the example:
	@echo cp terraform/terraform.tfvars.example terraform/terraform.tfvars
	@echo Here are the likely initial values for the first two vars:
	@echo 'hma_lambda_docker_uri = "${DOCKER_URI}:${DOCKER_TAG}"'
	@echo 'prefix = "${USER}"'
	exit 1

terraform/backend.tf:
	@echo terraform state will be stored locally unless a backend.tf file is configured. 
	@echo Create a backend.tf? to use custom s3 bucket run this first: export TF_STATE_S3_BUCKET=bucket_name [y/N]
	@read ans; if [ $$ans = "y" ]; then ./scripts/write_backend_config.sh > terraform/backend.tf; fi

dev_create_configs: terraform/terraform.tfvars terraform/backend.tf

dev_create_instance: dev_create_configs upload_docker
	terraform -chdir=terraform init 
	terraform -chdir=terraform apply

dev_destroy_instance:
	terraform -chdir=terraform destroy 

dev_test_instance:
	python3 hmalib/scripts/common/client_lib.py

dev_apply_with_newest_docker_image:
	@DIGEST=$(call shell-or-die, aws ecr describe-images --repository-name hma-lambda-dev --image-ids imageTag=${DOCKER_TAG} | jq -r '.imageDetails[0].imageDigest'); \
	terraform -chdir=terraform apply -var "hma_lambda_docker_uri=${DOCKER_URI}@$${DIGEST}"

dev_install_hmacli:
	python3 -m pip install -e '.[all]'
