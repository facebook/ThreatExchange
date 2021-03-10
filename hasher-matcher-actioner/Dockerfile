# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

ARG DEPS_PATH=/hma-deps
ARG CODE_DIRECTORY=/hma-lambda
ARG LOCAL_THREAT_EXCHANGE=./local_threatexchange

FROM public.ecr.aws/lambda/python:3.8 as build
ARG DEPS_PATH
RUN yum install -y gcc gcc-c++

# If there is a local version of the threat exchange module install it before other requirements
ARG LOCAL_THREAT_EXCHANGE
COPY $LOCAL_THREAT_EXCHANGE $LOCAL_THREAT_EXCHANGE
RUN if [[ -f $LOCAL_THREAT_EXCHANGE/setup.py ]] ;\
    then\
        python3 -m pip install $LOCAL_THREAT_EXCHANGE --target "${DEPS_PATH}" ;\
    else\
        echo using public threatexchange module ;\
fi

COPY requirements.txt .
ARG DEPS_PATH
RUN pip install --no-cache-dir -r requirements.txt --target "${DEPS_PATH}"

FROM public.ecr.aws/lambda/python:3.8 as prod
ARG DEPS_PATH
COPY --from=build $DEPS_PATH $DEPS_PATH
ENV PYTHONPATH $DEPS_PATH
COPY hmalib ./hmalib

RUN python3 ./hmalib/lambdas/fetcher.py
