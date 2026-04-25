import streamlit as st
import pandas as pd
import duckdb
from pyvis.network import Network
import streamlit.components.v1 as components


def build_co_participation_edges(
    conn: duckdb.DuckDBPyConnection, top_n: int = 50, min_shared: int = 1
) -> pd.DataFrame:
    top_orgs = conn.execute(f"""
        SELECT name, COUNT(DISTINCT projectID) AS project_count
        FROM organization
        GROUP BY name
        ORDER BY project_count DESC
        LIMIT {top_n}
    """).df()

    if top_orgs.empty:
        return pd.DataFrame(columns=["org_a", "org_b", "shared_projects"])

    edges = conn.execute(f"""
        WITH top AS (
            SELECT name FROM organization
            GROUP BY name
            ORDER BY COUNT(DISTINCT projectID) DESC
            LIMIT {top_n}
        )
        SELECT
            a.name AS org_a,
            b.name AS org_b,
            COUNT(DISTINCT a.projectID) AS shared_projects
        FROM organization a
        JOIN organization b ON a.projectID = b.projectID AND a.name < b.name
        WHERE a.name IN (SELECT name FROM top)
          AND b.name IN (SELECT name FROM top)
        GROUP BY a.name, b.name
        HAVING shared_projects >= {min_shared}
        ORDER BY shared_projects DESC
    """).df()

    return edges


def build_network_html(conn: duckdb.DuckDBPyConnection, top_n: int = 50) -> str:
    node_data = conn.execute(f"""
        SELECT name, COUNT(DISTINCT projectID) AS project_count, ANY_VALUE(country) AS country
        FROM organization
        GROUP BY name
        ORDER BY project_count DESC
        LIMIT {top_n}
    """).df()

    edges = build_co_participation_edges(conn, top_n=top_n, min_shared=2)

    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    net.barnes_hut()

    for _, row in node_data.iterrows():
        net.add_node(
            row["name"],
            label=row["name"],
            title=f"{row['name']} ({row['country']}): {row['project_count']} projects",
            size=max(5, min(50, int(row["project_count"]) * 2)),
        )

    for _, row in edges.iterrows():
        net.add_edge(row["org_a"], row["org_b"], value=int(row["shared_projects"]))

    net.set_options("""
    {
      "physics": {"enabled": true, "solver": "barnesHut"},
      "interaction": {"hover": true, "tooltipDelay": 100}
    }
    """)
    return net.generate_html()


def render_network(conn: duckdb.DuckDBPyConnection, filters: dict) -> None:
    top_n = st.slider("Number of top organisations to include", 10, 100, 50, step=10)

    with st.spinner("Building network graph..."):
        html = build_network_html(conn, top_n=top_n)

    st.caption(
        f"Nodes: top {top_n} organisations by project count. "
        "Edges: organisations that co-appear in the same project (min 2 shared)."
    )
    components.html(html, height=620, scrolling=False)
