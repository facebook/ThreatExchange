from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

# Database configuration
PRODUCTION = False
DBUSER = "media_match"
DBPASS = "hunter2"
DBHOST = "localhost"
DBNAME = "media_match"
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True

# Installed signal types
SIGNAL_TYPES = [PdqSignal, VideoMD5Signal]


# APScheduler (background threads for development)
SCHEDULER_API_ENABLED = True
