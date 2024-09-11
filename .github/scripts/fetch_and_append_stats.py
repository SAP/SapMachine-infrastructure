import requests
import pandas as pd
from datetime import datetime
import uuid
import re
import os

# Set the maximum file size limit (in bytes) for the CSV
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Function to fetch download stats for all releases
def fetch_release_stats():
    releases = []
    url = "https://api.github.com/repos/SAP/SapMachine/releases"
    
    while url:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        releases.extend(data)
        # Get the URL for the next page, if it exists
        url = response.links.get('next', {}).get('url')
    
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
            
            # Extract OS, architecture, and type (jre/jdk) from the asset name using regex
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
        'aarch64': r'aarch64',
        'x64': r'x64',
        'x86': r'x86',
        'ppc64le': r'ppc64le',
        'musl': r'musl'
    }
    
    os_name = None
    arch = None
    java_type = None
    
    # Extract the JRE or JDK type
    if 'jre' in asset_name.lower():
        java_type = 'jre'
    elif 'jdk' in asset_name.lower():
        java_type = 'jdk'
    
    # Extract OS and architecture
    for key, pattern in patterns.items():
        if re.search(pattern, asset_name, re.IGNORECASE):
            if key in ['linux', 'macos', 'windows', 'alpine']:
     
