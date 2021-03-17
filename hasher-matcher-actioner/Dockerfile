# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

ARG DEPS_PATH=/hma-deps
ARG CODE_DIRECTORY=/hma-lambda

FROM public.ecr.aws/lambda/python:3.8 as build
RUN yum install -y gcc gcc-c++
COPY requirements.txt .
ARG DEPS_PATH
RUN pip install --no-cache-dir -r requirements.txt --target "${DEPS_PATH}"

FROM public.ecr.aws/lambda/python:3.8 as prod
ARG DEPS_PATH
COPY --from=build $DEPS_PATH $DEPS_PATH
ENV PYTHONPATH $DEPS_PATH
COPY hmalib ./hmalib
