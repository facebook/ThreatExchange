# Copyright (c) Meta Platforms, Inc. and affiliates.

import flask

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

    @app.cli.command("reset_all_tables")
    def reset_tables():
        """Clears all the tables and recreates them"""
        with app.app_context():
            # drop_all not smart enough to drop in the right order
            database.db.drop_all()
            database.db.create_all()
