# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
from datetime import datetime

def lambda_handler(event, context):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    data = 'Triggered at time ' + current_time
    print(data)

    # TODO fetch data from ThreatExchange
    threat_exchange_data = [
        {'should_delete' : False,
         'data' : data}
        ]

    # TODO add TE data to indexer

    return {
        'statusCode': 200,
        'body': json.dumps(threat_exchange_data)
    }
