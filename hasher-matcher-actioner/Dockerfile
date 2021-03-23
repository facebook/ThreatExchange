# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

FROM public.ecr.aws/lambda/python:3.8 as build
RUN yum install -y gcc gcc-c++
COPY setup.py ./setup.py
COPY hmalib ./hmalib
RUN pip install --no-cache-dir .