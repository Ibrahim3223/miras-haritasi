import os

root_dir = "content/eserler"
fixed_count = 0

print("Scanning and fixing Markdown files...")

for filename in os.listdir(root_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(root_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            modified = False
            new_lines = []
            
            for line in lines:
                # Check for the specific broken pattern: key: "value "quote" value"
                if line.startswith("featured_image:"):
                    # If it has more than 2 quotes (opening and closing)
                    if line.count('"') > 2:
                        # Extract the URL part
                        # Assuming format: featured_image: "URL"
                        # We want to change outer quotes to single quotes if inner are double
                        parts = line.split("featured_image:", 1)
                        if len(parts) == 2:
                            val = parts[1].strip()
                            # If it starts and ends with double quote
                            if val.startswith('"') and val.endswith('"'):
                                inner_content = val[1:-1]
                                # If inner content has quotes
                                if '"' in inner_content:
                                    # Use single quotes for outer wrapping
                                    new_line = f"featured_image: '{inner_content}'\n"
                                    new_lines.append(new_line)
                                    modified = True
                                    continue
                
                new_lines.append(line)
            
            if modified:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                fixed_count += 1
                print(f"Fixed: {filename}")

        except Exception as e:
            print(f"Error checking {filename}: {e}")

print(f"Done! Fixed {fixed_count} files.")
