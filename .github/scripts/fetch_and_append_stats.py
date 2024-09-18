import os
import re
import requests
import pandas as pd
from datetime import datetime
import uuid
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
        'linux': r'linux',
        'macos': r'(macos|osx)',  # Handles both macos and osx, normalized to 'macos'
        'windows': r'windows',
        'alpine': r'alpine',
        'aix': r'aix',  # Add pattern for AIX
        'aarch64': r'aarch64',
        'x64': r'x64',
        'x86': r'x86',
        'ppc64le': r'ppc64le',
        'musl': r'musl'
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
    
    # Extract OS and architecture
    for key, pattern in patterns.items():
        if re.search(pattern, asset_name_lower):
            if key in ['linux', 'macos', 'windows', 'alpine', 'aix']:  # Handle AIX
                os_name = 'macos' if key == 'macos' else key
            elif key in ['aarch64', 'x64', 'x86', 'ppc64le']:
                arch = key
    
    return {'os': os_name, 'arch': arch, 'type': java_type}

# Function to get the next available file name with a three-digit counter
def get_next_filename(base_name="stats/release_stats"):
    counter = 1
    while True:
        file_name = f"{base_name}_{datetime.now().strftime('%Y-%m-%d')}_{counter:03d}.csv"
        if not os.path.exists(file_name):
            return file_name
        counter += 1

# Function to archive the previous release_stats.csv file
def archive_previous_stats(file_name="stats/release_stats.csv"):
    # Check if the release_stats.csv exists
    if os.path.exists(file_name):
        # Generate a base name with date
        date_suffix = datetime.now().strftime('%Y-%m-%d')
        # Find the next available counter for today's file
        new_file_name = get_next_filename(base_name=f"stats/release_stats_{date_suffix}")
        # Rename the old stats file
        shutil.move(file_name, new_file_name)
        logging.info(f"Archived previous stats to {new_file_name}")
    else:
        logging.info(f"No previous stats file found at {file_name} to archive.")

# Function to write the new stats to a CSV file (always named release_stats.csv)
def write_stats_to_csv(stats, file_name="stats/release_stats.csv"):
    unique_id = str(uuid.uuid4())  # Generate a unique ID for the entire run
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')  # Format timestamp as yyyy-mm-dd HH:MM:SS
    data = []
    
    for stat in stats:
        data.append({
            'id': unique_id,  # Use the same unique ID for all rows in this run
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
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    
    # Write the new data to the CSV file (overwriting if it exists)
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
