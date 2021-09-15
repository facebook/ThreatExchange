# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

FROM public.ecr.aws/lambda/python:3.8@sha256:6fd9eea0292e900c7b8f4186c9e4fbcdb130118b8915ea8243394a7e620e5519 as build
RUN yum install -y gcc gcc-c++

# Install dependencies as a separate step so layers are reuseable.
COPY setup.py ./
RUN pip install -e .

# LAMBDA_TASK_ROOT is recommended in the image [1]. I'm hoping this will prevent
# the python path complications from arising.
# 1: https://hub.docker.com/r/amazon/aws-lambda-python
COPY hmalib ${LAMBDA_TASK_ROOT}/hmalib
