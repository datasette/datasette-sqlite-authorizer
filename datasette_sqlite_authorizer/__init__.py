from datasette import hookimpl
import sqlite3


CONSTANTS = {
    getattr(sqlite3, c): c
    for c in dir(sqlite3)
    if (
        c.startswith("SQLITE_")
        and isinstance(getattr(sqlite3, c), int)
        and c not in ("SQLITE_OK", "SQLITE_IGNORE", "SQLITE_DENY")
    )
}

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
