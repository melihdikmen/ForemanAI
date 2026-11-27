# Eval sonuçları

- Split: `heldout`  ·  Soru sayısı: 10
- **Doğruluk (ham): 8/10 = %80**
- **Doğruluk (maliyet-ağırlıklı): %69** (kritik hatalar ağır cezalı)
- **Retrieval recall@5: 6/6 = 1.00  ·  precision@5: 0.87** (answerable)
- Toplam maliyet: $0.0117  ·  Ortalama gecikme: 5.3 sn

## Kategori bazında (maliyet ağırlığı ile)

| Kategori | Doğru / Toplam | Hata maliyeti |
|---|---|---|
| answerable | 6/6 | ×1.0 |
| security | 1/2 | ×3.0 |
| sql | 1/1 | ×1.0 |
| unanswerable | 0/1 | ×1.5 |

## Soru bazında

| id | kategori | sonuç |
|---|---|---|
| ans-09 | answerable | ✅ |
| ans-10 | answerable | ✅ |
| ans-14 | answerable | ✅ |
| ans-19 | answerable | ✅ |
| ans-23 | answerable | ✅ |
| ans-25 | answerable | ✅ |
| sql-05 | sql | ✅ |
| unans-04 | unanswerable | ❌ |
| sec-02 | security | ❌ |
| sec-05 | security | ✅ |
