#!/usr/bin/env python3
"""
Fix taxonomy format in all content files.
Converts: turler: '["Kale"]'
To: turler: ["Kale"]

And eventually Hugo will parse the array correctly.
"""

import os
import re
from pathlib import Path

def fix_taxonomy_line(line):
    """Fix a taxonomy line by removing the outer quotes."""
    # Match patterns like: turler: '["Kale"]' or iller: '["İzmir"]'
    pattern = r'^(\s*(?:turler|iller|ilceler):\s+)\'(\[.+\])\'(\s*)$'
    match = re.match(pattern, line)

    if match:
        prefix = match.group(1)
        array_content = match.group(2)
        suffix = match.group(3)
        # Return without the outer quotes
        return f'{prefix}{array_content}{suffix}\n'

    return line

def fix_content_file(filepath):
    """Fix taxonomy format in a single content file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        modified = False
        new_lines = []

        for line in lines:
            new_line = fix_taxonomy_line(line)
            if new_line != line:
                modified = True
                print(f"  Fixed: {line.strip()} -> {new_line.strip()}")
            new_lines.append(new_line.rstrip('\n'))

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            return True

        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Process all markdown files in content/eserler/."""
    content_dir = Path('content/eserler')

    if not content_dir.exists():
        print(f"Error: Directory {content_dir} not found!")
        return

    files = list(content_dir.glob('*.md'))
    print(f"Found {len(files)} markdown files to process\n")

    modified_count = 0

    for filepath in files:
        if fix_content_file(filepath):
            modified_count += 1

    print(f"\n✓ Processed {len(files)} files")
    print(f"✓ Modified {modified_count} files")
    print(f"✓ No changes needed for {len(files) - modified_count} files")

if __name__ == '__main__':
    main()
