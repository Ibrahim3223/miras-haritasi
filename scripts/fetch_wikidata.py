import requests
import json
import time
from pathlib import Path
from urllib.parse import unquote

# Categories to fetch
# Categories to fetch
CATEGORIES = {
    "Cami": "Q32815",
    "Kale": "Q23413",
    "Köprü": "Q12280",
    "Müze": "Q33506",
    "Arkeolojik Sit": "Q839954",
    "Kervansaray": "Q1021645",
    "Kilise": "Q16970",
    "Manastır": "Q44613",
    "Çeşme": "Q483453",
    "Saray": "Q16560",
    "Anıt": "Q4989906",
    "Sinagog": "Q34627",
    "Antik Tiyatro": "Q24354",
    
    # Sorunlu Kategoriler & Güncel QID'ler (Debug Sonucu V2)
    "Antik Kent": "Q839954",  # Archaeological Site
    "Hamam": "Q28077",        # Hammam
    "Türbe": "Q838159",       # Türbe
    "Saat Kulesi": "Q853854", # Clock Tower
    "Medrese": "Q132834",     # Madrasa
    "Su Kemeri": "Q13465",    # Aqueduct
    "Kütüphane": "Q7075",     # Library
}

def get_sparql_query(type_id, offset=0):
    query = f"""
    SELECT DISTINCT ?item ?itemLabel ?image ?coords ?provinceLabel ?districtLabel ?article WHERE {{
      ?item wdt:P17 wd:Q43; # Country: Turkey
            wdt:P31/wdt:P279* wd:{type_id}. 
      
      OPTIONAL {{ ?item wdt:P18 ?image. }}
      OPTIONAL {{ ?item wdt:P625 ?coords. }}
      OPTIONAL {{ ?item wdt:P131 ?district. ?district wdt:P131 ?province. }}
      OPTIONAL {{ ?article schema:about ?item ; schema:isPartOf <https://tr.wikipedia.org/> . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }}
    }}
    LIMIT 2500
    OFFSET {offset}
    """
    return query

def fetch_data(query):
    url = "https://query.wikidata.org/sparql"
    headers = {
        "User-Agent": "MirasHaritasiBot/1.0 (contact@mirasharitasi.com)"
    }
    params = {
        "query": query,
        "format": "json"
    }

    retries = 3
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            results = data["results"]["bindings"]
            return results
        except Exception as e:
            print(f"    Error (attempt {i+1}): {e}")
            time.sleep(2)
    return []

def process_results(results, type_label):
    processed = []
    
    for result in results:
        item_id = result["item"]["value"].split("/")[-1]
        name = result.get("itemLabel", {}).get("value", "Bilinmeyen Eser")
        
        if name.startswith("Q") and name[1:].isdigit():
            continue

        image_url = result.get("image", {}).get("value", "")
        image_filename = ""
        if image_url:
            image_filename = unquote(image_url.split("/")[-1])

        entry = {
            "id": item_id,
            "title": name,
            "type": type_label,
            "province": result.get("provinceLabel", {}).get("value", ""),
            "district": result.get("districtLabel", {}).get("value", ""),
            "coords": result.get("coords", {}).get("value", "").replace("Point(", "").replace(")", "").replace(" ", ","),
            "image_url": image_url,
            "image_filename": image_filename,
            "wikipedia_url": result.get("article", {}).get("value", ""),
            "wikidata_url": result["item"]["value"]
        }
        processed.append(entry)
    
    return processed

def main():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    all_data = []
    seen_ids = set()

    for cat_name, cat_id in CATEGORIES.items():
        print(f"Fetching {cat_name} ({cat_id})...")
        offset = 0
        while True:
            query = get_sparql_query(cat_id, offset)
            results = fetch_data(query)
            
            if not results:
                break
                
            print(f"  Got {len(results)} items (Offset: {offset})")
            
            processed = process_results(results, cat_name)
            new_count = 0
            for item in processed:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    all_data.append(item)
                    new_count += 1
            
            print(f"  Added {new_count} new items (Total Unique: {len(all_data)})")
            
            if len(results) < 2500:
                break
                
            offset += 2500
            time.sleep(1) # Be nice to API

    print(f"Total unique items: {len(all_data)}")

    output_file = data_dir / "eserler.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    main()
