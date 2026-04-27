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
    "Pillars.csv",
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


def build_summary_tables(conn: duckdb.DuckDBPyConnection) -> None:
    _build_org_project_base(conn)
    _build_org_search_index(conn)


def _create_views(conn: duckdb.DuckDBPyConnection, data_path: Path) -> None:
    semicolon_views = {
        "project": "project.csv",
        "organization": "organization.csv",
        "euro_sci_voc": "euroSciVoc.csv",
        "topics": "topics.csv",
        "legal_basis": "legalBasis.csv",
        "policy_priorities": "policyPriorities.csv",
        "web_link": "webLink.csv",
    }
    for view_name, filename in semicolon_views.items():
        file_path = str(data_path / filename).replace("\\", "/")
        conn.execute(
            f"CREATE VIEW {view_name} AS "
            f"SELECT * FROM read_csv_auto('{file_path}', delim=';', header=true, "
            f"ignore_errors=true, normalize_names=true)"
        )

    pillars_path = str(data_path / "Pillars.csv").replace("\\", "/")
    conn.execute(
        f"CREATE VIEW pillars AS "
        f"SELECT * FROM read_csv_auto('{pillars_path}', delim=',', header=true, "
        f"ignore_errors=true, normalize_names=true)"
    )


def _build_org_project_base(conn: duckdb.DuckDBPyConnection) -> None:
    """One row per org-project pair. All expensive joins done once here.
    Filters at query time use simple WHERE clauses against this table."""
    conn.execute("DROP TABLE IF EXISTS org_project_base")
    conn.execute("""
        CREATE TABLE org_project_base AS
        WITH project_pillar AS (
            SELECT
                lb.projectid                  AS projectid_clean,
                ANY_VALUE(pi.pillar)          AS pillar
            FROM legal_basis lb
            JOIN pillars pi ON pi.legalbasis = lb.legalbasis
            WHERE lb.uniqueprogrammepart IS TRUE
            GROUP BY lb.projectid
        )
        SELECT
            o.organisationid,
            TRIM('"' FROM o._name)                                        AS name,
            TRIM('"' FROM o.activitytype)                                 AS activitytype,
            TRIM('"' FROM o.sme)                                          AS sme,
            TRIM('"' FROM o.city)                                         AS city,
            TRIM('"' FROM o.country)                                      AS country,
            TRIM('"' FROM o.geolocation)                                  AS geolocation,
            TRIM('"' FROM o.organizationurl)                              AS organizationurl,
            o.projectid,
            TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE)        AS eccontribution,
            TRIM('"' FROM p.status)                                       AS status,
            TRIM('"' FROM p.frameworkprogramme)                           AS framework,
            pp_pillar.pillar                                               AS pillar,
            COALESCE(TRY_CAST(pp.ai           AS INTEGER), 0)             AS has_ai,
            COALESCE(TRY_CAST(pp.climate      AS INTEGER), 0)             AS has_climate,
            COALESCE(TRY_CAST(pp.biodiversity AS INTEGER), 0)             AS has_biodiversity,
            COALESCE(TRY_CAST(pp.cleanair     AS INTEGER), 0)             AS has_cleanair,
            COALESCE(TRY_CAST(pp.digitalagenda AS INTEGER), 0)            AS has_digitalagenda
        FROM organization o
        JOIN project p ON p.id = o.projectid
        LEFT JOIN policy_priorities pp
            ON pp.projectid = TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)
        LEFT JOIN project_pillar pp_pillar
            ON pp_pillar.projectid_clean = TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)
    """)


def _build_org_search_index(conn: duckdb.DuckDBPyConnection) -> None:
    """One row per org with pre-aggregated searchable text.
    ESV is pre-aggregated by project in a CTE to avoid row explosion."""
    conn.execute("DROP TABLE IF EXISTS org_search_index")
    conn.execute("""
        CREATE TABLE org_search_index AS
        WITH esv_by_project AS (
            SELECT
                projectid,
                STRING_AGG(euroscivoctitle, ' ') AS sci_voc
            FROM euro_sci_voc
            GROUP BY projectid
        )
        SELECT
            o.organisationid,
            STRING_AGG(DISTINCT TRIM('"' FROM p.keywords), ' ')                    AS all_keywords,
            STRING_AGG(DISTINCT LEFT(TRIM('"' FROM p.objective), 300), ' ')        AS all_objectives,
            COALESCE(STRING_AGG(DISTINCT ep.sci_voc, ' '), '')                     AS all_sci_voc
        FROM organization o
        JOIN project p ON p.id = o.projectid
        LEFT JOIN esv_by_project ep
            ON ep.projectid = TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)
        GROUP BY o.organisationid
    """)
