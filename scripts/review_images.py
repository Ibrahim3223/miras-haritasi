#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Review Tool
Manually review and approve/reject images found by Google Custom Search
"""

import json
import re
import webbrowser
from pathlib import Path

# Paths
CONTENT_DIR = Path("content/eserler")
REVIEW_QUEUE_FILE = Path("scripts/needs_review.json")
PROGRESS_FILE = Path("scripts/google_search_progress.json")

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

def load_progress():
    """Load progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": [], "found": {}, "not_found": [], "needs_review": []}

def save_progress(progress):
    """Save progress"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def update_markdown_image(file_path, image_url):
    """Update featured_image in markdown"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'^featured_image:\s*"[^"]*"$'
    replacement = f'featured_image: "{image_url}"'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def display_review_item(item, index, total):
    """Display a review item with all details"""
    print("\n" + "=" * 70)
    print(f"Review Item {index + 1} of {total}")
    print("=" * 70)

    print(f"\n[*] Heritage Site:")
    print(f"   Title: {item['title']}")
    print(f"   Province: {item.get('province', 'N/A')}")
    print(f"   Type: {item.get('type', 'N/A')}")

    result = item['result']
    print(f"\n[IMAGE] Proposed Image:")
    print(f"   URL: {result['url']}")
    print(f"   Source: {result['source_url']}")
    print(f"   Domain: {result['domain']}")
    print(f"   Image Title: {result['title']}")

    print(f"\n[SCORE] Confidence Analysis:")
    print(f"   Score: {result['confidence']}/100")
    print(f"   Search Query: {result['query']}")
    print(f"\n   Reasons:")
    for reason in result['reasons']:
        print(f"     - {reason}")

    print(f"\n[INFO] Context:")
    print(f"   {result['snippet'][:200]}...")

def main():
    print("=" * 70)
    print("Image Review Tool")
    print("=" * 70)

    # Load data
    review_queue = load_review_queue()
    progress = load_progress()

    if not review_queue:
        print("\n[OK] No images need review! Queue is empty.")
        return

    print(f"\n[*] Review Queue: {len(review_queue)} items")
    print("\nCommands:")
    print("  [a] Approve - Add image to site")
    print("  [r] Reject - Don't use this image")
    print("  [s] Skip - Review later")
    print("  [o] Open URLs - Open image and source in browser")
    print("  [q] Quit - Save and exit")

    approved_count = 0
    rejected_count = 0
    skipped_items = []

    for index, item in enumerate(review_queue):
        display_review_item(item, index, len(review_queue))

        while True:
            choice = input("\n>> Your decision [a/r/s/o/q]: ").lower().strip()

            if choice == 'a':
                # Approve
                file_path = CONTENT_DIR / item['file']
                update_markdown_image(file_path, item['result']['url'])

                # Update progress
                progress['found'][item['file']] = item['result']
                if item['file'] in progress['needs_review']:
                    progress['needs_review'].remove(item['file'])

                approved_count += 1
                print("[OK] Approved and applied!")
                break

            elif choice == 'r':
                # Reject
                if item['file'] in progress['needs_review']:
                    progress['needs_review'].remove(item['file'])
                progress['not_found'].append(item['file'])

                rejected_count += 1
                print("[X] Rejected!")
                break

            elif choice == 's':
                # Skip for later
                skipped_items.append(item)
                print("[SKIP] Skipped for later review")
                break

            elif choice == 'o':
                # Open URLs in browser
                print("[OPEN] Opening URLs in browser...")
                try:
                    webbrowser.open(item['result']['url'])
                    webbrowser.open(item['result']['source_url'])
                    print("[OK] Opened! Check your browser.")
                except Exception as e:
                    print(f"[ERROR] Error opening browser: {e}")
                    print(f"   Image URL: {item['result']['url']}")
                    print(f"   Source URL: {item['result']['source_url']}")

            elif choice == 'q':
                # Quit
                print("\n[SAVE] Saving and exiting...")
                # Add current item to skipped if not processed
                skipped_items.append(item)
                # Add remaining items to skipped
                skipped_items.extend(review_queue[index + 1:])
                save_review_queue(skipped_items)
                save_progress(progress)
                print(f"\n[OK] Saved! {len(skipped_items)} items still in queue.")
                return

            else:
                print("[ERROR] Invalid choice. Please enter a, r, s, o, or q.")

    # Save final results
    save_review_queue(skipped_items)
    save_progress(progress)

    print("\n" + "=" * 70)
    print("REVIEW COMPLETE!")
    print("=" * 70)
    print(f"\n  [OK] Approved: {approved_count}")
    print(f"  [X] Rejected: {rejected_count}")
    print(f"  [SKIP] Skipped: {len(skipped_items)}")
    print(f"\n  [*] Remaining in queue: {len(skipped_items)}")

    if skipped_items:
        print(f"\n[TIP] Run this script again to review remaining {len(skipped_items)} items")
    else:
        print("\n[SUCCESS] All items reviewed!")

if __name__ == "__main__":
    main()
