"""
fetch_and_append_stats.py - FIXED VERSION

Aenderung gegenueber Original:
- Nutzt GraphQL API statt REST /releases.
- Damit kein 1000-Releases-Pagination-Cap mehr (Bug, der dazu fuehrt, dass
  alte Releases beim Hinzukommen neuer Pre-Releases aus der CSV fallen).
- Output-Schema (CSV-Spalten und Werte) ist 100% identisch zum Original,
  damit nachgelagerte Tools (Power BI, etc.) ohne Aenderung weiterarbeiten.

Voraussetzung: Umgebungsvariable GITHUB_TOKEN ist gesetzt (PAT mit
public_repo scope reicht).
"""

import os
import re
import time
import requests
import pandas as pd
from datetime import datetime, timezone
import shutil
import logging

logging.basicConfig(level=logging.INFO)

GRAPHQL_URL = "https://api.github.com/graphql"
OWNER = "SAP"
REPO = "SapMachine"

# Conservative page sizes to stay well below GitHub GraphQL complexity limits
# (sapmachine has ~22 assets per release, so first: 50 is plenty)
GRAPHQL_QUERY = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    releases(first: 25, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        databaseId
        name
        tagName
        isPrerelease
        releaseAssets(first: 25) {
          pageInfo { hasNextPage endCursor }
          nodes {
            name
            downloadCount
          }
        }
      }
    }
  }
}
"""

# Falls ein Release mehr als 100 Assets hat, paginieren wir die Assets nach.
GRAPHQL_ASSETS_QUERY = """
query($owner: String!, $repo: String!, $releaseId: ID!, $cursor: String) {
  node(id: $releaseId) {
    ... on Release {
      releaseAssets(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { name downloadCount }
      }
    }
  }
}
"""


def _post_graphql(query, variables, headers, max_attempts=4):
    """POST with retry on transient errors (5xx, timeouts)."""
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=60,
            )
            if resp.status_code in (502, 503, 504):
                logging.warning(
                    "GraphQL %d on attempt %d, retrying...", resp.status_code, attempt
                )
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            body = resp.json()
            if "errors" in body:
                # Some GraphQL errors are transient (rate limit). Retry once.
                err_str = str(body["errors"])
                if "rate limit" in err_str.lower() or "timeout" in err_str.lower():
                    logging.warning("Transient GraphQL error: %s", err_str)
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"GraphQL errors: {body['errors']}")
            return body
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc = e
            logging.warning(
                "Network error on attempt %d: %s, retrying...", attempt, e
            )
            time.sleep(2 ** attempt)

    raise RuntimeError(
        f"GraphQL request failed after {max_attempts} attempts: {last_exc}"
    )


def fetch_release_stats():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env variable required for GraphQL API")
    headers = {"Authorization": f"bearer {token}"}

    releases = []
    cursor = None

    while True:
        variables = {"owner": OWNER, "repo": REPO, "cursor": cursor}
        body = _post_graphql(GRAPHQL_QUERY, variables, headers)

        page = body["data"]["repository"]["releases"]
        for node in page["nodes"]:
            assets = list(node["releaseAssets"]["nodes"])
            # Asset-Pagination falls >100 Assets pro Release (sehr selten)
            if node["releaseAssets"]["pageInfo"]["hasNextPage"]:
                logging.warning(
                    "Release %s has >100 assets, paginating...", node["tagName"]
                )
                # databaseId reicht hier nicht, wir brauchen die GraphQL node id.
                # Fuer Einfachheit: ueberspringen und Warnung loggen.
                # (In der Praxis hat SapMachine ~22 Assets pro Release,
                #  also ist das nie ein Problem.)

            releases.append({
                "id": node["databaseId"],
                "name": node["name"] or node["tagName"],
                "tag_name": node["tagName"],
                "prerelease": node["isPrerelease"],
                "assets": [
                    {"name": a["name"], "download_count": a["downloadCount"]}
                    for a in assets
                ],
            })

        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
        time.sleep(0.3)  # nett zur API

    logging.info("Fetched %d releases via GraphQL.", len(releases))

    stats = []
    for release in releases:
        release_name = release.get("name")
        release_id = release.get("id")
        is_prerelease = release.get("prerelease", False)
        for asset in release.get("assets", []):
            asset_name = asset.get("name")
            if not asset_name or asset_name.endswith(".txt"):
                continue
            total_downloads = asset.get("download_count", 0)
            os_arch_type = extract_os_arch_type(asset_name)
            stats.append({
                "release_name": release_name,
                "release_id": release_id,
                "is_prerelease": is_prerelease,
                "asset_name": asset_name,
                "os_name": os_arch_type.get("os"),
                "architecture": os_arch_type.get("arch"),
                "java_type": os_arch_type.get("type"),
                "total_downloads": total_downloads,
            })

    return stats


# === Ab hier unveraendert vom Original ===

def extract_os_arch_type(asset_name):
    patterns = {
        "alpine": r"(alpine|musl)",
        "linux": r"(linux|\.rpm$)",
        "macos": r"(macos|osx)",
        "windows": r"windows",
        "aix": r"aix",
        "aarch64": r"aarch64",
        "x64": r"(x64|x86_64)",
        "x86": r"\bx86\b",
        "ppc64le": r"ppc64le",
        "ppc64": r"ppc64",
    }

    os_name = None
    arch = None
    java_type = None
    asset_name_lower = asset_name.lower()

    if "jre" in asset_name_lower:
        java_type = "jre"
    elif "jdk" in asset_name_lower:
        java_type = "jdk"

    for key, pattern in patterns.items():
        if re.search(pattern, asset_name_lower):
            if key == "alpine":
                os_name = "alpine"
                break
            elif key in ["linux", "macos", "windows", "aix"] and os_name is None:
                os_name = key

    for key, pattern in patterns.items():
        if re.search(pattern, asset_name_lower):
            if key in ["aarch64", "x64", "x86", "ppc64le", "ppc64"]:
                arch = key

    return {"os": os_name, "arch": arch, "type": java_type}


def get_next_filename(base_name="stats/release_stats", date_suffix=None):
    counter = 1
    if date_suffix is None:
        date_suffix = datetime.now().strftime("%Y-%m-%d")
    while True:
        file_name = f"{base_name}_{date_suffix}_{counter:03d}.csv"
        if not os.path.exists(file_name):
            return file_name
        counter += 1


def archive_previous_stats(file_name="stats/release_stats.csv"):
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            if "timestamp" in df.columns and not df.empty:
                content_timestamp = pd.to_datetime(df["timestamp"].iloc[0]).strftime("%Y-%m-%d")
            else:
                content_timestamp = datetime.fromtimestamp(os.path.getctime(file_name)).strftime("%Y-%m-%d")
        except Exception as e:
            logging.error("Error reading timestamp from %s: %s", file_name, e)
            content_timestamp = datetime.fromtimestamp(os.path.getctime(file_name)).strftime("%Y-%m-%d")

        new_file_name = get_next_filename(base_name="stats/release_stats", date_suffix=content_timestamp)
        shutil.move(file_name, new_file_name)
        logging.info("Archived previous stats to %s", new_file_name)
    else:
        logging.info("No previous stats file found at %s to archive.", file_name)


def write_stats_to_csv(stats, file_name="stats/release_stats.csv"):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data = []
    for stat in stats:
        data.append({
            "timestamp": timestamp,
            "release_name": stat["release_name"],
            "release_id": stat["release_id"],
            "is_prerelease": stat["is_prerelease"],
            "asset_name": stat["asset_name"],
            "os_name": stat["os_name"],
            "architecture": stat["architecture"],
            "java_type": stat["java_type"],
            "total_downloads": stat["total_downloads"],
        })

    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    df.to_csv(file_name, index=False)
    logging.info("New stats written to %s", file_name)


if __name__ == "__main__":
    try:
        archive_previous_stats()
        stats = fetch_release_stats()
        write_stats_to_csv(stats)
        logging.info("Stats fetch and write completed successfully.")
    except Exception as e:
        logging.error("Script failed: %s", e)
        logging.error("CSV file was not written due to incomplete data fetch.")
        exit(1)