import duckdb
from pathlib import Path

REQUIRED_FILES = [
    "project.csv",
    "organization.csv",
    "euroSciVoc.csv",
    "topics.csv",
    "legalBasis.csv",
    "policyPriorities.csv",
    "webLink.csv",
]


class DataDirectoryError(Exception):
    pass


def create_connection(data_dir: str) -> duckdb.DuckDBPyConnection:
    path = Path(data_dir)
    if not path.exists() or not path.is_dir():
        raise DataDirectoryError(f"Data directory not found: {data_dir}")

    missing = [f for f in REQUIRED_FILES if not (path / f).exists()]
    if missing:
        raise DataDirectoryError(f"Missing required files: {', '.join(missing)}")

    conn = duckdb.connect(database=":memory:")
    _create_views(conn, path)
    return conn


def _create_views(conn: duckdb.DuckDBPyConnection, data_path: Path) -> None:
    views = {
        "project": "project.csv",
        "organization": "organization.csv",
        "euro_sci_voc": "euroSciVoc.csv",
        "topics": "topics.csv",
        "legal_basis": "legalBasis.csv",
        "policy_priorities": "policyPriorities.csv",
        "web_link": "webLink.csv",
    }
    for view_name, filename in views.items():
        file_path = str(data_path / filename).replace("\\", "/")
        conn.execute(
            f"CREATE VIEW {view_name} AS "
            f"SELECT * FROM read_csv_auto('{file_path}', delim=';', header=true, ignore_errors=true, normalize_names=true)"
        )
