from hmalib.common.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    if is_s3_event(event):
        return process_s3_event(event)

    return {"result": "failed to process event", "event": event}


def is_s3_event(event) -> bool:
    return all("s3" in record for record in event["Records"])


def process_s3_event(event) -> dict:
    logger.info(event)
    return {"result": "successfully sent s3 event to hasher [MOCKED]", "event": event}
