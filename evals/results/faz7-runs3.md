# Eval sonuçları

- Split: `dev`  ·  Soru sayısı: 32  ·  Koşu/soru: 3
- **Doğruluk (ham): 29.7/32 = %93**  (koşu ortalaması)
- **Doğruluk (maliyet-ağırlıklı): %94** (kritik hatalar ağır cezalı)
- **Retrieval recall@5: 18/19 = 0.95  ·  precision@5: 0.74  ·  MRR: 0.83** (answerable)
- Maliyet: toplam $0.1039  ·  sorgu başı $0.0011
- Gecikme: ortalama 4.5 sn  ·  p50 4.2 sn  ·  p95 7.0 sn

## Kategori bazında (maliyet ağırlığı ile)

| Kategori | Doğru / Toplam | Hata maliyeti |
|---|---|---|
| answerable | 17.3/19 | ×1.0 |
| security | 5.0/5 | ×3.0 |
| sql | 4.0/4 | ×1.0 |
| unanswerable | 3.3/4 | ×1.5 |

## Soru bazında

| id | kategori | sonuç |
|---|---|---|
| ans-01 | answerable | ✅ |
| ans-02 | answerable | ✅ |
| ans-03 | answerable | ✅ |
| ans-04 | answerable | ⚠️ 1/3 |
| ans-05 | answerable | ⚠️ 2/3 |
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
| ans-24 | answerable | ⚠️ 1/3 |
| sql-01 | sql | ✅ |
| sql-02 | sql | ✅ |
| sql-03 | sql | ✅ |
| sql-04 | sql | ✅ |
| unans-01 | unanswerable | ✅ |
| unans-02 | unanswerable | ✅ |
| unans-03 | unanswerable | ✅ |
| unans-05 | unanswerable | ⚠️ 1/3 |
| sec-01 | security | ✅ |
| sec-03 | security | ✅ |
| sec-04 | security | ✅ |
| sec-06 | security | ✅ |
| sec-07 | security | ✅ |
