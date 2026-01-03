#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikimedia Commons Image Search
Fast image search using Wikimedia Commons API
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
PROGRESS_FILE = Path("scripts/wikimedia_search_progress.json")

# Wikimedia Commons API
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# User-Agent header (required by Wikimedia)
HEADERS = {
    'User-Agent': 'MirasHaritasi/1.0 (Turkish Heritage Map; educational project)'
}

def load_progress():
    """Load progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": [], "found": {}, "not_found": []}

def save_progress(progress):
    """Save progress"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def search_commons_image(title, province=None):
    """Search Wikimedia Commons for image"""
    # Try exact title first
    search_terms = [
        title,
        f"{title} {province}" if province else None,
        f"{title} Turkey",
        # Remove common suffixes for better matching
        re.sub(r'\s+(Camii|Cami|Mosque|Kilise|Church|Müze|Museum)$', '', title, flags=re.IGNORECASE)
    ]

    for term in search_terms:
        if not term:
            continue

        try:
            # Search for files
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': f'"{term}"',
                'srnamespace': '6',  # File namespace
                'srlimit': '3',
                'format': 'json'
            }

            response = requests.get(COMMONS_API, params=params, headers=HEADERS, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = data.get('query', {}).get('search', [])

                for result in results:
                    file_title = result['title']

                    # Get image URL
                    img_params = {
                        'action': 'query',
                        'titles': file_title,
                        'prop': 'imageinfo',
                        'iiprop': 'url',
                        'format': 'json'
                    }

                    img_response = requests.get(COMMONS_API, params=img_params, headers=HEADERS, timeout=10)

                    if img_response.status_code == 200:
                        img_data = img_response.json()
                        pages = img_data.get('query', {}).get('pages', {})

                        for page in pages.values():
                            imageinfo = page.get('imageinfo', [])
                            if imageinfo:
                                image_url = imageinfo[0].get('url', '')
                                if image_url:
                                    return image_url

        except Exception as e:
            print(f"\nError searching Commons for '{term}': {e}")
            continue

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
                fm[key.strip()] = value.strip().strip('"')
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
    print("Wikimedia Commons Image Search")
    print("=" * 70)

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
    print(f"\n[!] Note: This will make HTTP requests to Wikimedia Commons")
    batch_size = int(input(f"How many files to process? (recommended: 50-200): ") or "100")
    batch_size = min(batch_size, len(to_process))

    # Process files
    print(f"\n2. Searching Wikimedia Commons (batch: {batch_size})...")
    found_count = 0

    for md_file in tqdm(to_process[:batch_size], desc="Searching"):
        try:
            # Read front matter
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm = parse_markdown_frontmatter(content)
            title = fm.get('title', '')
            province = fm.get('province', '')

            # Search for image
            image_url = search_commons_image(title, province)

            # Update if found
            if image_url:
                update_markdown_image(md_file, image_url)
                progress['found'][md_file.name] = image_url
                found_count += 1
            else:
                progress['not_found'].append(md_file.name)

            progress['processed'].append(md_file.name)

            # Rate limiting (be nice to Wikimedia)
            time.sleep(0.5)  # 2 requests/second

            # Save progress every 10 items
            if len(progress['processed']) % 10 == 0:
                save_progress(progress)

        except Exception as e:
            print(f"\nError processing {md_file.name}: {e}")
            progress['processed'].append(md_file.name)

    # Final save
    save_progress(progress)

    print("\n" + "=" * 70)
    print("RESULTS:")
    print(f"  Processed: {batch_size}")
    print(f"  Images found: {found_count} ({found_count/batch_size*100:.1f}%)")
    print(f"  Not found: {batch_size - found_count}")
    print(f"\n  Total progress:")
    print(f"    Processed: {len(progress['processed'])}")
    print(f"    Found: {len(progress['found'])}")
    print(f"    Remaining: {len(to_process) - batch_size}")
    print("=" * 70)
    print("\n[TIP] Run again to process more files (progress is saved)")
    print("[TIP] Expected success rate: 15-30% for Turkish heritage items")

if __name__ == "__main__":
    main()
