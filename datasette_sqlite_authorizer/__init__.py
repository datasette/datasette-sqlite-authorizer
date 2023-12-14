from datasette import hookimpl
import sqlite3


ACTIONS = {
    "SQLITE_CREATE_INDEX",
    "SQLITE_CREATE_TABLE",
    "SQLITE_CREATE_TEMP_INDEX",
    "SQLITE_CREATE_TEMP_TABLE",
    "SQLITE_CREATE_TEMP_TRIGGER",
    "SQLITE_CREATE_TEMP_VIEW",
    "SQLITE_CREATE_TRIGGER",
    "SQLITE_CREATE_VIEW",
    "SQLITE_DELETE",
    "SQLITE_DROP_INDEX",
    "SQLITE_DROP_TABLE",
    "SQLITE_DROP_TEMP_INDEX",
    "SQLITE_DROP_TEMP_TABLE",
    "SQLITE_DROP_TEMP_TRIGGER",
    "SQLITE_DROP_TEMP_VIEW",
    "SQLITE_DROP_TRIGGER",
    "SQLITE_DROP_VIEW",
    "SQLITE_INSERT",
    "SQLITE_PRAGMA",
    "SQLITE_READ",
    "SQLITE_SELECT",
    "SQLITE_TRANSACTION",
    "SQLITE_UPDATE",
    "SQLITE_ATTACH",
    "SQLITE_DETACH",
    "SQLITE_ALTER_TABLE",
    "SQLITE_REINDEX",
    "SQLITE_ANALYZE",
    "SQLITE_CREATE_VTABLE",
    "SQLITE_DROP_VTABLE",
    "SQLITE_FUNCTION",
    "SQLITE_SAVEPOINT",
    "SQLITE_RECURSIVE",
}

# Define the CONSTANTS mapping
CONSTANTS = {getattr(sqlite3, c): c for c in dir(sqlite3) if c in ACTIONS}

READ_ONLY_DENIED_ACTIONS = {
    "SQLITE_DELETE",
    "SQLITE_DROP_TABLE",
    "SQLITE_INSERT",
    "SQLITE_UPDATE",
    "SQLITE_ALTER_TABLE",
}


def make_authorizer(config, database):
    # None in the first column means all databases
    read_only_tables = [
        (t.get("database"), t["table"]) for t in config.get("read_only_tables") or []
    ]

    def authorizer(action_int, arg1, arg2, db_name, trigger_name):
        table = arg1
        action = CONSTANTS.get(action_int)
        if action == "SQLITE_ALTER_TABLE":
            table = arg2

        if action not in READ_ONLY_DENIED_ACTIONS:
            return sqlite3.SQLITE_OK

        if (None, table) in read_only_tables or (database, table) in read_only_tables:
            return sqlite3.SQLITE_DENY

        return sqlite3.SQLITE_OK

    return authorizer


@hookimpl
def prepare_connection(conn, datasette, database):
    config = datasette.plugin_config("datasette-sqlite-authorizer")
    if not config:
        return
    conn.set_authorizer(make_authorizer(config, database))
