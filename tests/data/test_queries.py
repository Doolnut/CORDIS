import pytest
from tests.data.test_loader import data_dir  # reuse fixture


def test_get_filter_options_countries(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import get_filter_options
    conn = create_connection(data_dir)
    opts = get_filter_options(conn)
    assert "DE" in opts["countries"]


def test_get_filter_options_activity_types(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import get_filter_options
    conn = create_connection(data_dir)
    opts = get_filter_options(conn)
    assert "PRC" in opts["activity_types"]
    assert "HES" in opts["activity_types"]


def test_query_organizations_no_filters(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={})
    assert len(df) == 2  # 2 unique orgs (Acme appears twice but deduplicated)


def test_query_organizations_filter_by_activity_type(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={"activity_types": ["PRC"]})
    assert all(df["activityType"] == "PRC")
    assert len(df) == 1


def test_query_organizations_filter_by_country(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={"countries": ["DE"]})
    assert len(df) >= 1


def test_query_organizations_search_term(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={"search": "machine"})
    assert len(df) >= 1


def test_top_companies_by_project_count(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import top_companies_by_project_count
    conn = create_connection(data_dir)
    df = top_companies_by_project_count(conn, filters={}, limit=10)
    assert "name" in df.columns
    assert "project_count" in df.columns
    acme = df[df["name"] == "Acme Corp"]
    assert acme.iloc[0]["project_count"] == 2
