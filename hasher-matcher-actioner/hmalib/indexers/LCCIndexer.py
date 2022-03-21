from threatexchange.signal_type.pdq_index import PDQIndex
from hmalib.common.logging import get_logger
from datetime import timedelta, datetime
import time
from threatexchange.signal_type.timebucketizer import TimeBucketizer, CSViable
import pickle
starttime = time.time()
logger = get_logger(__name__)
import typing as t
from dataclasses import dataclass

# @staticmethod
# def get_file_contents2(
#         since: datetime.datetime,
        # until: datetime.datetime,
        # type: str,
        # storage_path: str,
        # bucket_width: datetime.timedelta,
        # type_class: t.Type[CSViable],
# ):

Self = t.TypeVar("Self", bound="CSViable")

@dataclass(eq=True)
class HashRecord(CSViable):
    """
    Example class used for testing purposes.
    """
    content_hash:str
    content_id:str

    def to_csv(self) -> t.List[t.Union[str, int]]:
        return [self.content_hash, self.content_id]

    @classmethod
    def from_csv(cls: t.Type[Self], value: t.List[str]) -> Self:
        return HashRecord(value[0],value[1])
class LCCIndexer:
  @classmethod
  def get_recent_index(cls) -> PDQIndex:
     """ Get the most recent index. """
    #  find some way to access most recent index in file structure
    #indexObjPath = path of index with latest creation time (should already be sorted by time in file structure)
    # file = open(indexObjPath,"r")
    #latest_index = pickle.load(file)
    #file.close()
    #return latest_index

  @classmethod
  def build_index_from_last_24h(cls) -> void:
    """ Create an index """
    d = timedelta(days=1)

    past_day_content = TimeBucketizer.get_records((datetime.now()-d),datetime.now(),
    "hasher","/tmp/makethisdirectory/ ",d,SampleCSViableClass)
    now = datetime.now()

    testIndex = PDQIndex.build(past_day_content)
    #variable name with creation time, index type, time delta value
    indexObj= {testIndex,datetime.now(),PDQIndex,d}
    # write_path = open(indexpath,"w")
    pickle.dump(indexObj,write_path)
    # example file structure 
    #"/var/data/threatexchange/LCCIndexes/<hash_type>/2022-02-08-20-45-<pickle-name>.pickle"
    # os.listdirs, check if this returns sorted list of files
