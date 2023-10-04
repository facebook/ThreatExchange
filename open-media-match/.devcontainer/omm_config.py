from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

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

SIGNAL_TYPES = [PdqSignal, VideoMD5Signal]
