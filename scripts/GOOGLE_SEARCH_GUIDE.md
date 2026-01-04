# Google Custom Search - Kurulum ve Kullanım Rehberi

## 🎯 Sistemin Avantajları

✅ **Güvenilir Kaynaklar:** .gov.tr, müzeler, Wikipedia'ya öncelik verir
✅ **Doğrulama Sistemi:** Her görsel için güven skoru hesaplar
✅ **Manuel Review:** Düşük skorlu görseller manuel onay bekler
✅ **Kaynak Takibi:** Her görselin kaynağını ve metadatasını saklar
✅ **Yanlış Görsel Koruması:** Alakasız görselleri filtreler

---

## 📝 1. Adım: Google API Key Alma

### A) Google Cloud Console'a Git
1. https://console.cloud.google.com/ adresine git
2. Gmail hesabınla giriş yap
3. Ücretsiz deneme başlat (kredi kartı gerekli ama ücret alınmaz)

### B) Yeni Proje Oluştur
1. Üst menüden "Select a project" → "New Project"
2. Proje adı: "Miras Haritası"
3. "Create" tıkla

### C) Custom Search API'yi Aktifleştir
1. Sol menüden "APIs & Services" → "Library"
2. "Custom Search API" ara
3. "Enable" tıkla

### D) API Key Oluştur
1. "APIs & Services" → "Credentials"
2. "+ CREATE CREDENTIALS" → "API key"
3. API key'ini kopyala
4. (Opsiyonel) "Restrict key" ile sadece Custom Search API'ye izin ver

**API Key Örneği:**
```
AIzaSyABC123XYZ789_your_api_key_here
```

---

## 🔍 2. Adım: Custom Search Engine (CX) Oluşturma

### A) Programmable Search Engine'e Git
1. https://programmablesearchengine.google.com/
2. "Get Started" → "Add" tıkla

### B) Search Engine Ayarları
**Temel Ayarlar:**
- **Name:** Miras Haritası Image Search
- **What to search:** Search the entire web
- **SafeSearch:** Off

**Gelişmiş Ayarlar (Önemli!):**
1. "Sites to search" → "Search the entire web"
2. "Preferred Sites" ekle (yüksek öncelik):
   ```
   *.gov.tr
   muze.gov.tr
   kulturportali.gov.tr
   ktb.gov.tr
   tr.wikipedia.org
   commons.wikimedia.org
   ```

3. **Image Search:** ON (çok önemli!)
4. **Language:** Turkish + English

### C) Search Engine ID (CX) Al
1. "Overview" sekmesine git
2. "Search engine ID" altındaki kodu kopyala

**CX Örneği:**
```
a1b2c3d4e5f6g7h8i
```

---

## ⚙️ 3. Adım: API'yi Yapılandırma

### Windows:
```cmd
# Geçici (bu oturum için)
set GOOGLE_API_KEY=AIzaSyABC123XYZ789_your_api_key_here
set GOOGLE_CX=a1b2c3d4e5f6g7h8i

# Kalıcı (her zaman)
setx GOOGLE_API_KEY "AIzaSyABC123XYZ789_your_api_key_here"
setx GOOGLE_CX "a1b2c3d4e5f6g7h8i"
```

### Linux/Mac:
```bash
export GOOGLE_API_KEY="AIzaSyABC123XYZ789_your_api_key_here"
export GOOGLE_CX="a1b2c3d4e5f6g7h8i"

# .bashrc veya .zshrc'ye ekle (kalıcı)
echo 'export GOOGLE_API_KEY="your_key"' >> ~/.bashrc
echo 'export GOOGLE_CX="your_cx"' >> ~/.bashrc
```

---

## 🚀 4. Adım: Script'i Çalıştırma

### İlk Arama (50-100 dosya önerilir)
```bash
python scripts/google_image_search.py
```

**Script Size Soracak:**
1. Kaç dosya işlensin? → **50** (günlük limit: 100)
2. Auto-approve threshold? → **75** (0-100 arası)

**Threshold Açıklaması:**
- **80+**: Çok güvenilir → Otomatik onaylanır
- **60-79**: Orta güvenilir → Manuel review gerekir
- **<60**: Düşük güvenilir → Manuel review gerekir

### Sonuçlar
```
RESULTS:
  Processed: 50
  Images found: 35 (70%)
  Auto-approved (≥75%): 28
  Needs review (<75%): 7
  Not found: 15
```

---

## 🔍 5. Adım: Manuel Review

Düşük skorlu görselleri incele:

```bash
python scripts/review_images.py
```

**Review Ekranı:**
```
📍 Heritage Site:
   Title: Aspendos Liman Hamamı
   Province: Antalya
   Type: Hamam

🖼️  Proposed Image:
   URL: https://example.com/image.jpg
   Source: https://kulturportali.gov.tr/...
   Domain: kulturportali.gov.tr

📊 Confidence Analysis:
   Score: 72/100
   Reasons:
     • Semi-trusted source: kulturportali.gov.tr
     • Good title/snippet match (3/3 terms)

👉 Your decision [a/r/s/o/q]:
```

**Komutlar:**
- **[a]** Approve - Görseli onayla ve ekle
- **[r]** Reject - Görseli reddet
- **[s]** Skip - Şimdilik geç, sonra incele
- **[o]** Open - Görseli ve kaynağı tarayıcıda aç
- **[q]** Quit - Kaydet ve çık

---

## 📊 Güven Skoru Sistemi

### Skor Hesaplama:

**Base Score:** 50

**Bonus (+):**
- Trusted domain (.gov.tr, wikipedia): **+30**
- Semi-trusted domain: **+15**
- Title/snippet match (70%+): **+15**
- Title/snippet match (50%+): **+10**
- Image from trusted context: **+10**

**Penalty (-):**
- No Turkish indicators: **-10**

**Maksimum Skor:** 100

### Örnek Skorlar:

**95/100 - Çok Güvenilir:**
```
Source: muze.gov.tr
Match: 100% (tüm kelimeler eşleşti)
Context: Türkiye Müzeleri
→ OTOMATİK ONAYLA
```

**72/100 - Orta Güvenilir:**
```
Source: kulturportali.gov.tr
Match: 75% (3/4 kelime)
Context: Kültür Portalı
→ MANUEL İNCELE
```

**45/100 - Düşük Güvenilir:**
```
Source: randomsite.com
Match: 25% (1/4 kelime)
No Turkish context
→ MANUEL İNCELE veya REDDET
```

---

## 💡 En İyi Uygulamalar

### 1. Günlük Kullanım
```bash
# Her gün 100 dosya işle (API limit)
python scripts/google_image_search.py
# Input: 100

# Düşük skorluları incele
python scripts/review_images.py
```

### 2. İlk Hafta Stratejisi
- **Gün 1-3:** Threshold: 80 (sadece çok güvenilirleri al)
- **Gün 4-7:** Threshold: 75 (orta güvenilirleri de ekle)
- **Gün 8+:** Threshold: 70 (daha fazla kapsam)

### 3. Review Stratejisi
- Önce [o] ile görseli aç, kontrol et
- Görsel doğruysa [a] ile onayla
- Şüpheliyse [r] ile reddet
- Emin değilsen [s] ile sonraya bırak

---

## 📈 Beklenen Sonuçlar

| Kaynak | Başarı Oranı | Güven Skoru |
|--------|--------------|-------------|
| gov.tr siteleri | %60-70 | 85-95 |
| Wikipedia | %50-60 | 80-90 |
| Kültür siteleri | %40-50 | 70-80 |
| Genel web | %20-30 | 50-70 |

**Genel Beklenti:**
- **Bulunma oranı:** %50-60
- **Otomatik onay:** %70-80 (threshold: 75)
- **Manuel review:** %20-30
- **Nihai kapsam:** %40-50 (wiki %20 + google %30)

---

## ⚠️ Önemli Notlar

### Limitler
- **Günlük:** 100 arama/gün (ücretsiz)
- **Her arama:** Maksimum 5 sonuç
- **Rate limiting:** 1 saniye bekleme

### Maliyetler
- **İlk 100 arama/gün:** ÜCRETSİZ
- **100+:** $5 / 1000 arama
- **Tavsiye:** Günlük 100'le kal

### Veri Yönetimi
- **Progress:** `scripts/google_search_progress.json`
- **Review Queue:** `scripts/needs_review.json`
- **Her 10 dosyada bir otomatik kayıt**

---

## 🔧 Sorun Giderme

### "API credentials not configured"
```bash
# API key ve CX'i kontrol et
echo %GOOGLE_API_KEY%
echo %GOOGLE_CX%

# Yeniden ayarla
set GOOGLE_API_KEY=your_key
set GOOGLE_CX=your_cx
```

### "API rate limit reached"
- Yarın tekrar dene (günlük 100 limit)
- Veya ücretli plana geç

### "No results found"
- Custom Search Engine ayarlarını kontrol et
- "Image search" aktif mi?
- "Preferred sites" doğru mu?

---

## 🎉 Başarı Kriterleri

✅ **İyi bir sonuç:**
- %50+ bulma oranı
- %80+ otomatik onay
- %20- manuel review

✅ **Mükemmel bir sonuç:**
- %60+ bulma oranı
- %85+ otomatik onay
- %15- manuel review

**Hedefiniz:**
- Wikimedia: %20 kapsam
- Google Search: %30 kapsam
- **TOPLAM: %50 görsel kapsamı** ✨
