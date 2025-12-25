#!/usr/bin/env python3
"""
Miras Haritası - İçerik Üretim Scripti
- Wikidata'dan alınan eser listesini okur
- Groq API ile SEO uyumlu içerik üretir
- Wikimedia Commons görsellerini thumbnail olarak ekler
- Hugo content dosyalarını oluşturur
"""

import json
import asyncio
import aiohttp
import os
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import re
import time
import hashlib

# ============================================================================
#  YAPILANDIRMA
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

# API Keys dosyasi
API_KEYS_FILE = SCRIPT_DIR / "api_keys.json"

# Progress dosyasi
PROGRESS_FILE = SCRIPT_DIR / "generation_progress.json"

# Veri dosyasi
DATA_FILE = PROJECT_DIR / "data" / "eserler.json"

# Cikti klasoru
OUTPUT_DIR = PROJECT_DIR / "content" / "eserler"

# Model
GROQ_MODEL = "llama-3.1-8b-instant"

# ============================================================================
#  YARDIMCI FONKSIYONLAR
# ============================================================================

def get_commons_thumb_url(filename, width=1200):
    """Wikimedia Commons dosya adindan thumbnail URL uretir"""
    if not filename:
        return ""
    
    filename = filename.replace(" ", "_")
    md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
    a = md5_hash[0]
    ab = md5_hash[0:2]
    
    # URL format: https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/{filename}/{width}px-{filename}
    url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{filename}/{width}px-{filename}"
    
    # Bazi dosya uzantilari icin (svg, tif vb) ozel durumlar olabilir ama jpg/png icin bu standarttir.
    if filename.lower().endswith(".svg"):
        url += ".png"
        
    return url

def slugify(text):
    """Turkce karakterleri cevirerek slug olustur"""
    text = text.lower()
    replacements = {
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
        ' ': '-', '.': '', ',': '', "'": '', '"': '', '(': '', ')': ''
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^a-z0-9-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

# ============================================================================
#  API KEY YONETICISI
# ============================================================================

class APIKeyManager:
    def __init__(self, keys_file: Path):
        self.keys = []
        self.current_index = 0
        self.exhausted_keys = set()
        self._load_keys(keys_file)

    def _load_keys(self, keys_file: Path):
        if not keys_file.exists():
            raise FileNotFoundError(f"API keys dosyasi bulunamadi: {keys_file}")
        with open(keys_file, 'r') as f:
            data = json.load(f)
        self.keys = data.get("groq_api_keys", [])
        if not self.keys:
            raise ValueError("API keys dosyasinda anahtar bulunamadi!")

    def get_current_key(self) -> str:
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
        original_index = self.current_index
        for _ in range(len(self.keys)):
            self.current_index = (self.current_index + 1) % len(self.keys)
            if self.keys[self.current_index] not in self.exhausted_keys:
                return
        self.current_index = original_index

    def all_exhausted(self) -> bool:
        return len(self.exhausted_keys) >= len(self.keys)

# ============================================================================
#  GROQ API CLIENT
# ============================================================================

class GroqClient:
    def __init__(self, key_manager: APIKeyManager):
        self.key_manager = key_manager
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.last_request_time = 0

    async def generate(self, system_prompt: str, user_prompt: str, retry_count: int = 0) -> str:
        if self.key_manager.all_exhausted():
            return None

        api_key = self.key_manager.get_current_key()
        
        # Rate limiting
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        if time_diff < 2.0: # Biraz daha yavas olsun
            await asyncio.sleep(2.0 - time_diff)

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
            "max_tokens": 2048,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload, timeout=60) as resp:
                    self.last_request_time = time.time()
                    
                    if resp.status == 200:
                        result = await resp.json()
                        return result["choices"][0]["message"]["content"]
                    elif resp.status == 429:
                        error_text = await resp.text()
                        if "daily" in error_text.lower():
                            self.key_manager.mark_exhausted()
                            return await self.generate(system_prompt, user_prompt, retry_count)
                        else:
                            if retry_count < len(self.key_manager.keys):
                                self.key_manager.rotate_key()
                                await asyncio.sleep(2)
                                return await self.generate(system_prompt, user_prompt, retry_count + 1)
                            else:
                                await asyncio.sleep(60)
                                return await self.generate(system_prompt, user_prompt, 0)
                    else:
                        print(f"API Error: {resp.status}")
                        return ""
        except Exception as e:
            print(f"Connection Error: {e}")
            if retry_count < 3:
                await asyncio.sleep(5)
                return await self.generate(system_prompt, user_prompt, retry_count + 1)
            return ""

# ============================================================================
#  ICERIK URETICISI
# ============================================================================

class ContentGenerator:
    def __init__(self, key_manager: APIKeyManager):
        self.client = GroqClient(key_manager)
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.completed_ids = set()
        self._load_progress()

    def _load_progress(self):
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                self.completed_ids = set(data.get("completed_ids", []))

    def save_progress(self):
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({"completed_ids": list(self.completed_ids)}, f)

    def get_prompts(self, item: dict):
        system_prompt = """Sen Türkiye'nin tarihi ve kültürel mirası konusunda uzman bir tarihçi ve rehbersin. 
        Verilen tarihi yapı hakkında bilgilendirici, SEO uyumlu ve akıcı bir makale yazmalısın.
        Kesinlikle uydurma bilgi verme. Bilmediğin detayları genel ifadelerle geç."""

        user_prompt = f"""
        Aşağıdaki tarihi eser hakkında detaylı bir tanıtım yazısı yaz:
        
        Eser Adı: {item['title']}
        Tür: {item['type']}
        Konum: {item['district']}, {item['province']}
        
        İÇERİK PLANI:
        1. Giriş (Eserin ne olduğu, nerede olduğu, kısa önemi)
        2. Tarihçe (Ne zaman yapıldı, kim yaptı, hangi dönem - eğer biliniyorsa)
        3. Mimari Özellikler (Yapısal özellikler, malzeme, plan vb.)
        4. Ziyaret Bilgileri (Nasıl gidilir, ne zaman gidilir - genel tavsiyeler)
        5. Neden Önemli? (Kültürel miras değeri)
        
        KURALLAR:
        - Markdown formatında yaz.
        - Başlıkları ## ile belirt (Giriş başlığı atma, direkt başla).
        - Alt başlıkları ### ile belirt.
        - Paragraflar halinde yaz, madde işaretlerini sadece gerekirse kullan.
        - En az 500 kelime olsun.
        - Dil: Türkçe.
        """
        return system_prompt, user_prompt

    def create_frontmatter(self, item: dict, content: str) -> str:
        slug = slugify(item['title'])
        desc = content.split('\n')[0][:160].replace('"', "'") + "..."
        
        image_url = get_commons_thumb_url(item.get('image_filename'))
        
        return f"""---
title: "{item['title']} | Miras Haritası"
date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S+03:00')}
slug: "{slug}"
description: "{desc}"
featured_image: "{image_url}"
province: "{item['province']}"
iller: ["{item['province']}"]
district: "{item['district']}"
type: "{item['type']}"
turler: ["{item['type']}"]
coords: "{item.get('coords', '')}"
draft: false
---

"""

    async def generate_item(self, item: dict):
        if item['id'] in self.completed_ids:
            return True

        slug = slugify(item['title'])
        filepath = self.output_dir / f"{slug}.md"
        
        if filepath.exists():
            self.completed_ids.add(item['id'])
            return True

        system_prompt, user_prompt = self.get_prompts(item)
        content = await self.client.generate(system_prompt, user_prompt)

        if not content:
            return False

        # Attribution ekle
        attribution = f"\n\n---\n\n**Kaynaklar:**\n- [Wikidata]({item['wikidata_url']})\n"
        if item.get('wikipedia_url'):
            attribution += f"- [Wikipedia]({item['wikipedia_url']})\n"
        
        if item.get('image_filename'):
            attribution += f"\n**Görsel Kaynağı:** Wikimedia Commons ({item['image_filename']})"

        full_content = self.create_frontmatter(item, content) + content + attribution

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)

        self.completed_ids.add(item['id'])
        return True

    async def generate_all(self):
        if not DATA_FILE.exists():
            print("Veri dosyasi bulunamadi!")
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            items = json.load(f)

        print(f"Toplam {len(items)} eser islenecek.")
        
        pbar = tqdm(items)
        for item in pbar:
            pbar.set_description(f"Isleniyor: {item['title'][:20]}")
            success = await self.generate_item(item)
            if not success and self.client.key_manager.all_exhausted():
                print("Tum keyler tukendi!")
                break
            
            if len(self.completed_ids) % 10 == 0:
                self.save_progress()

        self.save_progress()

async def main():
    try:
        key_manager = APIKeyManager(API_KEYS_FILE)
        generator = ContentGenerator(key_manager)
        await generator.generate_all()
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    asyncio.run(main())
