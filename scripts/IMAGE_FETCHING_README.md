# Görsel Ekleme Sistemi - Kullanım Kılavuzu

## 📸 Mevcut Durum
- **Toplam dosya:** 15,640
- **Görselli:** 2,930 (18.7%)
- **Görselsiz:** 12,710 (81.3%)
- **Hedef:** 12,500+ görsel (80% kapsam)

## 🚀 3 Katmanlı Sistem

### 1. sync_images_from_json.py ⚡ (Hızlı - Önce Bunu Çalıştır)
**Ne yapar:** eserler.json'dan markdown dosyalara görsel kopyalar

```bash
cd "c:/Users/Dante/Desktop/Yeniden/WebSite/miras-haritası"
python scripts/sync_images_from_json.py
```

**Özellikler:**
- Çok hızlı (saniyeler)
- Max 3,659 görsel
- Zaten çalıştırıldı (2,930 görsel eklendi)

**Ne zaman kullan:** İlk adım olarak

---

### 2. wikimedia_image_search.py ⭐ (Orta - ÖNERİLEN)
**Ne yapar:** Wikimedia Commons'dan başlık ile görsel arar

```bash
cd "c:/Users/Dante/Desktop/Yeniden/WebSite/miras-haritası"
python scripts/wikimedia_image_search.py
```

**Özellikler:**
- Orta hız (50-200 dosya/çalıştırma)
- Akıllı arama (multiple strategies)
- Başarı oranı: %15-30
- Progress kaydedilir
- Rate limit: 2 req/sec

**Kullanım:**
1. Script'i çalıştır
2. Kaç dosya işlensin? (önerilen: 100)
3. Bekle
4. Tekrar çalıştır (progress kaydedilir)

**Strateji:**
- Her gün 200 dosya işle
- ~60 gün içinde tamamlanır
- Her run ~2-3 dakika

---

### 3. wikidata_image_fetcher.py 🎯 (Yavaş - Ünlü Eserler İçin)
**Ne yapar:** Wikidata SPARQL query ile görsel bulur

```bash
cd "c:/Users/Dante/Desktop/Yeniden/WebSite/miras-haritası"
python scripts/wikidata_image_fetcher.py
```

**Özellikler:**
- En yavaş
- En doğru
- Koordinat bazlı arama da var
- Ünlü eserler için ideal
- Rate limit: 1.1 req/sec

**Ne zaman kullan:**
- Wikimedia Commons search sonrası
- Ünlü/önemli eserler için
- Daha yüksek kalite gerektiren durumlar

---

## 📊 Tahmini Sonuç

**Wikimedia Search ile (önerilen):**
- Batch size: 100
- Success rate: 20%
- Her run: 20 görsel
- Hedef için gereken run: ~500
- Günde 2 run × 60 gün = **hedef tamamlanır**

**Otomatik Batch:**
```python
# 500 dosya işle (bir seferde)
while True:
    python scripts/wikimedia_image_search.py
    # Input: 100
    # Wait 2-3 mins
    # Repeat
```

---

## 🔄 Önerilen Workflow

1. **İlk adım** (yapıldı ✅)
   ```bash
   python scripts/sync_images_from_json.py
   ```
   Sonuç: 2,930 görsel

2. **Ana strateji** (her gün)
   ```bash
   python scripts/wikimedia_image_search.py
   # Input: 200
   ```
   Her run: ~30-60 görsel

3. **Son rötuş** (opsiyonel)
   ```bash
   python scripts/wikidata_image_fetcher.py
   # Input: 50
   ```
   Kalan önemli eserler için

---

## 💡 İpuçları

- Progress dosyaları: `scripts/*_progress.json`
- Her run'dan sonra git commit gerekli değil
- Toplu commit yapabilirsiniz
- Wikimedia rate limit'e dikkat
- Network hatası olursa tekrar çalıştır (progress kaydedilir)

---

## 🎯 Hedef Takibi

```bash
# Mevcut durumu kontrol et
grep -l 'featured_image: ""' content/eserler/*.md | wc -l
```

**Milestone'lar:**
- ✅ 2,930 (18.7%) - Başlangıç
- 🎯 5,000 (32%) - İlk milestone
- 🎯 8,000 (51%) - Yarı yol
- 🎯 12,500 (80%) - HEDEF

---

## ⚠️ Notlar

- Wikimedia Commons'da olmayan eserlere görsel bulunamaz
- Bazı eserler için manuel ekleme gerekebilir
- Quality over quantity - yanlış görsel eklemekten iyidir hiç eklememek

---

**Hazırlayan:** Claude Code
**Tarih:** 2026-01-03
