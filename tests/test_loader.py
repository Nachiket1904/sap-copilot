from src.data_layer.loader import load_to_sqlite


def test_load_to_sqlite_runs_without_error():
    conn = load_to_sqlite()
    assert conn is not None
    conn.close()
