import os
from hmalib.aws_secrets import AWSSecrets
from threatexchange.api import ThreatExchangeAPI

os.environ[
    "THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"
] = "threatexchange/dipanjanm_api_tokens"

api = ThreatExchangeAPI(AWSSecrets().te_api_key())

description_to_hash = {
    "breaking-news.mp4": "e255a0f7186963764b984c8c00c1f98b",
    "empty-london-streets.mp4": "bb172bf87320056a619011f99735b83d",
    "ice-sheet-collapse.mp4": "4dde158717d97bd9c1ee9cd6a818765f",
    "scottish-fold-cat.mp4": "7a227535efcf0a5a9dfb3ed84a1b5de1",
    "beiging-traffic.mp4": "b1aa35aec2a92edeee4397de86a4d7e3",
    "bungee.mp4": "0a9235a623af789ec00d6ce9ff31cc92",
    "chloroplasts.mp4": "2a12f2972373fbd3f693a74adc9042fe",
}


for k in description_to_hash:
    indicator = description_to_hash[k]
    description = k
    api.upload_threat_descriptor(
        {
            "indicator": indicator,
            "type": "HASH_VIDEO_MD5",
            "description": description,
            "share_level": "RED",
            "tags": "uploaded_by_hma",
            "status": "MALICIOUS",
            "privacy_type": "HAS_PRIVACY_GROUP",
            "privacy_members": "303636684709969",
        },
        True,
        False,
    )
