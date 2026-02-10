#!/usr/bin/env python3
"""
404 veren çeşme sayfalarını geri getirme scripti.
GSC export CSV'sindeki 404 URL'leri data/eserler.json ile eşleştirir
ve matching çeşmeler için Hugo markdown dosyaları oluşturur.
"""

import json
import re
import os
import hashlib
from pathlib import Path
from datetime import datetime
import openpyxl

# ============================================================================
# YAPILANDIRMA
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_FILE = PROJECT_DIR / "data" / "eserler.json"
OUTPUT_DIR = PROJECT_DIR / "content" / "eserler"
UNMATCHED_FILE = PROJECT_DIR / "unmatched_404s.txt"

# Excel dosyası
EXCEL_FILE = PROJECT_DIR / "mirasharitasi.com-Coverage-Validation-2026-02-10.xlsx"

# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

def slugify(text):
    """Türkçe karakterleri çevirerek slug oluştur - generate_content_miras.py ile aynı"""
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

def get_commons_thumb_url(filename, width=1200):
    """Wikimedia Commons thumbnail URL üret"""
    if not filename:
        return ""
    filename = filename.replace(" ", "_")
    md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
    a = md5_hash[0]
    ab = md5_hash[0:2]
    url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{filename}/{width}px-{filename}"
    if filename.lower().endswith(".svg"):
        url += ".png"
    return url

def create_frontmatter(item: dict) -> str:
    """Front matter oluştur - mevcut dosyalarla tutarlı format"""
    slug = slugify(item['title'])
    title = item['title']
    province = item.get('province', '')
    district = item.get('district', '')
    item_type = item.get('type', 'Çeşme')
    coords = item.get('coords', '')
    wikidata_url = item.get('wikidata_url', '')
    wikipedia_url = item.get('wikipedia_url', '')

    image_filename = item.get('image_filename', '')
    featured_image = get_commons_thumb_url(image_filename) if image_filename else ""

    # Tarih - özgün tarih bilinmiyor, sabit bir tarih kullanalım
    date_str = "2025-01-04T10:00:00+03:00"

    # Basit açıklama
    description = f"{title}, {district}, {province} ilinde bulunan tarihi bir çeşmedir."

    return f"""---
title: "{title}"
date: "{date_str}"
slug: "{slug}"
description: "{description}"
featured_image: "{featured_image}"
province: "{province}"
iller: ["{province}"]
district: "{district}"
type: "{item_type}"
turler: ["{item_type}"]
coords: "{coords}"
draft: "false"
weight: "1"
---

"""

def create_content(item: dict) -> str:
    """Çeşme için Markdown içerik oluştur"""
    title = item['title']
    province = item.get('province', '')
    district = item.get('district', '')
    item_type = item.get('type', 'Çeşme')
    wikidata_url = item.get('wikidata_url', '')
    wikipedia_url = item.get('wikipedia_url', '')

    location_str = f"{district}, {province}" if district else province

    content = f"""## {title}

{title}, {location_str} ilinde bulunan tarihi bir {item_type.lower()}dir. Türkiye'nin zengin su mirasının önemli örneklerinden biri olan bu yapı, bulunduğu bölgenin kültürel ve tarihi kimliğine katkı sağlamaktadır.

## Konum ve Erişim

{title}, {province} iline bağlı {district} bölgesinde yer almaktadır. Yapıya ulaşmak için {province} şehir merkezinden yararlanılabilir.

## Tarihsel Önemi

Bu çeşme, Osmanlı dönemi su mimarlığının bölgedeki örneklerinden birini teşkil etmektedir. Tarihi çeşmeler, geçmiş dönemlerde halka açık içme suyu sağlayan ve sosyal buluşma noktaları işlevi gören önemli yapılardır. {province} iline ait bu yapı, Türkiye genelindeki tarihi su mirasının korunması gereken parçalarından biridir.

## Mimari Özellikler

Osmanlı dönemi çeşme mimarisinin genel özelliklerini yansıtan bu yapı, taş işçiliği ve süsleme unsurlarıyla dikkat çekmektedir. Bölgedeki diğer tarihi yapılarla birlikte değerlendirildiğinde, yerel mimari geleneğin önemli bir temsilcisi olduğu görülmektedir.

## Ziyaret Bilgileri

Çeşme, {location_str} bölgesinde açık hava mekânında yer almaktadır. Ziyaret için özel bir giriş ücreti bulunmamakta olup bölgeye her mevsim ulaşmak mümkündür.

---

**Kaynaklar:**
- [Wikidata]({wikidata_url})
"""

    if wikipedia_url:
        content += f"- [Wikipedia]({wikipedia_url})\n"

    if item.get('image_filename'):
        content += f"\n**Görsel Kaynağı:** Wikimedia Commons ({item['image_filename']})"

    return content

# ============================================================================
# ANA SÜREÇ
# ============================================================================

def main():
    print("=" * 60)
    print("404 Çeşme Sayfaları Geri Getirme Scripti")
    print("=" * 60)

    # ── ADIM 1: GSC 404 URL'lerini oku ──────────────────────────────
    print("\n[ADIM 1] GSC 404 listesi okunuyor...")

    if not EXCEL_FILE.exists():
        print(f"HATA: Excel dosyası bulunamadı: {EXCEL_FILE}")
        return

    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active

    gsc_slugs = set()
    gsc_urls = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        url = row[0]
        if not url or not isinstance(url, str):
            continue
        url = url.strip().rstrip('/')
        # /eserler/SLUG şeklinde URL'lerden slug çıkar
        match = re.search(r'/eserler/([^/]+)/?$', url)
        if match:
            slug = match.group(1)
            gsc_slugs.add(slug)
            gsc_urls.append(url)

    print(f"  → Toplam 404 URL: {len(gsc_urls)}")
    print(f"  → /eserler/ altındaki: {len(gsc_slugs)} benzersiz slug")
    print(f"  → İlk 5 slug: {list(gsc_slugs)[:5]}")

    # ── ADIM 2: Data dosyasını oku ───────────────────────────────────
    print("\n[ADIM 2] Veri dosyası okunuyor...")

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    # Çeşme kayıtlarını filtrele (tüm type varyasyonları)
    cesmeler = [
        item for item in all_data
        if item.get('type', '') in ['Çeşme', 'Çeşme ve Sebil', 'Sebil', 'Şadırvan']
        or 'eşme' in item.get('type', '')
    ]

    print(f"  → Toplam eser: {len(all_data)}")
    print(f"  → Çeşme/sebil türleri: {len(cesmeler)}")

    # Her çeşmenin slug'ını oluştur
    cesme_by_slug = {}
    slug_collisions = []
    for item in cesmeler:
        slug = slugify(item['title'])
        if slug in cesme_by_slug:
            slug_collisions.append(f"  ÇAKIŞMA: '{slug}' - '{item['title']}' vs '{cesme_by_slug[slug]['title']}'")
        cesme_by_slug[slug] = item

    if slug_collisions:
        print(f"  → {len(slug_collisions)} slug çakışması (ilk 5):")
        for c in slug_collisions[:5]:
            print(c)

    # ── ADIM 3: Eşleştir ────────────────────────────────────────────
    print("\n[ADIM 3] Eşleştirme yapılıyor...")

    matched = {}      # slug -> item
    unmatched = []    # GSC URL'leri

    for slug in gsc_slugs:
        if slug in cesme_by_slug:
            matched[slug] = cesme_by_slug[slug]
        else:
            # Eşleşmeyen URL'yi bul
            for url in gsc_urls:
                if f'/eserler/{slug}' in url:
                    unmatched.append(url + '/')
                    break

    print(f"  → Eşleşen: {len(matched)}")
    print(f"  → Eşleşmeyen: {len(unmatched)}")

    if matched:
        print(f"  → İlk 5 eşleşen:")
        for slug, item in list(matched.items())[:5]:
            print(f"    {slug} ← {item['title']}")

    if unmatched[:5]:
        print(f"  → İlk 5 eşleşmeyen:")
        for url in unmatched[:5]:
            print(f"    {url}")

    # ── ADIM 4: Mevcut dosyaları kontrol et ve oluştur ──────────────
    print("\n[ADIM 4] Markdown dosyaları oluşturuluyor...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    already_exists = 0

    for slug, item in matched.items():
        filepath = OUTPUT_DIR / f"{slug}.md"

        if filepath.exists():
            already_exists += 1
            continue

        frontmatter = create_frontmatter(item)
        content = create_content(item)
        full_content = frontmatter + content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)

        created += 1

    print(f"  → Yeni oluşturulan: {created}")
    print(f"  → Zaten mevcut: {already_exists}")
    print(f"  → Toplam işlenen: {created + already_exists}")

    # ── ADIM 5: Eşleşmeyenleri yaz ──────────────────────────────────
    print("\n[ADIM 5] Eşleşmeyen URL'ler yazılıyor...")

    with open(UNMATCHED_FILE, 'w', encoding='utf-8') as f:
        f.write("# Eşleşmeyen 404 URL'ler - 410 Gone için\n")
        f.write(f"# Toplam: {len(unmatched)}\n")
        f.write(f"# Oluşturma tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for url in sorted(unmatched):
            f.write(url + "\n")

    print(f"  → {len(unmatched)} URL unmatched_404s.txt'ye yazıldı")

    # ── ADIM 6: Doğrulama ────────────────────────────────────────────
    print("\n[ADIM 6] Doğrulama...")

    # Mevcut toplam dosya sayısı
    total_md = len(list(OUTPUT_DIR.glob("*.md")))
    print(f"  → content/eserler/ içindeki toplam .md dosyası: {total_md}")

    # Örnek dosyaları göster
    if created > 0:
        print("\n  Örnek oluşturulan dosyalar:")
        count = 0
        for slug in list(matched.keys())[:3]:
            filepath = OUTPUT_DIR / f"{slug}.md"
            if filepath.exists():
                lines = filepath.read_text(encoding='utf-8').split('\n')
                print(f"\n  --- {slug}.md (ilk 8 satır) ---")
                for line in lines[:8]:
                    print(f"  {line}")
                count += 1

    # Cloudflare Pages limit uyarısı
    print(f"\n  [UYARI] Cloudflare Pages 20.000 dosya limiti:")
    print(f"  Mevcut .md dosyası: {total_md}")
    # Hugo bu dosyaların her birinden 1 HTML + pagination sayfaları üretir
    estimated_pages = total_md + 2000  # pagination ve taxonomy sayfaları tahmini
    print(f"  Tahmini toplam Hugo sayfası: ~{estimated_pages}")
    if total_md > 17000:
        print("  ⚠️  DİKKAT: 17.000+ dosya, Hugo sayfaları 20.000 limiti yaklaşıyor!")
    else:
        print("  ✓ Cloudflare Pages 20.000 limiti güvenli.")

    print("\n" + "=" * 60)
    print("TAMAMLANDI!")
    print(f"  Oluşturulan: {created} yeni çeşme sayfası")
    print(f"  Eşleşmeyen: {len(unmatched)} URL → unmatched_404s.txt")
    print("=" * 60)

    # 410 önerisi
    if unmatched:
        print("\n[410 ÖNERİSİ] Cloudflare Bulk Redirect için:")
        print("  Cloudflare Dashboard → Bulk Redirects → Create list")
        print("  Her satır için: Source URL → /gone (410 status)")
        print("\n  Veya static/_redirects dosyasına ekle:")
        print("  (İlk 5 örnek)")
        for url in unmatched[:5]:
            path = url.replace('https://mirasharitasi.com', '')
            print(f"  {path} /gone 410")

if __name__ == "__main__":
    main()
