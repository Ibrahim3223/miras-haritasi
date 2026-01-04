#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Custom Search Image Finder with Verification
Searches Google for Turkish heritage site images with confidence scoring
"""

import json
import os
import re
import time
from pathlib import Path
from tqdm import tqdm
import requests
from urllib.parse import quote, urlparse

# Paths
CONTENT_DIR = Path("content/eserler")
PROGRESS_FILE = Path("scripts/google_search_progress.json")
REVIEW_QUEUE_FILE = Path("scripts/needs_review.json")

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_CX = os.getenv('GOOGLE_CX', '')  # Custom Search Engine ID

# Trusted sources (higher confidence)
TRUSTED_DOMAINS = [
    'gov.tr',
    'muze.gov.tr',
    'kulturportali.gov.tr',
    'ktb.gov.tr',
    'wikipedia.org',
    'wikimedia.org',
    'commons.wikimedia.org',
    'kulturvarliklari.gov.tr',
    'turkiyekulturportali.gov.tr',
]

# Semi-trusted sources (medium confidence)
SEMI_TRUSTED_DOMAINS = [
    'arkeolojikhaber.com',
    'kulturenvanteri.com',
    'tarihnotlari.com',
    'gezimanya.com',
    'kulturturizm.gov.tr',
]

# User-Agent
HEADERS = {
    'User-Agent': 'MirasHaritasi/1.0 (Turkish Heritage Map; educational project)'
}

def load_progress():
    """Load progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "processed": [],
        "found": {},
        "not_found": [],
        "needs_review": []
    }

def save_progress(progress):
    """Save progress"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def load_review_queue():
    """Load review queue"""
    if REVIEW_QUEUE_FILE.exists():
        with open(REVIEW_QUEUE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_review_queue(queue):
    """Save review queue"""
    with open(REVIEW_QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

def calculate_confidence(result, search_query):
    """
    Calculate confidence score for an image result
    Returns: (score, reasons)
    Score: 0-100
    STRICT MODE: Only trusted sources get high scores
    """
    score = 0  # Start from 0 (strict mode)
    reasons = []

    # Extract domain from URL
    try:
        domain = urlparse(result.get('link', '')).netloc.lower()
    except:
        domain = ''

    # Check trusted domains (MUST have this for high score)
    is_trusted = False
    for trusted in TRUSTED_DOMAINS:
        if trusted in domain:
            score = 70  # Start with high base for trusted sources
            reasons.append(f"Trusted source: {domain}")
            is_trusted = True
            break

    if not is_trusted:
        # Check semi-trusted domains
        for semi in SEMI_TRUSTED_DOMAINS:
            if semi in domain:
                score = 55  # Medium base for semi-trusted
                reasons.append(f"Semi-trusted source: {domain}")
                break
        else:
            # Untrusted source - very low base score
            score = 30
            reasons.append(f"WARNING: Untrusted source: {domain}")

    # Check if title/snippet contains search terms
    title = result.get('title', '').lower()
    snippet = result.get('snippet', '').lower()

    search_terms = search_query.lower().split()
    matched_terms = sum(1 for term in search_terms if len(term) > 3 and (term in title or term in snippet))

    if matched_terms >= len(search_terms) * 0.7:  # 70% of terms matched
        score += 20
        reasons.append(f"Excellent match ({matched_terms}/{len(search_terms)} terms)")
    elif matched_terms >= len(search_terms) * 0.5:  # 50% of terms matched
        score += 10
        reasons.append(f"Good match ({matched_terms}/{len(search_terms)} terms)")
    else:
        score -= 5
        reasons.append(f"Poor match ({matched_terms}/{len(search_terms)} terms)")

    # Check image metadata
    if 'image' in result:
        img_context = result['image'].get('contextLink', '').lower()
        if any(trusted in img_context for trusted in TRUSTED_DOMAINS):
            score += 10
            reasons.append("Image from trusted context page")

    # STRICT: Require Turkish content indicators
    turkish_indicators = ['türkiye', 'turkey', 'anadolu', 'anatolia', 'türk', 'turkish']
    has_turkish = any(ind in title.lower() or ind in snippet.lower() for ind in turkish_indicators)

    if has_turkish:
        score += 5
        reasons.append("Turkish context confirmed")
    else:
        # Heavy penalty for no Turkish context
        score -= 20
        reasons.append("CRITICAL: No Turkish context indicators")

    # Extra validation: penalize social media heavily
    social_media = ['instagram', 'facebook', 'twitter', 'tiktok', 'pinterest']
    if any(sm in domain for sm in social_media):
        score -= 30
        reasons.append("PENALTY: Social media source (unreliable)")

    return min(100, max(0, score)), reasons

def search_google_images(query, num_results=5):
    """Search Google Custom Search for images"""
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return None

    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CX,
            'q': query,
            'searchType': 'image',
            'num': num_results,
            'imgSize': 'large',
            'imgType': 'photo',
            'safe': 'off',
            'lr': 'lang_tr|lang_en',  # Turkish or English
        }

        response = requests.get(url, params=params, headers=HEADERS, timeout=15)

        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        elif response.status_code == 429:
            print("\n[!] API rate limit reached. Wait and try again.")
            return None
        else:
            print(f"\n[!] API error: {response.status_code}")
            return None

    except Exception as e:
        print(f"\n[!] Error: {e}")
        return None

def find_best_image(title, province=None, type_name=None):
    """
    Find the best image for a heritage site
    Returns: (image_url, confidence_score, metadata) or None
    """
    # Build search queries (try multiple variations)
    queries = [
        f"{title} {province}" if province else title,
        f"{title} Turkey",
        f"{title} Türkiye",
        f"{title} {type_name}" if type_name else None,
    ]

    best_result = None
    best_score = 0

    for query in queries:
        if not query:
            continue

        results = search_google_images(query, num_results=3)

        if not results:
            continue

        # Evaluate each result
        for result in results:
            score, reasons = calculate_confidence(result, query)

            if score > best_score:
                best_score = score
                best_result = {
                    'url': result.get('link'),
                    'source_url': result.get('image', {}).get('contextLink', ''),
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'confidence': score,
                    'reasons': reasons,
                    'query': query,
                    'domain': urlparse(result.get('link', '')).netloc
                }

        # Rate limiting
        time.sleep(0.5)

    return best_result

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

    pattern = r'^featured_image:\s*"[^"]*"$'
    replacement = f'featured_image: "{image_url}"'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    print("=" * 70)
    print("Google Custom Search - Image Finder with Verification")
    print("=" * 70)

    # Check API configuration
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        print("\n[!] ERROR: Google API credentials not configured!")
        print("\nYou need:")
        print("1. Google API Key: https://console.cloud.google.com/")
        print("2. Custom Search Engine ID: https://programmablesearchengine.google.com/")
        print("\nSet them as environment variables:")
        print("  set GOOGLE_API_KEY=your_api_key")
        print("  set GOOGLE_CX=your_search_engine_id")
        return

    print("\n[OK] API credentials configured")
    print("[!] Daily limit: 100 searches")

    # Load progress
    progress = load_progress()
    review_queue = load_review_queue()

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
    print(f"\n[!] Recommended: 50-100 files per day (API limit)")
    batch_size = int(input(f"How many files to process? (max 100): ") or "50")
    batch_size = min(100, min(batch_size, len(to_process)))

    # Confidence threshold
    print(f"\n[!] Confidence threshold for auto-approval:")
    print("   - High (80+): Very confident, auto-approve")
    print("   - Medium (60-79): Somewhat confident, needs review")
    print("   - Low (<60): Not confident, needs review")
    confidence_threshold = int(input("Auto-approve threshold (recommended: 75): ") or "75")

    # Process files
    print(f"\n2. Searching Google Images (batch: {batch_size})...")
    found_count = 0
    auto_approved = 0
    needs_review_count = 0

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
            result = find_best_image(title, province, type_name)

            if result:
                found_count += 1

                # Check confidence
                if result['confidence'] >= confidence_threshold:
                    # Auto-approve
                    update_markdown_image(md_file, result['url'])
                    progress['found'][md_file.name] = result
                    auto_approved += 1
                else:
                    # Needs review
                    review_item = {
                        'file': md_file.name,
                        'title': title,
                        'province': province,
                        'type': type_name,
                        'result': result
                    }
                    review_queue.append(review_item)
                    progress['needs_review'].append(md_file.name)
                    needs_review_count += 1
            else:
                progress['not_found'].append(md_file.name)

            progress['processed'].append(md_file.name)

            # Save progress every 10 items
            if len(progress['processed']) % 10 == 0:
                save_progress(progress)
                save_review_queue(review_queue)

            # Rate limiting (Google has daily limits)
            time.sleep(1)

        except Exception as e:
            print(f"\n[!] Error processing {md_file.name}: {e}")
            progress['processed'].append(md_file.name)

    # Final save
    save_progress(progress)
    save_review_queue(review_queue)

    print("\n" + "=" * 70)
    print("RESULTS:")
    print(f"  Processed: {batch_size}")
    print(f"  Images found: {found_count} ({found_count/batch_size*100:.1f}%)")
    print(f"  Auto-approved (>={confidence_threshold}%): {auto_approved}")
    print(f"  Needs review (<{confidence_threshold}%): {needs_review_count}")
    print(f"  Not found: {batch_size - found_count}")
    print(f"\n  Total progress:")
    print(f"    Processed: {len(progress['processed'])}")
    print(f"    Found: {len(progress['found'])}")
    print(f"    Needs review: {len(review_queue)}")
    print(f"    Remaining: {len(to_process) - batch_size}")
    print("=" * 70)

    if needs_review_count > 0:
        print(f"\n[!] {needs_review_count} images need manual review")
        print(f"    Review file: scripts/needs_review.json")
        print("    Use the review script to approve/reject images")

    print("\n[TIP] Run again tomorrow to process more (100/day limit)")

if __name__ == "__main__":
    main()
