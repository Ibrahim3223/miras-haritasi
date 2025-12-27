import os
import glob
import re

# Constants
VIP_LIST = [
    "ayasofya", "topkapi-sarayi", "efes-antik-kenti", "kapadokya", "anitkabir",
    "sultan-ahmet-camii", "pamukkale", "sumela-manastiri", "aspendos", "gobeklitepe",
    "galata-kulesi", "kiz-kulesi", "dolmabahce-sarayi", "selimiye-camii", "ishak-pasa-sarayi",
    "nemrut-dagi", "zeugma", "topkapi", "suleymaniye", "yerebatan"
]

CONTENT_DIR = "content/eserler"

def score_content():
    print("Scoring content based on visual quality and importance (No Dependencies)...")
    
    files = glob.glob(os.path.join(CONTENT_DIR, "*.md"))
    count = 0
    updated = 0
    
    # Regex to find weight
    weight_pattern = re.compile(r"^weight:\s*(\d+)", re.MULTILINE)
    
    for filepath in files:
        count += 1
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse YAML Front Matter (Between first two ---)
            parts = content.split('---', 2)
            if len(parts) < 3:
                continue # Invalid Format
                
            front_matter = parts[1]
            body = parts[2]
            
            # Extract basic fields manually
            slug = ""
            title = ""
            has_image = False
            
            # Simple line parsing
            for line in front_matter.split('\n'):
                line = line.strip()
                if line.startswith('slug:'):
                    slug = line.replace('slug:', '').strip().replace('"', '')
                if line.startswith('title:'):
                    title = line.replace('title:', '').strip().replace('"', '')
                if line.startswith('image:') or line.startswith('featured_image:') or line.startswith('cover:'):
                    # Check if value is not empty/null
                    val = line.split(':', 1)[1].strip().replace('"', '')
                    if len(val) > 5:
                        has_image = True

            # Logic
            is_vip = False
            title_lower = title.lower()
            slug_lower = slug.lower()
            
            for vip in VIP_LIST:
                if vip in slug_lower or vip in title_lower:
                    is_vip = True
                    break
            
            new_weight = 100
            if is_vip:
                new_weight = 1
            elif has_image:
                new_weight = 10
            else:
                new_weight = 100
            
            # Replace or Add Weight
            if weight_pattern.search(front_matter):
                # Check exist value
                existing_weight = int(weight_pattern.search(front_matter).group(1))
                if existing_weight != new_weight:
                    new_front_matter = weight_pattern.sub(f"weight: {new_weight}", front_matter)
                    new_content = f"---{new_front_matter}---{body}"
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    updated += 1
            else:
                # Append weight
                new_front_matter = front_matter + f"\nweight: {new_weight}\n"
                new_content = f"---{new_front_matter}---{body}"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                updated += 1

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print(f"Processed {count} files. Updated weights for {updated} files.")

if __name__ == "__main__":
    score_content()
