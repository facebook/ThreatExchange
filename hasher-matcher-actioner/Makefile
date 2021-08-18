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
	echo 'hma_lambda_docker_uri = "${DOCKER_URI}:${DOCKER_TAG}"' > terraform/terraform.tfvars

terraform/backend.tf:
	@echo terraform state will be stored locally unless a backend.tf file is configured. 
	@echo Create a backend.tf? to use custom s3 bucket run: export TF_STATE_S3_BUCKET=bucket_name [y/N]
	@read ans; if [ $$ans = "y" ]; then ./scripts/write_backend_config.sh > terraform/backend.tf; fi

dev_create_configs: terraform/terraform.tfvars terraform/backend.tf

dev_create_instance: dev_create_configs upload_docker
	cd terraform/ && terraform init -var "prefix=${USER}"
	cd terraform/ && terraform apply -var "prefix=${USER}"

dev_destroy_instance:
	cd terraform/ && terraform destroy -var "prefix=${USER}"

dev_test_instance:
	python3 scripts/hma_client_lib.py

dev_clear_configs:
	-rm terraform/terraform.tfvars terraform/backend.tf
