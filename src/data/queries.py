import duckdb
import pandas as pd
from typing import Any


def get_filter_options(conn: duckdb.DuckDBPyConnection) -> dict[str, list]:
    countries = conn.execute(
        "SELECT DISTINCT country FROM organization WHERE country IS NOT NULL ORDER BY country"
    ).df()["country"].tolist()

    activity_types = conn.execute(
        "SELECT DISTINCT activityType FROM organization WHERE activityType IS NOT NULL ORDER BY activityType"
    ).df()["activityType"].tolist()

    frameworks = conn.execute(
        "SELECT DISTINCT frameworkProgramme FROM project WHERE frameworkProgramme IS NOT NULL ORDER BY frameworkProgramme"
    ).df()["frameworkProgramme"].tolist()

    statuses = conn.execute(
        "SELECT DISTINCT status FROM project WHERE status IS NOT NULL ORDER BY status"
    ).df()["status"].tolist()

    return {
        "countries": countries,
        "activity_types": activity_types,
        "frameworks": frameworks,
        "statuses": statuses,
        "policy_priorities": ["ai", "biodiversity", "cleanAir", "climate", "digitalAgenda"],
    }


def query_organizations(
    conn: duckdb.DuckDBPyConnection, filters: dict[str, Any]
) -> pd.DataFrame:
    where_clauses = ["1=1"]
    params: list[Any] = []

    if filters.get("activity_types"):
        placeholders = ", ".join(["?" for _ in filters["activity_types"]])
        where_clauses.append(f"o.activityType IN ({placeholders})")
        params.extend(filters["activity_types"])

    if filters.get("countries"):
        placeholders = ", ".join(["?" for _ in filters["countries"]])
        where_clauses.append(f"o.country IN ({placeholders})")
        params.extend(filters["countries"])

    if filters.get("sme_only"):
        where_clauses.append("o.SME = 'true'")

    if filters.get("project_status"):
        placeholders = ", ".join(["?" for _ in filters["project_status"]])
        where_clauses.append(f"p.status IN ({placeholders})")
        params.extend(filters["project_status"])

    if filters.get("frameworks"):
        placeholders = ", ".join(["?" for _ in filters["frameworks"]])
        where_clauses.append(f"p.frameworkProgramme IN ({placeholders})")
        params.extend(filters["frameworks"])

    if filters.get("search"):
        term = f"%{filters['search']}%"
        where_clauses.append(
            "(p.keywords ILIKE ? OR p.objective ILIKE ? "
            "OR esv.euroSciVocTitle ILIKE ? OR o.name ILIKE ?)"
        )
        params.extend([term, term, term, term])

    if filters.get("policy_priorities"):
        for col in filters["policy_priorities"]:
            where_clauses.append(f"TRY_CAST(pp.{col} AS INTEGER) = 1")

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            o.organisationID,
            ANY_VALUE(o.name)           AS name,
            ANY_VALUE(o.shortName)      AS shortName,
            ANY_VALUE(o.activityType)   AS activityType,
            ANY_VALUE(o.SME)            AS SME,
            ANY_VALUE(o.city)           AS city,
            ANY_VALUE(o.country)        AS country,
            ANY_VALUE(o.organizationURL) AS organizationURL,
            ANY_VALUE(o.contactForm)    AS contactForm,
            ANY_VALUE(o.geolocation)    AS geolocation,
            COUNT(DISTINCT o.projectID) AS project_count,
            SUM(TRY_CAST(o.ecContribution AS DOUBLE)) AS total_ec_contribution
        FROM organization o
        JOIN project p ON p.id = o.projectID
        LEFT JOIN euro_sci_voc esv ON esv.projectID = o.projectID
        LEFT JOIN policy_priorities pp ON pp.projectID = o.projectID
        WHERE {where_sql}
        GROUP BY o.organisationID
        ORDER BY project_count DESC
    """
    return conn.execute(sql, params).df()


def top_companies_by_project_count(
    conn: duckdb.DuckDBPyConnection,
    filters: dict[str, Any],
    limit: int = 25,
) -> pd.DataFrame:
    df = query_organizations(conn, filters)
    return df.nlargest(limit, "project_count")[
        ["name", "country", "activityType", "project_count", "total_ec_contribution"]
    ]


def run_raw_sql(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return conn.execute(sql).df()
