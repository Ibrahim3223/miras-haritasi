#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikidata Image Fetcher - URL Based
Fetches images from Wikidata/Wikimedia Commons for heritage items
Uses SPARQL queries and updates markdown files directly with URLs
"""

import json
import os
import re
import time
from pathlib import Path
from tqdm import tqdm
import requests

# Paths
CONTENT_DIR = Path("content/eserler")
JSON_FILE = Path("data/eserler.json")
PROGRESS_FILE = Path("scripts/image_fetch_progress.json")

# Wikidata endpoint
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

def load_progress():
    """Load fetch progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": [], "found": {}, "not_found": []}

def save_progress(progress):
    """Save fetch progress"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def query_wikidata_by_title(title, province=None):
    """Query Wikidata for image by title"""
    # Build SPARQL query
    query = f"""
    SELECT ?item ?itemLabel ?image WHERE {{
      ?item rdfs:label "{title}"@tr.
      ?item wdt:P18 ?image.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }}
    }}
    LIMIT 1
    """

    try:
        response = requests.get(
            WIKIDATA_SPARQL,
            params={'query': query, 'format': 'json'},
            headers={'User-Agent': 'MirasHaritasi/1.0'},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            bindings = data.get('results', {}).get('bindings', [])
            if bindings:
                image_url = bindings[0].get('image', {}).get('value', '')
                return image_url
    except Exception as e:
        print(f"Error querying Wikidata for '{title}': {e}")

    return None

def query_wikidata_by_coords(lat, lon, title_hint=None):
    """Query Wikidata for nearby heritage items with images"""
    # Search within ~100m radius
    radius = 0.001  # approximately 100m

    query = f"""
    SELECT ?item ?itemLabel ?image ?coord WHERE {{
      ?item wdt:P625 ?coord.
      ?item wdt:P18 ?image.

      FILTER(
        ?coord >= "Point({lon-radius} {lat-radius})"^^geo:wktLiteral &&
        ?coord <= "Point({lon+radius} {lat+radius})"^^geo:wktLiteral
      )

      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }}
    }}
    LIMIT 1
    """

    try:
        response = requests.get(
            WIKIDATA_SPARQL,
            params={'query': query, 'format': 'json'},
            headers={'User-Agent': 'MirasHaritasi/1.0'},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            bindings = data.get('results', {}).get('bindings', [])
            if bindings:
                image_url = bindings[0].get('image', {}).get('value', '')
                return image_url
    except Exception as e:
        print(f"Error querying Wikidata by coords ({lat}, {lon}): {e}")

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
    pattern = r'^featured_image:\s*".*"$'
    replacement = f'featured_image: "{image_url}"'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    print("=" * 70)
    print("Wikidata Image Fetcher - URL Based")
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
        print("\n✅ All files have been processed!")
        return

    # Ask for batch size
    print(f"\n⚠️  Rate limits: Wikidata allows ~60 req/min")
    batch_size = int(input(f"How many files to process? (max {len(to_process)}): ") or "100")
    batch_size = min(batch_size, len(to_process))

    # Process files
    print(f"\n2. Fetching images from Wikidata (batch: {batch_size})...")
    found_count = 0

    for md_file in tqdm(to_process[:batch_size], desc="Fetching"):
        try:
            # Read front matter
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm = parse_markdown_frontmatter(content)
            title = fm.get('title', '')
            coords = fm.get('coords', '')
            province = fm.get('province', '')

            # Try to find image
            image_url = None

            # Method 1: Query by title
            image_url = query_wikidata_by_title(title, province)

            # Method 2: If coords available, try nearby search
            if not image_url and coords:
                try:
                    lat, lon = map(float, coords.split(','))
                    image_url = query_wikidata_by_coords(lat, lon, title)
                except:
                    pass

            # Update if found
            if image_url:
                update_markdown_image(md_file, image_url)
                progress['found'][md_file.name] = image_url
                found_count += 1
            else:
                progress['not_found'].append(md_file.name)

            progress['processed'].append(md_file.name)

            # Rate limiting
            time.sleep(1.1)  # ~50 req/min to be safe

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
    print("\n💡 Tip: Run again to process more files (progress is saved)")

if __name__ == "__main__":
    main()
