# API Anahtarları Rehberi

Bu rehber, multi-source image search scriptini kullanmak için gerekli API anahtarlarını nasıl alacağınızı açıklar.

## 1. Unsplash API (ÖNERİLEN)

**Avantajlar:**
- Yüksek kaliteli, profesyonel fotoğraflar
- Ücretsiz tier: 50 istek/saat
- API kullanımı kolay

**Nasıl Alınır:**
1. https://unsplash.com/developers adresine gidin
2. "Register as a developer" butonuna tıklayın
3. Uygulamanız için bir isim verin (örn: "Miras Haritası")
4. Access Key'inizi kopyalayın

**Kullanım:**
```bash
set UNSPLASH_API_KEY=your_access_key_here
```

---

## 2. Pexels API

**Avantajlar:**
- Ücretsiz stok fotoğraflar
- Sınırsız istek
- Telif hakkı sorunu yok

**Nasıl Alınır:**
1. https://www.pexels.com/api/ adresine gidin
2. "Get Started" butonuna tıklayın
3. Email ile kayıt olun
4. API Key'inizi kopyalayın

**Kullanım:**
```bash
set PEXELS_API_KEY=your_api_key_here
```

---

## 3. Pixabay API

**Avantajlar:**
- Geniş görsel koleksiyonu
- Ücretsiz tier: 5000 istek/ay
- Türkçe içerik bulma şansı yüksek

**Nasıl Alınır:**
1. https://pixabay.com/api/docs/ adresine gidin
2. Ücretsiz hesap oluşturun
3. API key'inizi alın

**Kullanım:**
```bash
set PIXABAY_API_KEY=your_api_key_here
```

---

## Hızlı Başlangıç

### Windows:
```bash
# API anahtarlarını ayarlayın
set UNSPLASH_API_KEY=your_unsplash_key
set PEXELS_API_KEY=your_pexels_key
set PIXABAY_API_KEY=your_pixabay_key

# Script'i çalıştırın
python scripts/multi_source_image_search.py
```

### Linux/Mac:
```bash
# API anahtarlarını ayarlayın
export UNSPLASH_API_KEY=your_unsplash_key
export PEXELS_API_KEY=your_pexels_key
export PIXABAY_API_KEY=your_pixabay_key

# Script'i çalıştırın
python scripts/multi_source_image_search.py
```

---

## Alternatif: .env Dosyası

Script'te doğrudan API anahtarlarını da girebilirsiniz:

`scripts/multi_source_image_search.py` dosyasını açın ve şu satırları düzenleyin:

```python
API_KEYS = {
    'unsplash': 'your_unsplash_access_key',
    'pexels': 'your_pexels_api_key',
    'pixabay': 'your_pixabay_api_key',
}
```

---

## Önerilen Strateji

1. **İlk önce Unsplash** - En kaliteli görseller burada
2. **Sonra Pexels** - Sınırsız istek imkanı
3. **Son olarak Pixabay** - Geniş koleksiyon

Script otomatik olarak bu sırayla arama yapar ve ilk bulduğu görseli kullanır.

---

## Beklenen Sonuçlar

- **Unsplash:** %30-40 başarı oranı (mimari yapılar için)
- **Pexels:** %25-35 başarı oranı
- **Pixabay:** %20-30 başarı oranı
- **Toplam:** %50-60 kapsama şansı

Wikimedia (%14) + Multi-source (%50) = **~%64 toplam kapsama** hedeflenebilir.
