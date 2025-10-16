import os
import re
import time
import requests
import pandas as pd
from datetime import datetime, timezone
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to fetch download stats for all releases
def fetch_release_stats():
    releases = []
    url = "https://api.github.com/repos/SAP/SapMachine/releases"

    # Use GitHub token if available (avoids 60-requests/hour limit)
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    while url:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Stop if no data returned (end of pagination)
            if not data:
                logging.info("No more releases found, stopping pagination.")
                break

            releases.extend(data)

            # Get the URL for the next page, if it exists
            next_url = response.links.get('next', {}).get('url')
            if not next_url:
                break  # no next page
            url = next_url

            # Be nice to the GitHub API
            time.sleep(1)

        except requests.RequestException as e:
            logging.error(f"Error fetching data from GitHub API: {e}")
            break

    stats = []
    for release in releases:
        release_name = release['name']
        release_id = release['id']
        is_prerelease = release['prerelease']  # Check if the release is a pre-release

        for asset in release['assets']:
            asset_name = asset['name']

            # Skip text files
            if asset_name.endswith('.txt'):
                continue

            total_downloads = asset['download_count']

            # Extract OS, architecture, and type (jre/jdk) from the asset name
            os_arch_type = extract_os_arch_type(asset_name)
            os_name = os_arch_type.get('os')
            arch = os_arch_type.get('arch')
            java_type = os_arch_type.get('type')

            stats.append({
                'release_name': release_name,
                'release_id': release_id,
                'is_prerelease': is_prerelease,
                'asset_name': asset_name,
                'os_name': os_name,
                'architecture': arch,
                'java_type': java_type,
                'total_downloads': total_downloads
            })

    return stats


# Function to extract OS, architecture, and java type (jre/jdk) from asset name
def extract_os_arch_type(asset_name):
    patterns = {
        'alpine': r'(alpine|musl)',
        'linux': r'(linux|\.rpm$)',
        'macos': r'(macos|osx)',
        'windows': r'windows',
        'aix': r'aix',
        'aarch64': r'aarch64',
        'x64': r'(x64|x86_64)',
        'x86': r'\bx86\b',
        'ppc64le': r'ppc64le',
        'ppc64': r'ppc64'
    }

    os_name = None
    arch = None
    java_type = None

    asset_name_lower = asset_name.lower()

    # Extract JRE or JDK type
    if 'jre' in asset_name_lower:
        java_type = 'jre'
    elif 'jdk' in asset_name_lower:
        java_type = 'jdk'

    # Extract OS
    for key, pattern in patterns.items():
        if re.search(pattern, asset_name_lower):
            if key == 'alpine':
                os_name = 'alpine'
                break
            elif key in ['linux', 'macos', 'windows', 'aix'] and os_name is None:
                os_name = key

    # Extract architecture
    for key, pattern in patterns.items():
        if re.search(pattern, asset_name_lower):
            if key in ['aarch64', 'x64', 'x86', 'ppc64le', 'ppc64']:
                arch = key

    return {'os': os_name, 'arch': arch, 'type': java_type}


# Function to get the next available file name with a consistent date
def get_next_filename(base_name="stats/release_stats", date_suffix=None):
    counter = 1
    if date_suffix is None:
        date_suffix = datetime.now().strftime('%Y-%m-%d')

    while True:
        file_name = f"{base_name}_{date_suffix}_{counter:03d}.csv"
        if not os.path.exists(file_name):
            return file_name
        counter += 1


# Function to archive the previous release_stats.csv file
def archive_previous_stats(file_name="stats/release_stats.csv"):
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            if 'timestamp' in df.columns and not df.empty:
                content_timestamp = pd.to_datetime(df['timestamp'].iloc[0]).strftime('%Y-%m-%d')
            else:
                content_timestamp = datetime.fromtimestamp(os.path.getctime(file_name)).strftime('%Y-%m-%d')
        except Exception as e:
            logging.error(f"Error reading timestamp from {file_name}: {e}")
            content_timestamp = datetime.fromtimestamp(os.path.getctime(file_name)).strftime('%Y-%m-%d')

        new_file_name = get_next_filename(base_name="stats/release_stats", date_suffix=content_timestamp)
        shutil.move(file_name, new_file_name)
        logging.info(f"Archived previous stats to {new_file_name}")
    else:
        logging.info(f"No previous stats file found at {file_name} to archive.")


# Function to write the new stats to a CSV file (always named release_stats.csv)
def write_stats_to_csv(stats, file_name="stats/release_stats.csv"):
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    data = []

    for stat in stats:
        data.append({
            'timestamp': timestamp,
            'release_name': stat['release_name'],
            'release_id': stat['release_id'],
            'is_prerelease': stat['is_prerelease'],
            'asset_name': stat['asset_name'],
            'os_name': stat['os_name'],
            'architecture': stat['architecture'],
            'java_type': stat['java_type'],
            'total_downloads': stat['total_downloads']
        })

    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    df.to_csv(file_name, index=False)
    logging.info(f"New stats written to {file_name}")


# Main execution
if __name__ == "__main__":
    archive_previous_stats()
    stats = fetch_release_stats()
    write_stats_to_csv(stats)
