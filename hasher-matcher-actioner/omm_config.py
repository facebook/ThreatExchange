import os
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

# Database configuration
PRODUCTION = True
DBUSER = os.environ.get("POSTGRES_USER", "media_match")
DBPASS = os.environ.get("POSTGRES_PASSWORD", "hunter2")
DBHOST = os.environ.get("POSTGRESS_HOST", "db")
DBNAME = os.environ.get("POSTGRESS_DBNAME", "media_match")
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True

# Installed SignalTypes
SIGNAL_TYPES = [PdqSignal, VideoMD5Signal]
