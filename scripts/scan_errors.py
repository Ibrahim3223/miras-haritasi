import os

root_dir = "content/eserler"
broken_files = []

for filename in os.listdir(root_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(root_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.startswith("featured_image:"):
                        # Check count of double quotes
                        # Expected format: featured_image: "URL"
                        # If weird: featured_image: "URL"weird"
                        if line.count('"') > 2:
                            broken_files.append((filename, i + 1, line.strip()))
        except Exception as e:
            print(f"Error reading {filename}: {e}")

if broken_files:
    print(f"Found {len(broken_files)} broken files:")
    for f, line_num, content in broken_files:
        print(f"{f}:{line_num} -> {content}")
else:
    print("No broken files found.")
