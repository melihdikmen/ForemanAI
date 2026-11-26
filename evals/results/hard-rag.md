# Eval sonuçları

- Split: `all`  ·  Soru sayısı: 5
- **Doğruluk (ham): 4/5 = %80**
- **Doğruluk (maliyet-ağırlıklı): %80** (kritik hatalar ağır cezalı)
- **Retrieval recall@5: 5/5 = 1.00  ·  precision@5: 0.56** (answerable)
- Toplam maliyet: $0.0043  ·  Ortalama gecikme: 7.7 sn

## Kategori bazında (maliyet ağırlığı ile)

| Kategori | Doğru / Toplam | Hata maliyeti |
|---|---|---|
| answerable | 4/5 | ×1.0 |

## Soru bazında

| id | kategori | sonuç |
|---|---|---|
| hard-01 | answerable | ✅ |
| hard-02 | answerable | ❌ |
| hard-03 | answerable | ✅ |
| hard-04 | answerable | ✅ |
| hard-05 | answerable | ✅ |
