#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Images from eserler.json to Markdown Files
Copies image_url from eserler.json to featured_image in markdown front matter
"""

import json
import os
import re
from pathlib import Path
from tqdm import tqdm

# Paths
CONTENT_DIR = Path("content/eserler")
JSON_FILE = Path("data/eserler.json")

def load_eserler_json():
    """Load eserler.json"""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_slug_from_title(title):
    """Convert title to slug"""
    import unicodedata
    # Remove Turkish characters
    title = title.replace('ı', 'i').replace('İ', 'I')
    title = title.replace('ş', 's').replace('Ş', 'S')
    title = title.replace('ğ', 'g').replace('Ğ', 'G')
    title = title.replace('ü', 'u').replace('Ü', 'U')
    title = title.replace('ö', 'o').replace('Ö', 'O')
    title = title.replace('ç', 'c').replace('Ç', 'C')

    # Normalize and slugify
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = re.sub(r'[^\w\s-]', '', title.lower())
    return re.sub(r'[-\s]+', '-', title).strip('-')

def update_markdown_image(file_path, image_url):
    """Update featured_image in markdown front matter"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace featured_image line (match any value, not just empty)
    pattern = r'^featured_image:\s*"[^"]*"$'
    replacement = f'featured_image: "{image_url}"'

    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    print("=" * 60)
    print("Sync Images from eserler.json to Markdown Files")
    print("=" * 60)

    # Load eserler.json
    print("\n1. Loading eserler.json...")
    eserler = load_eserler_json()
    print(f"   Loaded {len(eserler)} items")

    # Filter items with images
    with_images = [item for item in eserler if item.get('image_url')]
    print(f"   Items with images: {len(with_images)} ({len(with_images)/len(eserler)*100:.1f}%)")

    # Create slug to image mapping
    print("\n2. Creating slug to image mapping...")
    slug_to_image = {}
    for item in with_images:
        slug = get_slug_from_title(item['title'])
        slug_to_image[slug] = item['image_url']

    # Get all markdown files
    print("\n3. Scanning markdown files...")
    md_files = list(CONTENT_DIR.glob("*.md"))
    print(f"   Found {len(md_files)} markdown files")

    # Update files
    print("\n4. Updating images...")
    updated = 0
    skipped = 0
    already_has_image = 0

    for md_file in tqdm(md_files, desc="Processing"):
        slug = md_file.stem

        if slug in slug_to_image:
            # Check current image status
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Only update if currently empty
            if 'featured_image: ""' in content:
                # Update with image from JSON
                update_markdown_image(md_file, slug_to_image[slug])
                updated += 1
            else:
                # Already has an image
                already_has_image += 1
        else:
            skipped += 1

    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Total files: {len(md_files)}")
    print(f"  Images updated: {updated}")
    print(f"  Already had images: {already_has_image}")
    print(f"  No match in JSON: {skipped}")
    print(f"\n  Image coverage:")
    print(f"    With images: {updated + already_has_image} ({(updated + already_has_image)/len(md_files)*100:.1f}%)")
    print(f"    Without images: {len(md_files) - updated - already_has_image} ({(len(md_files) - updated - already_has_image)/len(md_files)*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
