from hmalib.common.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    logger.info("bucket_hasher received event")
    logger.info(event)
