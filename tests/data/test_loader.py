import pytest
import duckdb
import os
import csv


def make_fixture_csvs(path: str):
    """Create minimal valid CSV fixtures matching the real schema."""
    os.makedirs(path, exist_ok=True)

    project_rows = [
        ["id", "acronym", "status", "title", "startDate", "endDate",
         "totalCost", "ecMaxContribution", "legalBasis", "topics",
         "frameworkProgramme", "objective", "keywords"],
        ["101", "TEST1", "SIGNED", "Test Project One", "2023-01-01",
         "2026-01-01", "500000", "400000", "HORIZON.1.2", "AI",
         "HORIZON", "Test objective", "machine learning"],
        ["102", "TEST2", "CLOSED", "Test Project Two", "2022-01-01",
         "2024-01-01", "200000", "180000", "HORIZON.2.4", "BIO",
         "HORIZON", "Bio objective", "biotech"],
    ]
    org_rows = [
        ["projectID", "organisationID", "name", "shortName", "SME",
         "activityType", "city", "country", "geolocation",
         "organizationURL", "contactForm", "role",
         "ecContribution", "netEcContribution", "totalCost", "active"],
        ["101", "9001", "Acme Corp", "ACME", "false", "PRC",
         "Berlin", "DE", "52.52,13.40", "http://acme.com", "", "coordinator",
         "200000", "200000", "250000", "true"],
        ["101", "9002", "Uni Hamburg", "UHH", "false", "HES",
         "Hamburg", "DE", "53.55,9.99", "", "", "participant",
         "200000", "200000", "250000", "true"],
        ["102", "9001", "Acme Corp", "ACME", "false", "PRC",
         "Berlin", "DE", "52.52,13.40", "", "", "coordinator",
         "180000", "180000", "200000", "true"],
    ]

    def write_csv(filename, rows):
        with open(os.path.join(path, filename), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(rows)

    write_csv("project.csv", project_rows)
    write_csv("organization.csv", org_rows)
    for name, headers in [
        ("euroSciVoc.csv", ["projectID", "euroSciVocPath", "euroSciVocTitle"]),
        ("topics.csv", ["projectID", "topic", "title"]),
        ("legalBasis.csv", ["projectID", "legalBasis", "title", "uniqueProgrammePart"]),
        ("policyPriorities.csv", ["projectID", "ai", "biodiversity", "cleanAir", "climate", "digitalAgenda"]),
        ("webLink.csv", ["projectID", "physUrl", "type", "source"]),
    ]:
        write_csv(name, [headers])


@pytest.fixture
def data_dir(tmp_path):
    make_fixture_csvs(str(tmp_path))
    return str(tmp_path)


def test_loader_creates_views(data_dir):
    from src.data.loader import create_connection
    conn = create_connection(data_dir)
    tables = conn.execute("SHOW TABLES").fetchall()
    names = {t[0] for t in tables}
    assert "project" in names
    assert "organization" in names


def test_loader_rejects_missing_data_dir():
    from src.data.loader import create_connection, DataDirectoryError
    with pytest.raises(DataDirectoryError):
        create_connection("/nonexistent/path")


def test_loader_rejects_missing_required_file(tmp_path):
    from src.data.loader import create_connection, DataDirectoryError
    with open(str(tmp_path / "project.csv"), "w") as f:
        f.write("id;title\n")
    with pytest.raises(DataDirectoryError):
        create_connection(str(tmp_path))


def test_project_count(data_dir):
    from src.data.loader import create_connection
    conn = create_connection(data_dir)
    count = conn.execute("SELECT COUNT(*) FROM project").fetchone()[0]
    assert count == 2


def test_organization_count(data_dir):
    from src.data.loader import create_connection
    conn = create_connection(data_dir)
    count = conn.execute("SELECT COUNT(*) FROM organization").fetchone()[0]
    assert count == 3
