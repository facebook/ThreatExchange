.PHONY: all docker upload_docker dev_create_configs dev_create_instance dev_test_instance dev_destroy_instance dev_clear_configs clean

shell-or-die = $\
	$(eval sod_out := $(shell $(1); echo $$?))$\
	$(if $(filter 0,$(lastword $(sod_out))),$\
		$(wordlist 1, $(shell echo $$(($(words $(sod_out)) - 1))), $(sod_out)),$\
		$(error $(1) exited with status $(lastword $(sod_out))))

USER ?= $(call shell-or-die,whoami)
REPOSITORY_NAME = hma-lambda-dev
DOCKER_TAG ?= ${USER} # todo - change to ${USER}-latest?
DOCKER_URI = $(call shell-or-die,docker images --filter=reference='*/${REPOSITORY_NAME}:${DOCKER_TAG}' --format='{{.Repository}}')

LOCAL_TE_DIR = local_threatexchange # Should match LOCAL_THREAT_EXCHANGE ARG in Dockerfile

all:
	@echo >&2 "Must specify target. ${FAIL}"

docker:
	if [ ! -d ${LOCAL_TE_DIR} ] ; then mkdir ${LOCAL_TE_DIR} ; fi
	docker build -f Dockerfile -t ${REPOSITORY_NAME} .

docker_with_local_te:
	cp -r ../python-threatexchange ${LOCAL_TE_DIR}
	make docker
	rm -r ${LOCAL_TE_DIR}

upload_docker:
	@echo Using tag ${DOCKER_TAG}
	DOCKER_TAG=${DOCKER_TAG} ./scripts/update_lambda_docker_image.sh

use_local_te:
	cp -r ${LOCAL_TE_MOD} ./local_threatexchange
	python3 -m pip install -e local_threatexchange

terraform/terraform.tfvars:
	echo 'hma_lambda_docker_uri = "${DOCKER_URI}:${DOCKER_TAG}"' > terraform/terraform.tfvars

terraform/backend.tf:
	./scripts/write_backend_config.sh > terraform/backend.tf

dev_create_configs: terraform/terraform.tfvars terraform/backend.tf

dev_create_instance: dev_create_configs upload_docker
	cd terraform/ && terraform init -var "prefix=${USER}"
	cd terraform/ && terraform apply -var "prefix=${USER}"


# TODO There is probably a better way to do this
dev_test_instance:
	TF_DYNAMODB_TABLE=$(call shell-or-die, cd terraform/ && terraform output -json datastore_name) \
	TF_BUCKET_NAME=$(call shell-or-die, cd terraform/ &&  terraform output -json bucket_name) \
	TF_PREFIX=$(call shell-or-die, cd terraform/ &&  terraform output -json prefix) \
	./tests/scripts/check_deployed_instance.py

dev_destroy_instance:
	cd terraform/ && terraform destroy -var "prefix=${USER}"

dev_clear_configs:
	-rm terraform/terraform.tfvars terraform/backend.tf
