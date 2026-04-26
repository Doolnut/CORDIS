"""
CORDIS Horizon Europe query script.
Downloads, caches, and queries the EU research projects dataset.
Data source: https://cordis.europa.eu/data/cordis-HORIZONprojects-csv.zip
"""
import argparse
import os
import zipfile
import urllib.request
import sys
from pathlib import Path
from io import BytesIO

DATA_URL = "https://cordis.europa.eu/data/cordis-HORIZONprojects-csv.zip"
ORG_CACHE = "cordis_organizations.csv"
PROJECT_CACHE = "cordis_projects.csv"


def download_and_cache(cache_dir: str) -> tuple[str, str]:
    cache_dir = Path(cache_dir)
    org_path = cache_dir / ORG_CACHE
    proj_path = cache_dir / PROJECT_CACHE

    if org_path.exists() and proj_path.exists():
        print(f"Using cached data in {cache_dir}", file=sys.stderr)
        return str(org_path), str(proj_path)

    print("Downloading CORDIS dataset (~30MB)...", file=sys.stderr)
    cache_dir.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(DATA_URL, timeout=120) as response:
        data = response.read()

    print(f"Downloaded {len(data)/1024/1024:.1f} MB, extracting...", file=sys.stderr)

    with zipfile.ZipFile(BytesIO(data)) as zf:
        with zf.open("organization.csv") as f:
            org_path.write_bytes(f.read())
        with zf.open("project.csv") as f:
            proj_path.write_bytes(f.read())

    print("Cached organization.csv and project.csv", file=sys.stderr)
    return str(org_path), str(proj_path)


def load_orgs(org_path: str):
    import pandas as pd
    df = pd.read_csv(org_path, sep=";", dtype=str, low_memory=False)
    df.columns = df.columns.str.strip('"').str.strip()
    # Clean string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip('"').str.strip()
    # Numeric conversion
    for col in ("ecContribution", "netEcContribution", "totalCost"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # Normalise role to lowercase
    if "role" in df.columns:
        df["role"] = df["role"].str.lower().str.strip()
    if "country" in df.columns:
        df["country"] = df["country"].str.upper().str.strip()
    return df


def load_projects(proj_path: str):
    import pandas as pd
    df = pd.read_csv(proj_path, sep=";", dtype=str, low_memory=False)
    df.columns = df.columns.str.strip('"').str.strip()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip('"').str.strip()
    return df


def run_query(orgs: "pd.DataFrame", projects: "pd.DataFrame", query: str):
    import pandas as pd
    q = query.lower().strip()

    # Top N orgs by project count
    if "project" in q and ("top" in q or "count" in q or "most" in q):
        n = _extract_n(q, 10)
        result = (
            orgs.groupby("name")["projectID"]
            .nunique()
            .nlargest(n)
            .reset_index()
            .rename(columns={"name": "Organisation", "projectID": "Projects"})
        )
        result.insert(0, "Rank", range(1, len(result) + 1))
        return result, f"Top {n} organisations by number of distinct projects"

    # Top N orgs by EU funding
    if "fund" in q or "contribution" in q or "receiv" in q or "money" in q or "euro" in q:
        n = _extract_n(q, 10)
        result = (
            orgs.groupby("name")["ecContribution"]
            .sum()
            .nlargest(n)
            .reset_index()
        )
        result["EU Funding (€M)"] = (result["ecContribution"] / 1_000_000).round(2)
        result = result.drop(columns=["ecContribution"])
        result = result.rename(columns={"name": "Organisation"})
        result.insert(0, "Rank", range(1, len(result) + 1))
        return result, f"Top {n} organisations by total EU contribution received"

    # Filter by country
    for marker in ("from ", "in country ", "country "):
        if marker in q:
            country_code = q.split(marker)[-1].strip().split()[0].upper()[:2]
            filtered = orgs[orgs["country"] == country_code]
            result = (
                filtered.groupby("name")["projectID"]
                .nunique()
                .nlargest(20)
                .reset_index()
                .rename(columns={"name": "Organisation", "projectID": "Projects"})
            )
            result.insert(0, "Rank", range(1, len(result) + 1))
            return result, f"Top organisations from {country_code} by project count"

    # Coordinators only
    if "coordinator" in q:
        n = _extract_n(q, 10)
        filtered = orgs[orgs["role"] == "coordinator"]
        result = (
            filtered.groupby("name")["projectID"]
            .nunique()
            .nlargest(n)
            .reset_index()
            .rename(columns={"name": "Organisation", "projectID": "Projects Coordinated"})
        )
        result.insert(0, "Rank", range(1, len(result) + 1))
        return result, f"Top {n} organisations by projects they coordinate"

    # SMEs
    if "sme" in q or "small" in q:
        n = _extract_n(q, 10)
        filtered = orgs[orgs["SME"].str.lower() == "true"]
        result = (
            filtered.groupby("name")["projectID"]
            .nunique()
            .nlargest(n)
            .reset_index()
            .rename(columns={"name": "Organisation", "projectID": "Projects"})
        )
        result.insert(0, "Rank", range(1, len(result) + 1))
        return result, f"Top {n} SMEs by project count"

    # Country summary
    if "countr" in q and ("summar" in q or "breakdown" in q or "by countr" in q):
        result = (
            orgs.groupby("country")["projectID"]
            .nunique()
            .nlargest(30)
            .reset_index()
            .rename(columns={"country": "Country", "projectID": "Distinct Projects"})
        )
        result.insert(0, "Rank", range(1, len(result) + 1))
        return result, "Countries by number of distinct projects they participate in"

    # Overview / summary
    if "summar" in q or "overview" in q or "stats" in q or "total" in q:
        summary_data = {
            "Total projects": projects["id"].nunique() if "id" in projects.columns else orgs["projectID"].nunique(),
            "Total org-project rows": len(orgs),
            "Distinct organisations": orgs["name"].nunique(),
            "Countries represented": orgs["country"].nunique(),
            "Total EU contribution (€B)": round(orgs["ecContribution"].sum() / 1e9, 2),
        }
        result = pd.DataFrame(list(summary_data.items()), columns=["Metric", "Value"])
        return result, "Dataset overview"

    # Search for a specific org name
    if "find" in q or "search" in q or "look" in q:
        search_term = q.replace("find", "").replace("search", "").replace("look for", "").strip()
        filtered = orgs[orgs["name"].str.contains(search_term, case=False, na=False)]
        result = (
            filtered.groupby(["name", "country"])["projectID"]
            .nunique()
            .reset_index()
            .rename(columns={"name": "Organisation", "country": "Country", "projectID": "Projects"})
            .sort_values("Projects", ascending=False)
            .head(20)
        )
        return result, f"Organisations matching '{search_term}'"

    # Default: top 10 by project count
    result = (
        orgs.groupby("name")["projectID"]
        .nunique()
        .nlargest(10)
        .reset_index()
        .rename(columns={"name": "Organisation", "projectID": "Projects"})
    )
    result.insert(0, "Rank", range(1, len(result) + 1))
    return result, "Top 10 organisations by project count (default)"


def _extract_n(text: str, default: int = 10) -> int:
    import re
    m = re.search(r"\b(\d+)\b", text)
    return int(m.group(1)) if m else default


def main():
    parser = argparse.ArgumentParser(description="Query CORDIS Horizon Europe organisations")
    parser.add_argument("--cache-dir", required=True, help="Directory to store cached CSVs")
    parser.add_argument("--query", default="top 10 by project count", help="Natural language query")
    parser.add_argument("--refresh", action="store_true", help="Force re-download")
    args = parser.parse_args()

    if args.refresh:
        for fname in (ORG_CACHE, PROJECT_CACHE):
            p = Path(args.cache_dir) / fname
            if p.exists():
                p.unlink()

    org_path, proj_path = download_and_cache(args.cache_dir)

    print("Loading organisations...", file=sys.stderr)
    orgs = load_orgs(org_path)
    projects = load_projects(proj_path)
    print(
        f"Loaded {len(orgs):,} org-project rows | "
        f"{orgs['name'].nunique():,} distinct orgs | "
        f"{orgs['projectID'].nunique():,} projects",
        file=sys.stderr,
    )

    result, description = run_query(orgs, projects, args.query)
    print(f"\n## {description}\n")
    try:
        print(result.to_markdown(index=False))
    except Exception:
        print(result.to_string(index=False))

    print(f"\n*Source: CORDIS, Horizon Europe 2021-2027*")


if __name__ == "__main__":
    main()
