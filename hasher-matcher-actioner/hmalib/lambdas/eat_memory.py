from hmalib.common.logging import get_logger
from threatexchange.signal_type.pdq_index import PDQIndex,PDQFlatIndex
from threatexchange.signal_type.signal_base import TrivialSignalTypeIndex
import secrets


# Make upload_docker
# terraform -chdir=terraform apply

logger = get_logger(__name__)

items = []
indexDict = {'PDQIndex':PDQIndex,'PDQFlatIndex':PDQFlatIndex,'TrivialSignalTypeIndex':TrivialSignalTypeIndex}
def index_increaser(indexType):
    logger.info(len(items))
    indexType.build(items)
    logger.info(f'{indexType} Built')


def lambda_handler(event, context):
    events = list(event.values())
    i= 1
    while i < (int(events[1])+1):
        items.append((secrets.token_hex(32),{"content_id": "8a642764-efab-4d53-a601-523abdcebee3"}))
        i +=1
    index_increaser(indexDict[events[0]])
    items.clear()

