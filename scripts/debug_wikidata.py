import requests

def search_and_inspect(label):
    print(f"\n--- Searching: {label} ---")
    
    # 1. Find the QID for this label
    search_url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": label,
        "language": "tr",
        "format": "json",
        "limit": 1
    }
    
    try:
        resp = requests.get(search_url, params=params, headers={"User-Agent": "MirasHaritasiDebug/1.0"})
        data = resp.json()
        
        if not data.get("search"):
            print("No entity found matching label.")
            return
            
        entity = data["search"][0]
        qid = entity["id"]
        desc = entity.get("description", "No description")
        print(f"Found: {entity['label']} ({qid}) - {desc}")
        
        # 2. Inspect P31 (Instance Of) for this QID
        sparql = f"""
        SELECT ?class ?classLabel WHERE {{
          wd:{qid} wdt:P31 ?class.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,tr". }}
        }}
        """
        sparql_url = "https://query.wikidata.org/sparql"
        resp2 = requests.get(sparql_url, params={"query": sparql, "format": "json"}, headers={"User-Agent": "MirasHaritasiDebug/1.0"})
        data2 = resp2.json()
        
        results = data2["results"]["bindings"]
        for r in results:
             c_label = r.get("classLabel", {}).get("value", "Unknown")
             c_qid = r["class"]["value"].split("/")[-1]
             print(f"  -> Is instance of: {c_label} ({c_qid})")
             
    except Exception as e:
        print(f"Error: {e}")

search_and_inspect("İzmir Saat Kulesi")
search_and_inspect("Dolmabahçe Saat Kulesi")
search_and_inspect("Karatay Medresesi")
search_and_inspect("Çifte Minareli Medrese")
search_and_inspect("Büyük Saat")
