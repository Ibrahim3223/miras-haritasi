#!/usr/bin/env python3
"""
Miras Haritası - Mevcut İçerik Düzeltici

Bu script mevcut markdown dosyalarındaki sorunları düzeltir:
1. Title'lardan "| Miras Haritası" kaldırır
2. Province/District verilerini düzeltir
3. Boş featured_image için eserler.json'dan günceller
4. Eksik alanları tamamlar

Kullanım:
    python fix_existing_content.py --dry-run  # Sadece kontrol
    python fix_existing_content.py            # Düzelt
"""

import json
import re
import argparse
from pathlib import Path
from tqdm import tqdm
import hashlib

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_DIR / "content" / "eserler"
DATA_FILE = PROJECT_DIR / "data" / "eserler.json"

# Türkiye'nin 81 ili (normalize edilmiş)
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

# İstanbul ilçeleri
ISTANBUL_DISTRICTS = {
    "fatih", "beyoglu", "besiktas", "uskudar", "kadikoy", "sisli", "bakirkoy",
    "zeytinburnu", "eyupsultan", "sariyer", "maltepe", "kartal", "pendik",
    "tuzla", "sultanbeyli", "umraniye", "atasehir", "beykoz", "sile", "adalar",
    "avcilar", "bagcilar", "bahcelievler", "basaksehir", "bayrampasa", "buyukcekmece",
    "catalca", "cekmekoy", "esenler", "esenyurt", "gaziosmanpasa", "gungoren",
    "kagithane", "kucukcekmece", "sultangazi", "arnavutkoy"
}


def normalize_text(text):
    replacements = {
        'ı': 'i', 'İ': 'i', 'ğ': 'g', 'Ğ': 'g', 'ü': 'u', 'Ü': 'u',
        'ş': 's', 'Ş': 's', 'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
    }
    text = text.lower().strip()
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def get_commons_thumb_url(filename, width=1200):
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


def fix_province_district(province, district):
    """Province ve district verilerini düzelt"""
    prov_norm = normalize_text(province) if province else ""
    dist_norm = normalize_text(district) if district else ""

    # Boş veya Türkiye ise
    if prov_norm in ["", "turkiye", "turkey"]:
        if dist_norm in TURKEY_PROVINCES:
            return district.strip(), ""
        return "", district.strip() if district else ""

    # İstanbul ilçesi ise
    if prov_norm in ISTANBUL_DISTRICTS:
        return "İstanbul", province.strip()

    # Province il değilse ama district il ise
    if prov_norm not in TURKEY_PROVINCES and dist_norm in TURKEY_PROVINCES:
        return district.strip(), province.strip()

    return province.strip() if province else "", district.strip() if district else ""


def parse_frontmatter(content):
    """Markdown dosyasından frontmatter ve body'yi ayır"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    fm_text = parts[1].strip()
    body = parts[2]

    # Basit YAML parser
    fm = {}
    current_key = None
    current_value = []

    for line in fm_text.split('\n'):
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            if current_key:
                fm[current_key] = '\n'.join(current_value).strip()

            idx = line.index(':')
            current_key = line[:idx].strip()
            current_value = [line[idx+1:].strip()]
        else:
            current_value.append(line)

    if current_key:
        fm[current_key] = '\n'.join(current_value).strip()

    # Değerleri temizle
    for key in fm:
        val = fm[key]
        # Tırnak işaretlerini kaldır
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        fm[key] = val

    return fm, body


def create_frontmatter_text(fm):
    """Frontmatter dict'ten YAML text oluştur"""
    lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            lines.append(f'{key}: {json.dumps(value, ensure_ascii=False)}')
        elif isinstance(value, bool):
            lines.append(f'{key}: {"true" if value else "false"}')
        elif value is None or value == "":
            lines.append(f'{key}: ""')
        else:
            # Özel karakterler varsa tırnak içine al
            if '"' in str(value):
                lines.append(f"{key}: '{value}'")
            else:
                lines.append(f'{key}: "{value}"')
    lines.append("---")
    return '\n'.join(lines)


def load_eserler_data():
    """eserler.json'dan veri yükle, slug ile indexle"""
    if not DATA_FILE.exists():
        return {}

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)

    # Slug ile indexle
    indexed = {}
    for item in items:
        title = item.get('title', '')
        # Basit slug oluştur
        slug = title.lower()
        for old, new in {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', ' ': '-'}.items():
            slug = slug.replace(old, new)
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        indexed[slug] = item

    return indexed


def fix_file(filepath, eserler_data, dry_run=False):
    """Tek bir dosyayı düzelt"""
    changes = []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    if not fm:
        return []

    original_fm = fm.copy()

    # 1. Title düzelt
    if 'title' in fm:
        old_title = fm['title']
        new_title = re.sub(r'\s*\|\s*Miras Haritası\s*$', '', old_title, flags=re.IGNORECASE)
        if old_title != new_title:
            fm['title'] = new_title
            changes.append(f"Title: '{old_title}' -> '{new_title}'")

    # 2. Province/District düzelt
    province = fm.get('province', '')
    district = fm.get('district', '')
    new_province, new_district = fix_province_district(province, district)

    if province != new_province:
        fm['province'] = new_province
        fm['iller'] = f'["{new_province}"]' if new_province else '[""]'
        changes.append(f"Province: '{province}' -> '{new_province}'")

    if district != new_district:
        fm['district'] = new_district
        if 'ilceler' in fm:
            fm['ilceler'] = f'["{new_district}"]' if new_district else '[""]'
        changes.append(f"District: '{district}' -> '{new_district}'")

    # 3. Eksik featured_image düzelt
    featured_image = fm.get('featured_image', '')
    if not featured_image or featured_image == '""':
        # eserler.json'dan bulmaya çalış
        slug = filepath.stem
        if slug in eserler_data:
            item = eserler_data[slug]
            if item.get('image_filename'):
                new_image = get_commons_thumb_url(item['image_filename'])
                fm['featured_image'] = new_image
                if 'image' not in fm or not fm.get('image'):
                    fm['image'] = new_image
                changes.append(f"Image: Added from eserler.json")

    # Değişiklik varsa kaydet
    if changes and not dry_run:
        new_fm_text = create_frontmatter_text(fm)
        new_content = new_fm_text + body

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return changes


def main():
    parser = argparse.ArgumentParser(description="Mevcut içerik düzeltici")
    parser.add_argument("--dry-run", action="store_true", help="Değişiklik yapmadan sadece kontrol et")
    parser.add_argument("--limit", type=int, help="İşlenecek maksimum dosya sayısı")
    args = parser.parse_args()

    print("\nMiras Haritası - Mevcut İçerik Düzeltici")
    print("=" * 50)

    if args.dry_run:
        print("MOD: Dry-run (değişiklik yapılmayacak)")
    else:
        print("MOD: Aktif (değişiklikler uygulanacak)")

    print("\n1. eserler.json yükleniyor...")
    eserler_data = load_eserler_data()
    print(f"   {len(eserler_data)} kayıt yüklendi")

    print("\n2. İçerik dosyaları taranıyor...")
    files = list(CONTENT_DIR.glob("*.md"))
    if args.limit:
        files = files[:args.limit]
    print(f"   {len(files)} dosya bulundu")

    stats = {
        "processed": 0,
        "modified": 0,
        "title_fixed": 0,
        "province_fixed": 0,
        "image_fixed": 0
    }

    print("\n3. Düzeltmeler uygulanıyor...")
    for filepath in tqdm(files, desc="İşleniyor"):
        changes = fix_file(filepath, eserler_data, dry_run=args.dry_run)
        stats["processed"] += 1

        if changes:
            stats["modified"] += 1
            for change in changes:
                if "Title" in change:
                    stats["title_fixed"] += 1
                if "Province" in change or "District" in change:
                    stats["province_fixed"] += 1
                if "Image" in change:
                    stats["image_fixed"] += 1

    print("\n" + "=" * 50)
    print("SONUÇLAR:")
    print(f"  İşlenen dosya: {stats['processed']}")
    print(f"  Değiştirilen: {stats['modified']}")
    print(f"  Title düzeltmesi: {stats['title_fixed']}")
    print(f"  Province/District düzeltmesi: {stats['province_fixed']}")
    print(f"  Görsel eklenen: {stats['image_fixed']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
