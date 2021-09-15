#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os


def get_endpoints(app):
    for route in app.routes:
        if "mountpoint" in route.config:
            prefix = route.config["mountpoint.prefix"]
            subpath = route.config["mountpoint.target"]

            for prefixes, route in get_endpoints(subpath):
                yield [prefix] + prefixes, route
        else:
            yield [], route


def print_endpoints(app, with_doc=True):
    for prefixes, route in get_endpoints(app):
        path = (
            "/" + "/".join(p.strip("/") for p in prefixes if p.strip("/"))
            if prefixes
            else ""
        )
        print(route.method, f"{path}{route.rule}", route.callback.__qualname__)
        if with_doc:
            print(route.callback.__doc__)


if __name__ == "__main__":

    # Provide dummy values to expected environ to avoid key errors when importing the app
    os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"] = ""
    os.environ["THREAT_EXCHANGE_DATA_FOLDER"] = ""
    os.environ["THREAT_EXCHANGE_PDQ_FILE_EXTENSION"] = ""
    os.environ["HMA_CONFIG_TABLE"] = ""
    os.environ["DYNAMODB_TABLE"] = ""
    os.environ["IMAGE_BUCKET_NAME"] = ""
    os.environ["IMAGE_PREFIX"] = ""
    os.environ["SUBMISSIONS_QUEUE_URL"] = ""
    os.environ["HASHES_QUEUE_URL"] = ""
    os.environ["INDEXES_BUCKET_NAME"] = ""
    os.environ["WRITEBACKS_QUEUE_URL"] = ""
    os.environ["BANKS_TABLE"] = ""

    from hmalib.lambdas.api.api_root import app

    print_endpoints(app)
