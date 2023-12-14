from datasette.app import Datasette
import pytest
import sqlite3


@pytest.fixture
def db_paths(tmpdir):
    db_paths = []
    for name in ("test1.db", "test2.db"):
        db_path = str(tmpdir / name)
        conn = sqlite3.connect(db_path)
        with conn:
            conn.executescript(
                """
                create table protected (id integer primary key, name text);
                insert into protected (name) values ('one');
                """
            )
        db_paths.append(db_path)
    return db_paths


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sql",
    (
        "delete from protected",
        "delete from protected where id = 1",
        "update protected set name = 'foo'",
        "drop table protected",
        "insert into protected (name) values ('two')",
        "alter table protected rename to protected2",
    ),
)
@pytest.mark.parametrize("configured", (True, False))
@pytest.mark.parametrize("test1_only", (None, "test1"))
async def test_read_only_tables(sql, configured, db_paths, test1_only):
    metadata = {}
    if configured:
        rule = {
            "table": "protected",
        }
        if test1_only:
            rule["database"] = "test1"
        metadata = {
            "plugins": {"datasette-sqlite-authorizer": {"read_only_tables": [rule]}}
        }

    datasette = Datasette(db_paths, metadata=metadata)
    db = datasette.get_database("test1")
    if configured:
        # SQL should not be allowed
        with pytest.raises(Exception):
            await db.execute_write(sql)

        if test1_only:
            # SQL should be allowed on test2
            db2 = datasette.get_database("test2")
            await db2.execute_write(sql)
        else:
            # SQL should not be allowed on test2
            db2 = datasette.get_database("test2")
            with pytest.raises(Exception):
                await db2.execute_write(sql)

    else:
        # SQL should be allowed
        await db.execute_write(sql)
