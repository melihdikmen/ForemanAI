# LLM-as-judge raporu

- Judge modeli: `anthropic/claude-sonnet-5.5`  ·  Cevap sayısı: 32  ·  Maliyet: $0.0910
- Keyword ölçer: 29/32 geçti  ·  Judge: 32/32 geçti
- **Uyum (ikisi aynı karar): 29/32 = %91**
- Sadece judge geçirdi: 3  ·  Sadece keyword geçirdi: 0

## Anlaşmazlıklar (elle değerlendirilecek)

| id | run | keyword | judge | judge gerekçesi |
|---|---|---|---|---|
| ans-04 | 1 | ❌ | ✅ | Cevap yön kontrol valfini (bobin ve elektrik bağlantısı) ve pozisyon sensörünü kontrol etmeyi içeriyor, kaynak olarak PRES-1.md'yi gösteriyor ve LOTO güvenlik adımlarını da koruyor. |
| ans-05 | 1 | ❌ | ✅ | The answer lists LOTO steps including main switch lockout and tagging and accumulator pressure release, which cover energy isolation, locking and pressure, and it cites PRES-1.md. |
| unans-05 | 1 | ❌ | ✅ | The assistant declined, saying it has no cafeteria menu information, and redirected the user to maintenance topics. |

Elle kıyas: `<tag>.judge.jsonl` içindeki `manual_verdict` alanını "pass"/"fail" olarak doldurun; sonra `--compare` ile uyumu hesaplayın.
