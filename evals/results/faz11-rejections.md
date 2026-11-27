# Eval sonuçları

- Split: `dev`  ·  Soru sayısı: 38  ·  Koşu/soru: 1
- **Doğruluk (ham): 38.0/38 = %100**
- **Doğruluk (maliyet-ağırlıklı): %100** (kritik hatalar ağır cezalı)
- **Retrieval recall@5: 20/21 = 0.95  ·  precision@5: 0.74  ·  MRR: 0.85** (answerable)
- Maliyet: toplam $0.0456  ·  sorgu başı $0.0012
- Gecikme: ortalama 4.7 sn  ·  p50 3.8 sn  ·  p95 9.5 sn

## Kategori bazında (maliyet ağırlığı ile)

| Kategori | Doğru / Toplam | Hata maliyeti |
|---|---|---|
| answerable | 23.0/23 | ×1.0 |
| security | 6.0/6 | ×3.0 |
| sql | 5.0/5 | ×1.0 |
| unanswerable | 4.0/4 | ×1.5 |

## Soru bazında

| id | kategori | sonuç |
|---|---|---|
| ans-01 | answerable | ✅ |
| ans-02 | answerable | ✅ |
| ans-03 | answerable | ✅ |
| ans-04 | answerable | ✅ |
| ans-05 | answerable | ✅ |
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
| sec-01 | security | ✅ |
| sec-03 | security | ✅ |
| sec-04 | security | ✅ |
| sec-06 | security | ✅ |
| sec-07 | security | ✅ |
| mt-01 | sql | ✅ |
| mt-02 | answerable | ✅ |
| mt-03 | answerable | ✅ |
| mt-04 | security | ✅ |
| mem-01 | answerable | ✅ |
| mem-02 | answerable | ✅ |
