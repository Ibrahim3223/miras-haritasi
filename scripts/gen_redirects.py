import os, re
from collections import Counter

def tr_lower(text):
    # Turkish-aware lowercase: İ→i, I→i
    text = text.replace('İ', 'i').replace('I', 'i')
    text = text.lower()
    # Remove combining dot above (U+0307) that Python adds when lowercasing İ
    text = text.replace('i\u0307', 'i')
    return text

def hugo_slug(text):
    text = tr_lower(text)
    text = re.sub(r'[\s_]+', '-', text)
    # Remove chars that aren't word chars, Turkish-extended, or hyphens
    text = re.sub(r'[^\w\u00c0-\u017e-]', '', text, flags=re.UNICODE)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

# Map non-standard province name (lowercase) → modern province slug
province_map = {
    # Istanbul districts
    'fatih': 'istanbul',
    'beyoğlu': 'istanbul',
    'üsküdar': 'istanbul',
    'beşiktaş': 'istanbul',
    'eyüpsultan': 'istanbul',
    'kadıköy': 'istanbul',
    'sarıyer': 'istanbul',
    'beykoz': 'istanbul',
    'bakırköy': 'istanbul',
    'istanbul vilayeti': 'istanbul',
    'adalar': 'istanbul',
    'şişli': 'istanbul',
    'zeytinburnu': 'istanbul',
    'büyükçekmece': 'istanbul',
    'ataşehir': 'istanbul',
    'şile': 'istanbul',
    'kağıthane': 'istanbul',
    'arnavutköy': 'istanbul',
    'silivri (ilçe)': 'istanbul',
    'küçükçekmece': 'istanbul',
    'sancaktepe': 'istanbul',
    'esenyurt': 'istanbul',
    'bahçelievler': 'istanbul',
    'avcılar': 'istanbul',
    'kartal': 'istanbul',
    'maltepe': 'istanbul',
    'tuzla': 'istanbul',
    'ümraniye': 'istanbul',
    'çatalca': 'istanbul',
    'esenler': 'istanbul',
    # Ankara districts
    'altındağ': 'ankara',
    'ankara vilayeti': 'ankara',
    'etimesgut': 'ankara',
    'çankaya': 'ankara',
    'polatlı': 'ankara',
    'kahramankazan': 'ankara',
    'haymana i̇lçesi': 'ankara',
    # Çanakkale
    'eceabat ilçesi': 'canakkale',
    'eceabat': 'canakkale',
    'çanakkale (ilçe)': 'canakkale',
    'ezine': 'canakkale',
    'ayvacık (çanakkale ilçesi)': 'canakkale',
    'bayramiç (ilçe)': 'canakkale',
    # Trabzon
    'trabzon vilayeti': 'trabzon',
    'trabzon eyaleti': 'trabzon',
    'çaykara i̇lçesi': 'trabzon',
    'of (ilçe)': 'trabzon',
    # Aydın
    'aydın vilayeti': 'aydin',
    'söke i̇lçesi': 'aydin',
    'kuşadası': 'aydin',
    'germencik (ilçe)': 'aydin',
    'karacasu (ilçe)': 'aydin',
    'bozdoğan': 'aydin',
    # Artvin
    'şavşat': 'artvin',
    'ardanuç': 'artvin',
    'borçka': 'artvin',
    'yusufeli': 'artvin',
    'murgul': 'artvin',
    'borçka ilçesi': 'artvin',
    'arhavi ilçesi': 'artvin',
    'hopa': 'artvin',
    'artvin i̇lçesi': 'artvin',
    # Erzurum
    'erzurum vilayeti': 'erzurum',
    'erzurum eyaleti': 'erzurum',
    'tortum ilçesi': 'erzurum',
    'oltu': 'erzurum',
    'olur': 'erzurum',
    'uzundere': 'erzurum',
    'i̇spir': 'erzurum',
    'şenkaya i̇lçesi': 'erzurum',
    'yakutiye': 'erzurum',
    # Ardahan
    'çıldır': 'ardahan',
    'posof': 'ardahan',
    'hanak': 'ardahan',
    'göle': 'ardahan',
    'göle i̇lçesi': 'ardahan',
    # Kars
    'kars oblasti': 'kars',
    'kars eyaleti': 'kars',
    'arpaçay': 'kars',
    'digor': 'kars',
    # İzmir
    'menemen (ilçe)': 'izmir',
    'konak (ilçe)': 'izmir',
    'bergama (ilçe)': 'izmir',
    'foça': 'izmir',
    'dikili (ilçe)': 'izmir',
    'ödemiş': 'izmir',
    'tire (ilçe)': 'izmir',
    'alaşehir (ilçe)': 'izmir',
    # Amasya
    'merzifon i̇lçesi': 'amasya',
    # Balıkesir
    'burhaniye (ilçe)': 'balikesir',
    'edremit (balıkesir) ilçesi': 'balikesir',
    'bandırma': 'balikesir',
    'erdek ilçesi': 'balikesir',
    'ayvalık (ilçe)': 'balikesir',
    'yenipazar': 'balikesir',
    # Antalya
    'kaş ilçesi': 'antalya',
    'manavgat (ilçe)': 'antalya',
    'akseki (ilçe)': 'antalya',
    'kemer district (antalya)': 'antalya',
    'finike': 'antalya',
    'serik': 'antalya',
    'demre': 'antalya',
    'konyaaltı': 'antalya',
    # Muğla
    'bodrum': 'mugla',
    'seydikemer': 'mugla',
    'milas': 'mugla',
    'dalaman': 'mugla',
    'marmaris (ilçe)': 'mugla',
    'ortaca (ilçe)': 'mugla',
    'menteşe': 'mugla',
    # Bursa
    'orhangazi (ilçe)': 'bursa',
    'hüdavendigâr vilayeti': 'bursa',
    'mudanya': 'bursa',
    'yıldırım': 'bursa',
    'i̇znik (ilçe)': 'bursa',
    'i̇znik': 'bursa',
    'karacabey ilçesi': 'bursa',
    # Manisa
    'akhisar (ilçe)': 'manisa',
    'salihli': 'manisa',
    'kula (ilçe)': 'manisa',
    'saruhanl\u0131 (ilçe)': 'manisa',
    # Hatay
    'i̇skenderun sancağı': 'hatay',
    'antakya ilçesi': 'hatay',
    'samandağ': 'hatay',
    'altınözü (ilçe)': 'hatay',
    # Samsun
    'i̇lkadım': 'samsun',
    # Mersin
    'silifke (ilçe)': 'mersin',
    'tarsus (ilçe)': 'mersin',
    'erdemli': 'mersin',
    # Elazığ
    'mamuret-ul-aziz vilayeti': 'elazig',
    # Nevşehir
    'avanos': 'nevsehir',
    'ürgüp': 'nevsehir',
    'gülşehir': 'nevsehir',
    # Tekirdağ
    'süleymanpaşa': 'tekirdag',
    'malkara': 'tekirdag',
    # Edirne
    'edirne vilayeti': 'edirne',
    'edirne (ilçe)': 'edirne',
    # Sivas
    'divriği': 'sivas',
    'hafik': 'sivas',
    'kangal': 'sivas',
    'zara': 'sivas',
    # Konya
    'selçuklu': 'konya',
    'yunak': 'konya',
    'seydişehir': 'konya',
    'akşehir (ilçe)': 'konya',
    'bozkır': 'konya',
    'meram': 'konya',
    'konya vilayeti': 'konya',
    # Kayseri
    'melikgazi': 'kayseri',
    'kocasinan': 'kayseri',
    # Bitlis
    'bitlis vilayeti': 'bitlis',
    'tatvan': 'bitlis',
    'hizan': 'bitlis',
    # Van
    'van vilayeti': 'van',
    'van eyaleti': 'van',
    'bahçesaray': 'van',
    'gevaş': 'van',
    'erciş district': 'van',
    # Kırşehir
    'kaman (ilçe)': 'kirsehir',
    # Adana
    'adana vilayeti': 'adana',
    'seyhan': 'adana',
    'karataş': 'adana',
    'aladağ': 'adana',
    # Mardin
    'midyat': 'mardin',
    # Diyarbakır
    'çüngüş': 'diyarbakir',
    'çınar': 'diyarbakir',
    'yenişehir (diyarbakır)': 'diyarbakir',
    # Tokat
    'erbaa': 'tokat',
    # Çorum
    'sungurlu': 'corum',
    'boğazkale': 'corum',
    # Kastamonu
    'kargı': 'kastamonu',
    # Sakarya
    'erenler': 'sakarya',
    # Kocaeli
    'i̇zmit (ilçe)': 'kocaeli',
    # Yalova
    'altınova': 'yalova',
    # Bayburt
    'demirözü': 'bayburt',
    # Karabük
    'eflani': 'karabuk',
    # Aksaray
    'eskil': 'aksaray',
    # Kahramanmaraş
    'onikişubat': 'kahramanmaras',
    # Afyonkarahisar
    'dinar ilçesi': 'afyonkarahisar',
    'dinar': 'afyonkarahisar',
    'i̇hsaniye': 'afyonkarahisar',
    'emirdağ': 'afyonkarahisar',
    # Denizli
    'çivril': 'denizli',
    'çal': 'denizli',
    # Isparta
    'yalvaç': 'isparta',
    # Burdur
    'bucak': 'burdur',
    # Gaziantep
    'gaziantep alt bölgesi': 'gaziantep',
    'antep sancağı': 'gaziantep',
    # Kütahya
    'altıntaş': 'kutahya',
    # Şanlıurfa
    'karaköprü': 'sanliurfa',
    # Kırklareli
    'vize': 'kirklareli',
    # Ağrı
    'taşlıçay': 'agri',
    # Tunceli
    'hozat': 'tunceli',
    # Bolu
    'kocaköy': 'bolu',
    # Ordu
    'ünye': 'ordu',
    # Rize
    'kalkandere': 'rize',
    # Çankırı
    'orta (ilçe)': 'cankiri',
    # Bartın
    'amasra i̇lçesi': 'bartin',
    # More Istanbul
    'istanbul vilayeti': 'istanbul',
    # Kars
    'kars oblasti': 'kars',
    # Hatay
    'antakya ilcesi': 'hatay',
    'antakya ilçesi': 'hatay',
    # Generic/foreign/historical/ambiguous → /iller/
    'i̇yonya': None,
    'kilikya': None,
    'anadolu eyaleti': None,
    'marmara bölgesi': None,
    'akdeniz bölgesi': None,
    'güneydoğu anadolu bölgesi': None,
    'iç anadolu bölgesi': None,
    'fransız suriye ve lübnan mandası': None,
    'halep vilayeti': None,
    'halep sancağı': None,
    'kutaisi guberniyası': None,
    'türkiye': None,
    'turkiye': None,
    'çıldır eyaleti': 'ardahan',
    'cildir eyaleti': 'ardahan',
    'batum oblasti': None,
    'batum oblastı': None,
    'kars oblastı': 'kars',
    'iç anadolu bölgesi': None,
    'ortaköy': None,
    'sürmeli uyezdi': None,
    'mezopotamya (roma eyaleti)': None,
    'part i̇mparatorluğu': None,
    'dioecesis asiana': None,
    'misya': None,
    'çamlıbel': None,
    'ermenistan demokratik cumhuriyeti': None,
}

import json

# Read province values from BOTH md files AND data/eserler.json for full coverage
provinces = Counter()
content_dir = 'content/eserler'
for fname in os.listdir(content_dir):
    if not fname.endswith('.md') or fname == '_index.md':
        continue
    fpath = os.path.join(content_dir, fname)
    with open(fpath, encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'^province:\s*["\']?(.*?)["\']?\s*$', text, re.MULTILINE)
    if m:
        val = m.group(1).strip().strip('"\'')
        if val:
            provinces[val] += 1

# Also include values from data/eserler.json (historical values, may be already corrected)
with open('data/eserler.json', encoding='utf-8') as f:
    data = json.load(f)
for item in data:
    p = item.get('province', '')
    if p and p not in provinces:
        provinces[p] = 0  # Add with 0 count if not already present

standard_tr = {
    'Adana','Adıyaman','Afyonkarahisar','Ağrı','Amasya','Ankara','Antalya','Artvin',
    'Aydın','Balıkesir','Bilecik','Bingöl','Bitlis','Bolu','Burdur','Bursa',
    'Çanakkale','Çankırı','Çorum','Denizli','Diyarbakır','Edirne','Elazığ','Erzincan',
    'Erzurum','Eskişehir','Gaziantep','Giresun','Gümüşhane','Hakkari','Hatay','Isparta',
    'Mersin','İstanbul','İzmir','Kars','Kastamonu','Kayseri','Kırklareli','Kırşehir',
    'Kocaeli','Konya','Kütahya','Malatya','Manisa','Kahramanmaraş','Mardin','Muğla',
    'Muş','Nevşehir','Niğde','Ordu','Rize','Sakarya','Samsun','Siirt','Sinop','Sivas',
    'Tekirdağ','Tokat','Trabzon','Tunceli','Şanlıurfa','Uşak','Van','Yozgat','Zonguldak',
    'Aksaray','Bayburt','Karaman','Kırıkkale','Batman','Şırnak','Bartın','Ardahan',
    'Iğdır','Yalova','Karabük','Kilis','Osmaniye','Düzce',
}

print('# Otomatik: Ilce/tarihi vilayet -> modern il yonlendirmeleri')
print()

missing = []
# Normalize all map keys the same way as lookup keys
normalized_map = {tr_lower(k): v for k, v in province_map.items()}

for p, c in provinces.most_common():
    if p in standard_tr:
        continue
    pkey = tr_lower(p)
    if pkey in normalized_map:
        target = normalized_map[pkey]
        dest = f'/iller/{target}/' if target else '/iller/'
        slug = hugo_slug(p)
        print(f'/iller/{slug}/  {dest}  301')
    else:
        missing.append((p, c))

if missing:
    print()
    print('# UNMAPPED (need manual review):')
    for p, c in missing:
        print(f'# {c:3d}  {p}  [slug: {hugo_slug(p)}]')
