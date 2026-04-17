# Seeds 100k pdq hashes via InfiniteRandomExchange, then reconfigures the
# collab so each fetcher cycle does +1 create / -1 delete -- signal count
# stays locked at the seed value while the index still rebuilds and reloads
# every cycle.
#
# End state in DB after this script runs:
#
#     InfiniteRandomExchangeCollabConfig(
#         name="LEAK_TEST",
#         api="infinite_random",
#         enabled=True,
#         new_items_per_fetch_iter=1,
#         new_items_per_fetch=1,
#         deletes_per_fetch_iter=1,
#         updates_per_fetch_iter=0,
#         total_item_limit=-1,
#         only_signal_types={"pdq"},
#     )
"""Seed 100k pdq entries via one-shot InfiniteRandom fetch (not direct SQL)
so that exchange_data, bank_content, and content_signal all exist.
Then reconfigure to net-zero."""
import sys, os, time
sys.path.insert(0, '/home/tao/ThreatExchange/hasher-matcher-actioner/src')
os.environ['OMM_CONFIG'] = '/home/tao/ThreatExchange/hasher-matcher-actioner/reference_omm_configs/development_omm_config.py'
os.environ['OMM_DATABASE_URI'] = 'postgresql+psycopg2://postgres:postgres@localhost:5432/media_match'

from OpenMediaMatch.app import create_app
from OpenMediaMatch import persistence
from OpenMediaMatch.background_tasks import fetcher
from OpenMediaMatch.utils.fetch_benchmarking import InfiniteRandomExchangeCollabConfig, InfiniteRandomExchange

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 100000

app = create_app()
with app.app_context():
    storage = persistence.get_storage()
    # Step 1: configure to SEED mode (large create, no delete)
    cfg = InfiniteRandomExchangeCollabConfig(
        name="LEAK_TEST",
        api=InfiniteRandomExchange.get_name(),
        enabled=True,
        new_items_per_fetch_iter=1000,
        new_items_per_fetch=SEED,
        total_item_limit=-1,
        deletes_per_fetch_iter=0,
        updates_per_fetch_iter=0,
        only_signal_types={"pdq"},
    )
    try: storage.exchange_delete("LEAK_TEST")
    except Exception: pass
    storage.exchange_update(cfg, create=True)
    print(f"Configured for seed of {SEED}; running fetch_all...")
    t0 = time.time()
    fetcher.fetch_all(storage, storage.get_signal_type_configs())
    print(f"fetch_all done in {time.time()-t0:.1f}s")
    # Verify count
    from sqlalchemy import text
    from OpenMediaMatch.storage.postgres import database
    count = database.db.session.execute(text("SELECT count(*) FROM content_signal WHERE signal_type='pdq'")).scalar()
    print(f"pdq content_signal rows: {count:,}")

    # Step 2: reconfigure to NET-ZERO mode
    cfg2 = InfiniteRandomExchangeCollabConfig(
        name="LEAK_TEST",
        api=InfiniteRandomExchange.get_name(),
        enabled=True,
        new_items_per_fetch_iter=1,
        new_items_per_fetch=1,           # 1 create per fetch cycle
        total_item_limit=-1,
        deletes_per_fetch_iter=1,         # 1 delete per iter (= per fetch at this config)
        updates_per_fetch_iter=0,
        only_signal_types={"pdq"},
    )
    storage.exchange_update(cfg2)
    print(f"Reconfigured to net-zero: {cfg2}")
