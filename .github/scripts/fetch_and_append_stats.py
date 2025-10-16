import requests
import csv
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# GitHub repository details (replace with your own)
REPO_ID = "110605490"  # Example: repo numeric ID
OUTPUT_FILE = "stats/release_stats.csv"
ARCHIVE_DIR = "stats"

# GitHub API base URL
BASE_URL = f"https://api.github.com/repositories/{REPO_ID}/releases"

# Ensure stats directory exists
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Archive the previous stats file, if it exists
if os.path.exists(OUTPUT_FILE):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    archived_file = os.path.join(ARCHIVE_DIR, f"release_stats_{timestamp}.csv")
    os.rename(OUTPUT_FILE, archived_file)
    logging.info(f"Archived previous stats to {archived_file}")

# Fetch releases with pagination
releases = []
url = BASE_URL

while url:
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Some repos might return a single object instead of a list
        if isinstance(data, dict):
            data = [data]

        releases.extend(data)

        # Get URL for next page (if available)
        url = response.links.get("next", {}).get("url")

    except requests.HTTPError as e:
        # Special case for 422 errors (no more pages)
        if e.response is not None and e.response.status_code == 422:
            logging.warning(f"Reached invalid page or no more results: {url}")
            break
        logging.error(f"Error fetching data from GitHub API: {e}")
        break
    except requests.RequestException as e:
        logging.error(f"Error fetching data from GitHub API: {e}")
        break

# Write the data to CSV
if releases:
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "tag_name", "name", "published_at", "html_url"])
        for r in releases:
            writer.writerow([
                r.get("id", ""),
                r.get("tag_name", ""),
                r.get("name", ""),
                r.get("published_at", ""),
                r.get("html_url", "")
            ])
    logging.info(f"New stats written to {OUTPUT_FILE}")
else:
    logging.warning("No releases found — no CSV written.")
