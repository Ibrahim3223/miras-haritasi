#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Source Image Search
Searches multiple free image APIs for Turkish heritage sites
"""

import json
import os
import re
import time
from pathlib import Path
from tqdm import tqdm
import requests
from urllib.parse import quote

# Paths
CONTENT_DIR = Path("content/eserler")
PROGRESS_FILE = Path("scripts/multi_source_progress.json")

# API Configuration (add your API keys here)
API_KEYS = {
    'unsplash': os.getenv('UNSPLASH_API_KEY', ''),  # Get free key from https://unsplash.com/developers
    'pexels': os.getenv('PEXELS_API_KEY', ''),      # Get free key from https://www.pexels.com/api/
    'pixabay': os.getenv('PIXABAY_API_KEY', ''),    # Get free key from https://pixabay.com/api/docs/
}

# User-Agent for requests
HEADERS = {
    'User-Agent': 'MirasHaritasi/1.0 (Turkish Heritage Map; educational project)'
}

def load_progress():
    """Load progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": [], "found": {}, "not_found": [], "source_stats": {}}

def save_progress(progress):
    """Save progress"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def search_unsplash(query):
    """Search Unsplash for images"""
    if not API_KEYS['unsplash']:
        return None

    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            'query': query,
            'per_page': 3,
            'orientation': 'landscape'
        }
        headers = {
            **HEADERS,
            'Authorization': f"Client-ID {API_KEYS['unsplash']}"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                # Return the regular size image URL
                return results[0]['urls']['regular'], 'unsplash'
    except Exception as e:
        pass

    return None

def search_pexels(query):
    """Search Pexels for images"""
    if not API_KEYS['pexels']:
        return None

    try:
        url = "https://api.pexels.com/v1/search"
        params = {
            'query': query,
            'per_page': 3,
            'orientation': 'landscape'
        }
        headers = {
            **HEADERS,
            'Authorization': API_KEYS['pexels']
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            photos = data.get('photos', [])
            if photos:
                # Return the large size image URL
                return photos[0]['src']['large'], 'pexels'
    except Exception as e:
        pass

    return None

def search_pixabay(query):
    """Search Pixabay for images"""
    if not API_KEYS['pixabay']:
        return None

    try:
        url = "https://pixabay.com/api/"
        params = {
            'key': API_KEYS['pixabay'],
            'q': query,
            'image_type': 'photo',
            'orientation': 'horizontal',
            'per_page': 3
        }

        response = requests.get(url, params=params, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', [])
            if hits:
                # Return the large image URL
                return hits[0]['largeImageURL'], 'pixabay'
    except Exception as e:
        pass

    return None

def search_all_sources(title, province=None, type_name=None):
    """Search all available sources for an image"""
    # Build search queries
    queries = [
        title,
        f"{title} {province}" if province else None,
        f"{title} Turkey",
        f"{title} Türkiye",
        f"{type_name} {province} Turkey" if type_name and province else None,
    ]

    # Try each source
    sources = [
        ('Unsplash', search_unsplash),
        ('Pexels', search_pexels),
        ('Pixabay', search_pixabay),
    ]

    for query in queries:
        if not query:
            continue

        for source_name, search_func in sources:
            result = search_func(query)
            if result:
                return result

            # Rate limiting
            time.sleep(0.3)

    return None

def parse_markdown_frontmatter(content):
    """Parse markdown front matter"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if match:
        fm_text = match.group(1)
        fm = {}
        for line in fm_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                fm[key.strip()] = value.strip().strip('"').strip("'")
        return fm
    return {}

def update_markdown_image(file_path, image_url):
    """Update featured_image in markdown"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update featured_image
    pattern = r'^featured_image:\s*"[^"]*"$'
    replacement = f'featured_image: "{image_url}"'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    print("=" * 70)
    print("Multi-Source Image Search")
    print("=" * 70)

    # Check API keys
    active_sources = []
    if API_KEYS['unsplash']:
        active_sources.append('Unsplash')
    if API_KEYS['pexels']:
        active_sources.append('Pexels')
    if API_KEYS['pixabay']:
        active_sources.append('Pixabay')

    if not active_sources:
        print("\n[!] WARNING: No API keys configured!")
        print("\nTo use this script, you need to set API keys:")
        print("1. Unsplash: https://unsplash.com/developers")
        print("2. Pexels: https://www.pexels.com/api/")
        print("3. Pixabay: https://pixabay.com/api/docs/")
        print("\nSet them as environment variables or edit the script.")
        return

    print(f"\nActive sources: {', '.join(active_sources)}")

    # Load progress
    progress = load_progress()

    # Get markdown files without images
    print("\n1. Scanning markdown files...")
    md_files = list(CONTENT_DIR.glob("*.md"))

    files_without_images = []
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'featured_image: ""' in content:
                files_without_images.append(md_file)

    print(f"   Total files: {len(md_files)}")
    print(f"   Files without images: {len(files_without_images)}")
    print(f"   Previously processed: {len(progress['processed'])}")

    # Filter out already processed
    to_process = [f for f in files_without_images if f.name not in progress['processed']]
    print(f"   To process: {len(to_process)}")

    if not to_process:
        print("\n[OK] All files have been processed!")
        return

    # Ask for batch size
    print(f"\n[!] Note: This will make HTTP requests to: {', '.join(active_sources)}")
    batch_size = int(input(f"How many files to process? (recommended: 50-100): ") or "50")
    batch_size = min(batch_size, len(to_process))

    # Process files
    print(f"\n2. Searching images (batch: {batch_size})...")
    found_count = 0
    source_stats = progress.get('source_stats', {})

    for md_file in tqdm(to_process[:batch_size], desc="Searching"):
        try:
            # Read front matter
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm = parse_markdown_frontmatter(content)
            title = fm.get('title', '')
            province = fm.get('il', '')
            type_name = fm.get('type', '')

            # Search for image
            result = search_all_sources(title, province, type_name)

            # Update if found
            if result:
                image_url, source = result
                update_markdown_image(md_file, image_url)
                progress['found'][md_file.name] = {
                    'url': image_url,
                    'source': source
                }
                source_stats[source] = source_stats.get(source, 0) + 1
                found_count += 1
            else:
                progress['not_found'].append(md_file.name)

            progress['processed'].append(md_file.name)

            # Rate limiting (be nice to APIs)
            time.sleep(1)

            # Save progress every 10 items
            if len(progress['processed']) % 10 == 0:
                progress['source_stats'] = source_stats
                save_progress(progress)

        except Exception as e:
            print(f"\nError processing {md_file.name}: {e}")
            progress['processed'].append(md_file.name)

    # Final save
    progress['source_stats'] = source_stats
    save_progress(progress)

    print("\n" + "=" * 70)
    print("RESULTS:")
    print(f"  Processed: {batch_size}")
    print(f"  Images found: {found_count} ({found_count/batch_size*100:.1f}%)")
    print(f"  Not found: {batch_size - found_count}")
    print(f"\n  Source breakdown:")
    for source, count in source_stats.items():
        print(f"    {source}: {count}")
    print(f"\n  Total progress:")
    print(f"    Processed: {len(progress['processed'])}")
    print(f"    Found: {len(progress['found'])}")
    print(f"    Remaining: {len(to_process) - batch_size}")
    print("=" * 70)
    print("\n[TIP] Run again to process more files (progress is saved)")

if __name__ == "__main__":
    main()
