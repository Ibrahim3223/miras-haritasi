import os
import json

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
                if line.startswith("featured_image:"):
                    # Extract the raw valuable part
                    parts = line.split("featured_image:", 1)
                    if len(parts) == 2:
                        raw_val = parts[1].strip()
                        
                        # Heuristic: If it looks like it has quoting issues
                        if raw_val.count('"') > 2 or (raw_val.startswith("'") and raw_val.count("'") > 2):
                            
                            clean_val = raw_val
                            if clean_val.startswith('"') and clean_val.endswith('"'):
                                clean_val = clean_val[1:-1]
                            elif clean_val.startswith("'") and clean_val.endswith("'"):
                                clean_val = clean_val[1:-1]
                            
                            safe_val = json.dumps(clean_val, ensure_ascii=False)
                            new_line = f"featured_image: {safe_val}\n"
                            
                            if new_line != line:
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
