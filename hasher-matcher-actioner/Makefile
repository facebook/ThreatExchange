.PHONY: all docker upload_docker dev_create_configs dev_create_instance dev_test_instance dev_upload_test_signal dev_upload_test_content dev_upload_test_data dev_destroy_instance dev_clear_configs clean

shell-or-die = $\
	$(eval sod_out := $(shell $(1); echo $$?))$\
	$(if $(filter 0,$(lastword $(sod_out))),$\
		$(wordlist 1, $(shell echo $$(($(words $(sod_out)) - 1))), $(sod_out)),$\
		$(error $(1) exited with status $(lastword $(sod_out))))

USER ?= $(call shell-or-die,whoami)
REPOSITORY_NAME = hma-lambda-dev
DOCKER_TAG ?= ${USER} # todo - change to ${USER}-latest?
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

dev_upload_test_signal:
	@TF_BUCKET_NAME=$(call shell-or-die, set -o pipefail && cd terraform/ &&  terraform output -json bucket_name | tr -d '"') && \
	TF_PDQ_DATA_FILE_KEY=$(call shell-or-die, set -o pipefail && cd terraform/ &&  terraform output -json pdq_data_file_key | tr -d '"') && \
	echo "Upload sample signals? [y/N] This will copy over $${TF_PDQ_DATA_FILE_KEY} in $${TF_BUCKET_NAME}" && read ans && [ $${ans:-N} = y ] && \
	aws s3 cp sample_data/pdq.csv s3://$${TF_BUCKET_NAME}/$${TF_PDQ_DATA_FILE_KEY}

dev_upload_test_content:
	@TF_BUCKET_NAME=$(call shell-or-die, set -o pipefail && cd terraform/ &&  terraform output -json bucket_name | tr -d '"') && \
	TF_IMAGE_FOLDER_KEY=$(call shell-or-die, set -o pipefail && cd terraform/ &&  terraform output -json image_folder_key | tr -d '"') && \
	echo "Upload test photo? [y/N]  This will upload an images to $${TF_IMAGE_FOLDER_KEY} in s3 and will likely trigger the hasher (and matcher)" && read ans && [ $${ans:-N} = y ] && \
	aws s3 cp tests/data/b.jpg s3://$${TF_BUCKET_NAME}/$${TF_IMAGE_FOLDER_KEY}

dev_upload_test_data: dev_upload_test_signal dev_upload_test_content


dev_destroy_instance:
	cd terraform/ && terraform destroy -var "prefix=${USER}"

dev_clear_configs:
	-rm terraform/terraform.tfvars terraform/backend.tf
