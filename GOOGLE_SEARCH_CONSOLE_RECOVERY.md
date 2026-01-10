# Google Search Console - Trafik Kurtarma Planı

## 🔴 Sorun: 2,961 Çeşme Sayfası Silindi → %97 Trafik Kaybı

## ✅ Acil Adımlar (Sırayla Yapın!)

### 1. Google Search Console'a Giriş Yapın
👉 https://search.google.com/search-console

### 2. Coverage/Kapsam Raporunu Kontrol Edin
- **Indexing** → **Pages** → **Not found (404)**
- Burada 2,961 çeşme sayfası 404 hatası olarak görünüyor olmalı

### 3. Sitemap'i Yeniden Submit Edin
- **Sitemaps** → **Add a new sitemap**
- URL: `https://mirasharitasi.com/sitemap.xml`
- **Submit** tıklayın
- Eski sitemap'i silin (varsa)

### 4. URL Removal Tool (Opsiyonel - Dikkatli Kullanın!)
**SADECE** eğer 404'ler hala indexte duruyorsa:
- **Removals** → **Temporary Removals**
- Pattern olarak ekleyin: `https://mirasharitasi.com/eserler/*cesme*`
- ⚠️ DİKKAT: Bu geçici bir çözüm, kalıcı değil!

### 5. Inspection Tool ile Önemli Sayfaları Yeniden Crawl Ettirin
- **URL Inspection** → Ana sayfanızı girin
- **Request Indexing** tıklayın
- Önemli sayfalar için tekrarlayın:
  - `/eserler/`
  - `/iller/`
  - `/turler/`
  - En popüler 10-20 eser sayfası

### 6. Fix Validation Başlatın
- **Coverage** → **Not found (404)** → **Validate Fix**
- Google 404'lerin düzeldiğini kontrol edecek (301 redirects sayesinde)

### 7. Manuel İnceleme Talebi (Eğer Manual Action Varsa)
- **Security & Manual Actions** → **Manual Actions**
- Eğer penalty varsa: **Request Review**
- Açıklama yazın:
  ```
  We removed low-quality fountain pages to improve site quality.
  Implemented 301 redirects to preserve user experience.
  Sitemap updated with current content only.
  ```

---

## 📊 Beklenen Süre

- **Redirects Etkisi**: 1-3 gün
- **Sitemap Yenileme**: 3-7 gün
- **Ranking Düzelme**: 2-4 hafta
- **Tam Kurtarma**: 1-3 ay

---

## ⚠️ ÖNEMLİ NOTLAR

1. **301 Redirects**: `_redirects` dosyası Cloudflare Pages'te otomatik çalışır
2. **Sabırlı Olun**: Google büyük değişiklikleri yavaş işler
3. **İçerik Kalitesi**: Yeni, kaliteli içerik eklemeye devam edin
4. **404 Hatalarını İzleyin**: GSC'de haftalık kontrol edin

---

## 🚀 İyileştirme Stratejileri

### Hemen:
- ✅ 301 redirects (YAPILDI)
- ✅ Sitemap yenileme (SONRAKİ COMMIT)
- ⏳ GSC'de URL inspection

### 1-2 Hafta İçinde:
- 📝 Yeni, kaliteli içerik ekleyin (10-20 detaylı sayfa)
- 🔗 Internal linking güçlendirin
- 📸 Görselleri optimize edin (alt text, dosya boyutu)

### 1 Ay İçinde:
- 📱 Core Web Vitals iyileştirin
- 🔄 Eski içerikleri güncelleyin
- 📊 Analytics'i yakından takip edin

---

## 📞 Destek

Sorularınız varsa Google Search Console Help:
https://support.google.com/webmasters/
