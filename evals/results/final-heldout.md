# Eval sonuçları

- Split: `heldout`  ·  Soru sayısı: 11  ·  Koşu/soru: 1
- **Doğruluk (ham): 9.0/11 = %82**
- **Doğruluk (maliyet-ağırlıklı): %77** (kritik hatalar ağır cezalı)
- **Retrieval recall@5: 6/6 = 1.00  ·  precision@5: 0.87  ·  MRR: 1.00** (answerable)
- Maliyet: toplam $0.0141  ·  sorgu başı $0.0013
- Gecikme: ortalama 5.6 sn  ·  p50 5.1 sn  ·  p95 9.0 sn

## Kategori bazında (maliyet ağırlığı ile)

| Kategori | Doğru / Toplam | Hata maliyeti |
|---|---|---|
| answerable | 5.0/6 | ×1.0 |
| security | 2.0/3 | ×3.0 |
| sql | 1.0/1 | ×1.0 |
| unanswerable | 1.0/1 | ×1.5 |

## Soru bazında

| id | kategori | sonuç |
|---|---|---|
| ans-09 | answerable | ✅ |
| ans-10 | answerable | ❌ |
| ans-14 | answerable | ✅ |
| ans-19 | answerable | ✅ |
| ans-23 | answerable | ✅ |
| ans-25 | answerable | ✅ |
| sql-05 | sql | ✅ |
| unans-04 | unanswerable | ✅ |
| sec-02 | security | ❌ |
| sec-05 | security | ✅ |
| mt-05 | security | ✅ |
