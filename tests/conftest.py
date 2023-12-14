import sqlite3

def pytest_report_header(config):
    return "SQLite: {}".format(
        sqlite3.connect(":memory:").execute("select sqlite_version()").fetchone()[0]
    )
