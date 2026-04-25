import pytest
from tests.data.test_loader import data_dir


def test_build_edges_finds_shared_projects(data_dir):
    from src.data.loader import create_connection
    from src.ui.network import build_co_participation_edges
    conn = create_connection(data_dir)
    # Acme Corp (9001) and Uni Hamburg (9002) both appear in project 101
    org_names = ["Acme Corp", "Uni Hamburg"]
    edges = build_co_participation_edges(conn, org_names, min_shared=1)
    assert len(edges) >= 1
    names = set(edges["org_a"].tolist() + edges["org_b"].tolist())
    assert "Acme Corp" in names
