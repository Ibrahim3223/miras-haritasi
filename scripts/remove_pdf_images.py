#!/usr/bin/env python3
"""Remove PDF file links from featured_image fields in content files."""

import os
import re

def remove_pdf_images():
    """Remove PDF images from all content files."""
    content_dir = "content/eserler"
    count = 0

    for filename in os.listdir(content_dir):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(content_dir, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if this file has a PDF image
        if 'featured_image:' in content and '.pdf' in content:
            # Replace PDF URLs with empty string
            pattern = r'featured_image:\s*"https://[^"]*\.pdf[^"]*"'
            replacement = 'featured_image: ""'

            new_content = re.sub(pattern, replacement, content)

            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f"[FIXED] {filename}")

    print(f"\n[DONE] Removed PDF images from {count} files")

if __name__ == '__main__':
    remove_pdf_images()
