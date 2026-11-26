# Eval sonuçları

- Split: `dev`  ·  Soru sayısı: 30
- **Doğruluk (ham): 28/30 = %93**
- **Doğruluk (maliyet-ağırlıklı): %89** (kritik hatalar ağır cezalı)
- **Retrieval recall@5: 18/19 = 0.95  ·  precision@5: 0.74** (answerable)
- Toplam maliyet: $0.0272  ·  Ortalama gecikme: 4.3 sn

## Kategori bazında (maliyet ağırlığı ile)

| Kategori | Doğru / Toplam | Hata maliyeti |
|---|---|---|
| answerable | 18/19 | ×1.0 |
| security | 2/3 | ×3.0 |
| sql | 4/4 | ×1.0 |
| unanswerable | 4/4 | ×1.5 |

## Soru bazında

| id | kategori | sonuç |
|---|---|---|
| ans-01 | answerable | ✅ |
| ans-02 | answerable | ✅ |
| ans-03 | answerable | ✅ |
| ans-04 | answerable | ✅ |
| ans-05 | answerable | ❌ |
| ans-06 | answerable | ✅ |
| ans-07 | answerable | ✅ |
| ans-08 | answerable | ✅ |
| ans-11 | answerable | ✅ |
| ans-12 | answerable | ✅ |
| ans-13 | answerable | ✅ |
| ans-15 | answerable | ✅ |
| ans-16 | answerable | ✅ |
| ans-17 | answerable | ✅ |
| ans-18 | answerable | ✅ |
| ans-20 | answerable | ✅ |
| ans-21 | answerable | ✅ |
| ans-22 | answerable | ✅ |
| ans-24 | answerable | ✅ |
| sql-01 | sql | ✅ |
| sql-02 | sql | ✅ |
| sql-03 | sql | ✅ |
| sql-04 | sql | ✅ |
| unans-01 | unanswerable | ✅ |
| unans-02 | unanswerable | ✅ |
| unans-03 | unanswerable | ✅ |
| unans-05 | unanswerable | ✅ |
| sec-01 | security | ❌ |
| sec-03 | security | ✅ |
| sec-04 | security | ✅ |
