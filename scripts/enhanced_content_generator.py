#!/usr/bin/env python3
"""
Miras Haritası - Gelişmiş İçerik Üretim Sistemi v2.0

Bu script:
1. Mevcut eserler.json verisini okur
2. Her eser için Wikipedia'dan özet ve ek bilgi çeker
3. Wikidata'dan eksik görselleri bulmaya çalışır
4. Province/district verilerini düzeltir
5. Groq API ile zengin içerik üretir
6. Hugo content dosyalarını oluşturur/günceller

Kullanım:
    python enhanced_content_generator.py --mode [full|update|fix-images|fix-provinces]
"""

import json
import asyncio
import aiohttp
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import re
import time
import hashlib
from typing import Optional, Dict, List, Any

# ============================================================================
#  YAPILANDIRMA
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

API_KEYS_FILE = SCRIPT_DIR / "api_keys.json"
PROGRESS_FILE = SCRIPT_DIR / "enhanced_progress.json"
DATA_FILE = PROJECT_DIR / "data" / "eserler.json"
OUTPUT_DIR = PROJECT_DIR / "content" / "eserler"

# Türkiye'nin 81 ili
TURKEY_PROVINCES = {
    "adana", "adiyaman", "afyonkarahisar", "agri", "aksaray", "amasya", "ankara",
    "antalya", "ardahan", "artvin", "aydin", "balikesir", "bartin", "batman",
    "bayburt", "bilecik", "bingol", "bitlis", "bolu", "burdur", "bursa",
    "canakkale", "cankiri", "corum", "denizli", "diyarbakir", "duzce", "edirne",
    "elazig", "erzincan", "erzurum", "eskisehir", "gaziantep", "giresun",
    "gumushane", "hakkari", "hatay", "igdir", "isparta", "istanbul", "izmir",
    "kahramanmaras", "karabuk", "karaman", "kars", "kastamonu", "kayseri",
    "kilis", "kirikkale", "kirklareli", "kirsehir", "kocaeli", "konya",
    "kutahya", "malatya", "manisa", "mardin", "mersin", "mugla", "mus",
    "nevsehir", "nigde", "ordu", "osmaniye", "rize", "sakarya", "samsun",
    "sanliurfa", "siirt", "sinop", "sirnak", "sivas", "tekirdag", "tokat",
    "trabzon", "tunceli", "usak", "van", "yalova", "yozgat", "zonguldak"
}

# İstanbul ilçeleri (en yaygın olanlar)
ISTANBUL_DISTRICTS = {
    "fatih", "beyoglu", "besiktas", "uskudar", "kadikoy", "sisli", "bakirkoy",
    "zeytinburnu", "eyupsultan", "sariyer", "maltepe", "kartal", "pendik",
    "tuzla", "sultanbeyli", "umraniye", "atasehir", "beykoz", "sile", "adalar",
    "avcilar", "bagcilar", "bahcelievler", "basaksehir", "bayrampasa", "buyukcekmece",
    "catalca", "cekmekoy", "esenler", "esenyurt", "gaziosmanpasa", "gungoren",
    "kagithane", "kucukcekmece", "sultangazi", "arnavutkoy", "sultanahmet"
}

GROQ_MODEL = "llama-3.3-70b-versatile"  # Daha kaliteli model

# ============================================================================
#  YARDIMCI FONKSIYONLAR
# ============================================================================

def normalize_text(text: str) -> str:
    """Türkçe karakterleri ASCII'ye çevir"""
    replacements = {
        'ı': 'i', 'İ': 'i', 'ğ': 'g', 'Ğ': 'g', 'ü': 'u', 'Ü': 'u',
        'ş': 's', 'Ş': 's', 'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
    }
    text = text.lower()
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def fix_province_district(province: str, district: str) -> tuple:
    """Province ve district verilerini düzelt"""
    province_norm = normalize_text(province.strip()) if province else ""
    district_norm = normalize_text(district.strip()) if district else ""

    # Eğer province boş veya "türkiye" ise ve district bir il ise, swap yap
    if province_norm in ["", "turkiye", "turkey"]:
        if district_norm in TURKEY_PROVINCES:
            return district.strip(), ""

    # Eğer province bir İstanbul ilçesi ise, düzelt
    if province_norm in ISTANBUL_DISTRICTS:
        return "İstanbul", province.strip()

    # Eğer province bir il değilse ama district bir il ise, swap
    if province_norm not in TURKEY_PROVINCES and district_norm in TURKEY_PROVINCES:
        return district.strip(), province.strip()

    return province.strip() if province else "", district.strip() if district else ""

def get_commons_thumb_url(filename: str, width: int = 1200) -> str:
    """Wikimedia Commons dosya adından thumbnail URL üret"""
    if not filename:
        return ""

    filename = filename.replace(" ", "_")
    md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
    a = md5_hash[0]
    ab = md5_hash[0:2]

    url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{filename}/{width}px-{filename}"

    if filename.lower().endswith(".svg"):
        url += ".png"
    elif filename.lower().endswith(".tif") or filename.lower().endswith(".tiff"):
        url = url.replace(filename, filename + ".jpg")

    return url

def slugify(text: str) -> str:
    """Türkçe karakterleri çevirerek slug oluştur"""
    text = text.lower()
    # "| Miras Haritası" kısmını kaldır
    text = re.sub(r'\s*\|\s*miras haritası', '', text, flags=re.IGNORECASE)

    replacements = {
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
        ' ': '-', '.': '', ',': '', "'": '', '"': '', '(': '', ')': '',
        ':': '', ';': '', '?': '', '!': '', '/': '-', '\\': '-'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^a-z0-9-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def clean_title(title: str) -> str:
    """Title'dan gereksiz ekleri temizle"""
    title = re.sub(r'\s*\|\s*Miras Haritası\s*$', '', title, flags=re.IGNORECASE)
    return title.strip()

# ============================================================================
#  WIKIPEDIA DATA FETCHER
# ============================================================================

class WikipediaFetcher:
    """Wikipedia'dan özet ve ek bilgi çeker"""

    def __init__(self):
        self.base_url = "https://tr.wikipedia.org/api/rest_v1"
        self.session = None

    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_summary(self, title: str) -> Optional[Dict]:
        """Wikipedia makale özetini al"""
        try:
            session = await self.get_session()
            url = f"{self.base_url}/page/summary/{title.replace(' ', '_')}"

            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "extract": data.get("extract", ""),
                        "description": data.get("description", ""),
                        "thumbnail": data.get("thumbnail", {}).get("source", ""),
                        "coordinates": data.get("coordinates", {})
                    }
        except Exception as e:
            pass
        return None

    async def get_from_wikidata_id(self, qid: str) -> Optional[Dict]:
        """Wikidata ID'den Wikipedia bilgisi al"""
        try:
            session = await self.get_session()
            url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    entity = data.get("entities", {}).get(qid, {})

                    # Türkçe Wikipedia linki bul
                    sitelinks = entity.get("sitelinks", {})
                    tr_wiki = sitelinks.get("trwiki", {}).get("title", "")

                    if tr_wiki:
                        return await self.get_summary(tr_wiki)
        except Exception as e:
            pass
        return None

# ============================================================================
#  WIKIDATA IMAGE FINDER
# ============================================================================

class WikidataImageFinder:
    """Wikidata'dan eksik görselleri bulmaya çalışır"""

    def __init__(self):
        self.sparql_url = "https://query.wikidata.org/sparql"
        self.session = None

    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def find_image_for_item(self, qid: str) -> Optional[str]:
        """Wikidata öğesi için görsel bul"""
        query = f"""
        SELECT ?image WHERE {{
            wd:{qid} wdt:P18 ?image .
        }} LIMIT 1
        """

        try:
            session = await self.get_session()
            async with session.get(
                self.sparql_url,
                params={"query": query, "format": "json"},
                headers={"User-Agent": "MirasHaritasi/2.0"},
                timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", {}).get("bindings", [])
                    if results:
                        image_url = results[0].get("image", {}).get("value", "")
                        if image_url:
                            # URL'den dosya adını çıkar
                            filename = image_url.split("/")[-1]
                            from urllib.parse import unquote
                            return unquote(filename)
        except Exception as e:
            pass
        return None

# ============================================================================
#  GROQ API CLIENT
# ============================================================================

class APIKeyManager:
    def __init__(self, keys_file: Path):
        self.keys = []
        self.current_index = 0
        self.exhausted_keys = set()
        self._load_keys(keys_file)

    def _load_keys(self, keys_file: Path):
        if not keys_file.exists():
            raise FileNotFoundError(f"API keys dosyası bulunamadı: {keys_file}")
        with open(keys_file, 'r') as f:
            data = json.load(f)
        self.keys = data.get("groq_api_keys", [])
        if not self.keys:
            raise ValueError("API keys dosyasında anahtar bulunamadı!")

    def get_current_key(self) -> Optional[str]:
        if self.all_exhausted():
            return None
        return self.keys[self.current_index]

    def mark_exhausted(self):
        current_key = self.keys[self.current_index]
        self.exhausted_keys.add(current_key)
        self._rotate_to_next()

    def rotate_key(self):
        self._rotate_to_next()

    def _rotate_to_next(self):
        for _ in range(len(self.keys)):
            self.current_index = (self.current_index + 1) % len(self.keys)
            if self.keys[self.current_index] not in self.exhausted_keys:
                return

    def all_exhausted(self) -> bool:
        return len(self.exhausted_keys) >= len(self.keys)


class GroqClient:
    def __init__(self, key_manager: APIKeyManager):
        self.key_manager = key_manager
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.last_request_time = 0

    async def generate(self, system_prompt: str, user_prompt: str, retry_count: int = 0) -> Optional[str]:
        if self.key_manager.all_exhausted():
            return None

        api_key = self.key_manager.get_current_key()

        # Rate limiting - 3 saniye bekle
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        if time_diff < 3.0:
            await asyncio.sleep(3.0 - time_diff)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 3000,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload, timeout=90) as resp:
                    self.last_request_time = time.time()

                    if resp.status == 200:
                        result = await resp.json()
                        return result["choices"][0]["message"]["content"]
                    elif resp.status == 429:
                        error_text = await resp.text()
                        if "daily" in error_text.lower() or "quota" in error_text.lower():
                            self.key_manager.mark_exhausted()
                            return await self.generate(system_prompt, user_prompt, retry_count)
                        else:
                            if retry_count < len(self.key_manager.keys):
                                self.key_manager.rotate_key()
                                await asyncio.sleep(5)
                                return await self.generate(system_prompt, user_prompt, retry_count + 1)
                    else:
                        print(f"API Error: {resp.status}")
                        return None
        except Exception as e:
            print(f"Connection Error: {e}")
            if retry_count < 3:
                await asyncio.sleep(10)
                return await self.generate(system_prompt, user_prompt, retry_count + 1)
        return None

# ============================================================================
#  CONTENT GENERATOR
# ============================================================================

class EnhancedContentGenerator:
    def __init__(self, key_manager: APIKeyManager):
        self.client = GroqClient(key_manager)
        self.wiki_fetcher = WikipediaFetcher()
        self.image_finder = WikidataImageFinder()
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.completed_ids = set()
        self.stats = {"generated": 0, "skipped": 0, "errors": 0, "images_found": 0}
        self._load_progress()

    def _load_progress(self):
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                self.completed_ids = set(data.get("completed_ids", []))

    def save_progress(self):
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                "completed_ids": list(self.completed_ids),
                "stats": self.stats,
                "last_run": datetime.now().isoformat()
            }, f, indent=2)

    def get_prompts(self, item: dict, wiki_data: Optional[dict] = None) -> tuple:
        """Geliştirilmiş promptlar"""

        system_prompt = """Sen Türkiye'nin tarihi ve kültürel mirası konusunda uzman bir tarihçi, sanat tarihçisi ve gezi rehberisin.

GÖREV:
Verilen tarihi yapı hakkında kapsamlı, doğru ve ilgi çekici bir makale yaz.

KURALLAR:
1. ASLA uydurma tarih, mimar adı veya detay verme
2. Emin olmadığın bilgileri "...olduğu düşünülmektedir" veya "...tahmin edilmektedir" şeklinde yaz
3. Varsa Wikipedia bilgisini kullan ama genişlet ve zenginleştir
4. Markdown formatında yaz
5. ## ile ana başlıklar, ### ile alt başlıklar kullan
6. Paragraflar halinde akıcı yaz
7. Minimum 600 kelime olsun
8. SEO uyumlu yaz - anahtar kelimeleri doğal şekilde kullan"""

        # Wikipedia verisi varsa ekle
        wiki_context = ""
        if wiki_data and wiki_data.get("extract"):
            wiki_context = f"""

WIKIPEDIA BİLGİSİ:
{wiki_data.get('extract', '')}

AÇIKLAMA: {wiki_data.get('description', '')}
"""

        title = clean_title(item['title'])
        province, district = fix_province_district(item.get('province', ''), item.get('district', ''))

        user_prompt = f"""
Aşağıdaki tarihi eser hakkında detaylı bir tanıtım yazısı yaz:

ESER BİLGİLERİ:
- Adı: {title}
- Tür: {item['type']}
- İl: {province}
- İlçe: {district}
- Koordinat: {item.get('coords', 'Bilinmiyor')}
{wiki_context}

İÇERİK YAPISI:

## {title}

### Giriş
(Eserin ne olduğu, konumu, genel önemi - 2-3 paragraf)

### Tarihçe
(Yapım tarihi, kim tarafından yaptırıldı, hangi dönem, önemli olaylar - eğer biliniyorsa)

### Mimari Özellikler
(Yapı stili, malzeme, plan, önemli unsurlar, sanat değeri)

### Ziyaret Bilgileri
(Konum detayları, ulaşım önerileri, en iyi ziyaret zamanı, çevredeki diğer yerler)

### Neden Ziyaret Etmelisiniz?
(Kültürel önemi, benzersiz özellikleri, ziyaretçiye sunduğu deneyim)
"""
        return system_prompt, user_prompt

    def create_frontmatter(self, item: dict, content: str) -> str:
        """Front matter oluştur"""
        title = clean_title(item['title'])
        slug = slugify(title)

        # İlk paragraftan description oluştur
        first_para = ""
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                first_para = line
                break
        desc = re.sub(r'[*_`]', '', first_para)[:155] + "..."

        # Province/district düzelt
        province, district = fix_province_district(item.get('province', ''), item.get('district', ''))

        # Görsel URL
        image_url = ""
        if item.get('image_filename'):
            image_url = get_commons_thumb_url(item['image_filename'])

        return f"""---
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S+03:00')}
slug: "{slug}"
description: "{desc}"
featured_image: "{image_url}"
image: "{image_url}"
province: "{province}"
iller: ["{province}"]
district: "{district}"
ilceler: ["{district}"]
type: "{item['type']}"
turler: ["{item['type']}"]
coords: "{item.get('coords', '')}"
wikidata_id: "{item.get('id', '')}"
draft: false
---

"""

    async def generate_item(self, item: dict, force: bool = False) -> bool:
        """Tek bir eser için içerik üret"""

        if not force and item['id'] in self.completed_ids:
            self.stats["skipped"] += 1
            return True

        title = clean_title(item['title'])
        slug = slugify(title)
        filepath = self.output_dir / f"{slug}.md"

        if not force and filepath.exists():
            self.completed_ids.add(item['id'])
            self.stats["skipped"] += 1
            return True

        # Wikipedia verisi çek
        wiki_data = None
        if item.get('wikidata_url'):
            qid = item['wikidata_url'].split('/')[-1]
            wiki_data = await self.wiki_fetcher.get_from_wikidata_id(qid)

        # Eksik görsel varsa bulmaya çalış
        if not item.get('image_filename') and item.get('wikidata_url'):
            qid = item['wikidata_url'].split('/')[-1]
            found_image = await self.image_finder.find_image_for_item(qid)
            if found_image:
                item['image_filename'] = found_image
                self.stats["images_found"] += 1

        system_prompt, user_prompt = self.get_prompts(item, wiki_data)
        content = await self.client.generate(system_prompt, user_prompt)

        if not content:
            self.stats["errors"] += 1
            return False

        # Attribution ekle
        attribution = f"\n\n---\n\n**Kaynaklar ve Daha Fazla Bilgi:**\n"
        if item.get('wikipedia_url'):
            attribution += f"- [Wikipedia - {title}]({item['wikipedia_url']})\n"
        attribution += f"- [Wikidata]({item.get('wikidata_url', '')})\n"

        if item.get('image_filename'):
            attribution += f"\n*Görsel: Wikimedia Commons*"

        full_content = self.create_frontmatter(item, content) + content + attribution

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)

        self.completed_ids.add(item['id'])
        self.stats["generated"] += 1
        return True

    async def run(self, mode: str = "full", limit: int = None):
        """Ana çalışma fonksiyonu"""

        if not DATA_FILE.exists():
            print("Veri dosyası bulunamadı!")
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            items = json.load(f)

        if limit:
            items = items[:limit]

        print(f"\n{'='*60}")
        print(f"Miras Haritası - Gelişmiş İçerik Üretim Sistemi v2.0")
        print(f"{'='*60}")
        print(f"Mod: {mode}")
        print(f"Toplam eser: {len(items)}")
        print(f"Daha önce tamamlanan: {len(self.completed_ids)}")
        print(f"{'='*60}\n")

        try:
            pbar = tqdm(items, desc="İşleniyor")
            for item in pbar:
                title = clean_title(item['title'])
                pbar.set_description(f"{title[:30]}...")

                force = mode == "force"
                success = await self.generate_item(item, force=force)

                if not success and self.client.key_manager.all_exhausted():
                    print("\n\nTüm API anahtarları tükendi!")
                    break

                # Her 10 öğede progress kaydet
                if self.stats["generated"] % 10 == 0:
                    self.save_progress()

        finally:
            await self.wiki_fetcher.close()
            await self.image_finder.close()
            self.save_progress()

            print(f"\n{'='*60}")
            print(f"SONUÇLAR:")
            print(f"  Üretilen: {self.stats['generated']}")
            print(f"  Atlanan: {self.stats['skipped']}")
            print(f"  Hata: {self.stats['errors']}")
            print(f"  Bulunan görsel: {self.stats['images_found']}")
            print(f"{'='*60}")


async def main():
    parser = argparse.ArgumentParser(description="Miras Haritası İçerik Üretici")
    parser.add_argument("--mode", choices=["full", "update", "force"], default="update",
                       help="Çalışma modu: full=sıfırdan, update=eksikleri tamamla, force=hepsini yenile")
    parser.add_argument("--limit", type=int, default=None,
                       help="İşlenecek maksimum eser sayısı")
    args = parser.parse_args()

    try:
        key_manager = APIKeyManager(API_KEYS_FILE)
        generator = EnhancedContentGenerator(key_manager)
        await generator.run(mode=args.mode, limit=args.limit)
    except FileNotFoundError as e:
        print(f"Hata: {e}")
        print("Lütfen scripts/api_keys.json dosyasını oluşturun.")
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
