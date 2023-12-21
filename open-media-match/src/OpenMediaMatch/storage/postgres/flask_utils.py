# Copyright (c) Meta Platforms, Inc. and affiliates.

import click
import flask
from sqlalchemy.sql import text, select
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.schema import DropConstraint, DropTable, MetaData, Table


from OpenMediaMatch.storage.postgres import database


def add_cli_commands(app: flask.Flask) -> None:
    @app.cli.command("create_tables")
    def create_tables():
        """Create all the tables based on the database module"""
        with app.app_context():
            database.db.create_all()

    @app.cli.command("table_stats")
    def table_stats():
        """Simple stats about the database"""
        with app.app_context():
            print("Banks:", database.Bank.query.count())
            print("Contents:", database.BankContent.query.count())
            print("Signals/Hashes:", database.ContentSignal.query.count())
            print("Signals/Index:", database.SignalIndex.query.count())
            print(
                "Postgres Large Object Volumes:",
                database.db.session.execute(
                    text("SELECT count(1) FROM pg_largeobject_metadata;")
                ).scalar_one(),
            )
            print("Exchanges:", database.CollaborationConfig.query.count())
            print("ExchangeData:", database.ExchangeData.query.count())

    @app.cli.command("reset_all_tables")
    @click.option("-n", "--nocreate", is_flag=True, help="Do drop only")
    @click.option(
        "-D", "--dropharder", is_flag=True, help="For when drop_all has failed us"
    )
    def _reset_tables(nocreate: bool, dropharder: bool) -> None:
        """Clears all the tables and recreates them"""
        with app.app_context():
            reset_tables(nocreate=nocreate, dropharder=dropharder)


def reset_tables(*, nocreate: bool = False, dropharder: bool = False) -> None:
    """Clears all the tables and recreates them"""
    # drop_all occasionally not strong enough enough
    if dropharder:
        _drop_harder()
    else:
        database.db.drop_all()
    database.db.session.execute(
        text("SELECT lo_unlink(l.oid) FROM pg_largeobject_metadata l;")
    )
    if not nocreate:
        database.db.create_all()


def _drop_harder():
    """
    Source: https://github.com/pallets-eco/flask-sqlalchemy/issues/722
    """

    con = database.db.engine.connect()
    trans = con.begin()
    inspector = Inspector.from_engine(database.db.engine)

    # We need to re-create a minimal metadata with only the required things to
    # successfully emit drop constraints and tables commands for postgres (based
    # on the actual schema of the running instance)
    meta = MetaData()
    tables = []
    all_fkeys = []

    for table_name in inspector.get_table_names():
        fkeys = []

        for fkey in inspector.get_foreign_keys(table_name):
            if not fkey["name"]:
                continue

            fkeys.append(database.db.ForeignKeyConstraint((), (), name=fkey["name"]))

        tables.append(Table(table_name, meta, *fkeys))
        all_fkeys.extend(fkeys)

    for fkey in all_fkeys:
        con.execute(DropConstraint(fkey))

    for table in tables:
        con.execute(DropTable(table))

    trans.commit()
