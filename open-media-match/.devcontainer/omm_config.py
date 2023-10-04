from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
import typing as t
from threatexchange.signal_type.signal_base import SignalType

# Database configuration
PRODUCTION = False
DBUSER = "media_match"
DBPASS = "hunter2"
DBHOST = "localhost"
DBNAME = "media_match"
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True

SIGNAL_TYPES: list[t.Type[SignalType]] = [PdqSignal, VideoMD5Signal]
