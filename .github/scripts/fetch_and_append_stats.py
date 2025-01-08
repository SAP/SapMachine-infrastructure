import os
import re
import requests
import pandas as pd
from datetime import datetime
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to fetch download stats for all releases
def fetch_release_stats():
    releases = []
    url = "https://api.github.com/repos/SAP/SapMachine/releases"
    
    while url:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            releases.extend(data)
            # Get the URL for the next page, if it exists
            url = response.links.get('next', {}).get('url')
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
    
    # Convert asset name to lowercase to ensure case-insensitive matching
    asset_name_lower = asset_name.lower()

    # Extract the JRE or JDK type
    if 'jre' in asset_name_lower:
        java_type = 'jre'
    elif 'jdk' in asset_name_lower:
        java_type = 'jdk'

    for key, pattern in patterns.items():
        if re.search(pattern, asset_name_lower):
            if key == 'alpine':  # Prioritize assigning 'alpine' for alpine/musl
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
        date_suffix = datetime.now().strftime('%Y-%m-%d')  # Default to current date

    while True:
        file_name = f"{base_name}_{date_suffix}_{counter:03d}.csv"
        if not os.path.exists(file_name):
            return file_name
        counter += 1

# Function to archive the previous release_stats.csv file
def archive_previous_stats(file_name="stats/release_stats.csv"):
    if os.path.exists(file_name):
        try:
            # Read the first timestamp from the existing file
            df = pd.read_csv(file_name)
            if 'timestamp' in df.columns and not df.empty:
                # Extract the date part of the first timestamp
                content_timestamp = pd.to_datetime(df['timestamp'].iloc[0]).strftime('%Y-%m-%d')
            else:
                # Fallback to the file's creation time if no timestamp column exists
                content_timestamp = datetime.fromtimestamp(os.path.getctime(file_name)).strftime('%Y-%m-%d')
        except Exception as e:
            logging.error(f"Error reading timestamp from {file_name}: {e}")
            content_timestamp = datetime.fromtimestamp(os.path.getctime(file_name)).strftime('%Y-%m-%d')

        # Generate a base name with the extracted date
        new_file_name = get_next_filename(base_name="stats/release_stats", date_suffix=content_timestamp)

        # Rename the old stats file
        shutil.move(file_name, new_file_name)
        logging.info(f"Archived previous stats to {new_file_name}")
    else:
        logging.info(f"No previous stats file found at {file_name} to archive.")

# Function to write the new stats to a CSV file (always named release_stats.csv)
def write_stats_to_csv(stats, file_name="stats/release_stats.csv"):
    timestamp = datetime.utcnow().isoformat(timespec='seconds')
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
    # Archive the previous release_stats.csv (if it exists)
    archive_previous_stats()

    # Fetch new stats from the GitHub API
    stats = fetch_release_stats()

    # Write the new stats to the release_stats.csv file
    write_stats_to_csv(stats)
