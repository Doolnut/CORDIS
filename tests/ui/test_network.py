import pytest
from tests.data.test_loader import data_dir


def test_build_edges_finds_shared_projects(data_dir):
    from src.data.loader import create_connection
    from src.ui.network import build_co_participation_edges
    conn = create_connection(data_dir)
    edges = build_co_participation_edges(conn, top_n=50)
    assert len(edges) >= 1
    names = set(edges["org_a"].tolist() + edges["org_b"].tolist())
    assert "Acme Corp" in names
