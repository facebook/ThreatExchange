# Copyright (c) Meta Platforms, Inc. and affiliates.

FROM public.ecr.aws/lambda/python:3.8@sha256:6fd9eea0292e900c7b8f4186c9e4fbcdb130118b8915ea8243394a7e620e5519 as build
RUN yum install -y gcc gcc-c++

# Install dependencies as a separate step so layers are reuseable.
# (the [y] is so the command does not fail if settings.py is not found.)
COPY setup.py settings.p[y] ./
RUN pip install -e .

# Copy local-threatexchange if it exists and install threatexchange from it in
# editable mode. This will override a copy of threatexchange fetched from pypi.
# Must copy .gitignore because COPY needs atleast one file to succeed.
COPY .gitignore local-threatexchang[e] ./
RUN if [ -d "local-threatexchange" ]; then pip install -e ./local-threatexchange; fi

# LAMBDA_TASK_ROOT is recommended in the image [1]. I'm hoping this will prevent
# the python path complications from arising.
# 1: https://hub.docker.com/r/amazon/aws-lambda-python
COPY hmalib ${LAMBDA_TASK_ROOT}/hmalib
COPY hmalib_extensions ${LAMBDA_TASK_ROOT}/hmalib_extensions
