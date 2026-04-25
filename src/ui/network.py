import streamlit as st
import pandas as pd
import duckdb
from pyvis.network import Network
import streamlit.components.v1 as components
from src.data.queries import query_organizations


def build_co_participation_edges(
    conn: duckdb.DuckDBPyConnection,
    org_names: list[str],
    min_shared: int = 1,
) -> pd.DataFrame:
    if not org_names:
        return pd.DataFrame(columns=["org_a", "org_b", "shared_projects"])

    placeholders = ", ".join([f"'{n.replace(chr(39), chr(39)*2)}'" for n in org_names])

    edges = conn.execute(f"""
        SELECT
            a.name AS org_a,
            b.name AS org_b,
            COUNT(DISTINCT a.projectID) AS shared_projects
        FROM organization a
        JOIN organization b ON a.projectID = b.projectID AND a.name < b.name
        WHERE a.name IN ({placeholders})
          AND b.name IN ({placeholders})
        GROUP BY a.name, b.name
        HAVING shared_projects >= {int(min_shared)}
        ORDER BY shared_projects DESC
    """).df()

    return edges


def build_network_html(
    conn: duckdb.DuckDBPyConnection,
    filters: dict,
    top_n: int = 50,
) -> str:
    # Get filtered organisations sorted by project count
    all_orgs = query_organizations(conn, filters)
    node_df = all_orgs.head(top_n)

    if node_df.empty:
        return "<p>No organisations match the current filters.</p>"

    org_names = node_df["name"].tolist()
    edges = build_co_participation_edges(conn, org_names, min_shared=2)

    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    net.barnes_hut()

    for _, row in node_df.iterrows():
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
        html = build_network_html(conn, filters, top_n=top_n)

    st.caption(
        f"Nodes: top {top_n} filtered organisations by project count. "
        "Edges: organisations that co-appear in the same project (min 2 shared)."
    )
    components.html(html, height=620, scrolling=False)
