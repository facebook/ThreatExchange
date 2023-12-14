# Database configuration
PRODUCTION = False
DBUSER = "media_match"
DBPASS = "hunter2"
DBHOST = "localhost"
DBNAME = "media_match_test"
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True

TASK_FETCHER = False
TASK_INDEXER = False
