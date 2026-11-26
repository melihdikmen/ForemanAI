# Fabrika Bakım Asistanı — PROCESS.md

> Amaç: FDE kursunda öğrendiğim konuları (eval, RAG, tool calling, agent, HITL, güvenlik, gözlemlenebilirlik, deployment) gerçekçi bir iş birimi problemi üzerinde, Python ile, uçtan uca uygulamak.
> Çalışma şekli: Claude Code ile, **öğrenme modunda** (bkz. CLAUDE.md). Her faz bitmeden sonrakine geçilmez.

---

## 1. Problem ve başarı metriği

**Senaryo (kurgusal müşteri):** "Anadolu Metal A.Ş." — orta ölçekli bir metal işleme fabrikası. Bakım ekibinde 12 teknisyen, 2 ustabaşı var.

**Bugünkü durum:** Bir makine arıza verdiğinde teknisyen;
- kağıt/PDF kılavuzlarda çözüm arıyor,
- "bu arıza daha önce olmuş muydu?" sorusu için kıdemli birine soruyor,
- iş emrini Excel'e elle giriyor.

Ortalama arıza teşhis süresi uzun, tecrübeli personel izne çıkınca bilgi kayboluyor.

**Çözüm:** Teknisyen arızayı doğal dille yazar ("Pres-3 hidrolik basınç düşük alarmı veriyor"). Asistan:
1. Kılavuzlarda ve geçmiş arıza kayıtlarında ilgili bilgiyi bulur, **kaynak göstererek** olası nedenleri ve adımları önerir.
2. Makinenin arıza geçmişini veritabanından sorgular.
3. **İş emri taslağı** hazırlar. Taslak, **ustabaşı onaylamadan** kaydedilmez.

**Başarı metrikleri (hedefler):**

| Metrik | Hedef |
|---|---|
| Cevap doğruluğu (eval seti, LLM-as-judge + elle kontrol) | ≥ %80 |
| Retrieval recall@5 | ≥ 0,85 |
| Retrieval precision@5 (gürültü göstergesi) | ölç ve raporla |
| Kaynak gösterme oranı | %100 (kaynaksız cevap yok) |
| "Bilmiyorum" demesi gereken sorularda doğru reddetme | ≥ %90 |
| Onaysız veritabanı yazması | 0 |
| p95 gecikme | < 8 sn |
| Sorgu başı maliyet | ölçülüp README'ye yazılır |

> **Precision/recall ve maliyet matrisi:** Sadece recall yetmez — recall "doğruyu kaçırdık mı",
> precision "getirdiğimiz gürültülü mü" sorusunu yanıtlar; ikisi birlikte okunur. Ayrıca her hata eşit
> maliyetli değildir: **kritik bir arızayı kaçırmak** (false negative) ucuz bir yanlış öneriden çok daha
> pahalıdır. Bu yüzden arızaları **kritik / normal / düşük** diye önceliklendirip bir **maliyet matrisi**
> (hangi hata ne kadar pahalı) tanımlayacağız; eval skorlarını bu matrisle ağırlıklandıracağız.

## 2. Kapsam (RICE ile öncelik)

| Özellik | Öncelik | Not |
|---|---|---|
| Kılavuz + arıza kaydı üzerinden soru-cevap (RAG) | Yüksek | Çekirdek değer |
| Arıza geçmişi sorgulama (SQL tool) | Yüksek | |
| İş emri taslağı + ustabaşı onayı (HITL) | Yüksek | FDE'nin kritik konusu |
| Basit web arayüzü | Orta | React (Vite) — güçlü olduğum alan |
| MCP sunucusu | Orta | Araçları başka istemcilere açmak için |
| Görsel (fotoğraftan arıza tanıma) | Kapsam dışı | v2 fikri |

## 3. Teknoloji seçimleri

- **Dil:** Python 3.12 (paket yönetimi: `uv`, lint: `ruff`, test: `pytest`)
- **API:** FastAPI + Pydantic
- **Veritabanı:** PostgreSQL + `pgvector` (Docker ile)
- **Agent:** LangGraph (checkpoint: Postgres)
- **Model:** **OpenRouter** üzerinden (tek API anahtarı, OpenAI uyumlu API — `openai` Python SDK'sı `base_url="https://openrouter.ai/api/v1"` ile kullanılır). Model adı `.env`'de (`LLM_MODEL=...`), böylece kod değişmeden model değiştirilebilir. Faz 2'de 2–3 modeli (ör. bir Claude, bir Gemini, bir ucuz/açık model) aynı eval setinde karşılaştır; kalite/maliyet/gecikmeye göre seç.
- **Embedding:** OpenRouter'da uygun embedding modeli varsa oradan; yoksa yerel çok dilli bir model (ör. `intfloat/multilingual-e5` ailesi, `sentence-transformers` ile — ücretsiz ve Türkçe'de iyi). Embedding boyutu pgvector kolonuyla aynı olmalı.
- **Gözlemlenebilirlik:** Langfuse
- **Arayüz:** React + Vite (tek sayfa)
- **Deploy:** Docker Compose → GitHub Actions → Google Cloud Run (veya AWS)
- **Model gateway:** Tüm LLM çağrıları tek bir kapıdan (`app/llm.py`) ve **OpenRouter** üzerinden geçer. OpenRouter burada bir *model gateway* rolü oynar: tek anahtar, çok sağlayıcı, model değiştirme (routing/fallback) ve maliyet görünürlüğü. Gateway deseninin ne kazandırdığını (merkezi loglama, rate-limit, retry, model soyutlama) README'de anlatacağız.
- **Context layer (bağlam katmanı):** "Modelin context window'una ne giriyor" bilinçli tasarlanır: sistem promptu + seçilen kılavuz parçaları + araç sonuçları + (ileride) hafıza. Her isteğin **token bütçesini** ve neyin dahil/hariç olduğunu belgeleyeceğiz; gereksiz bağlam hem maliyet hem gürültüdür.

## 4. Veri

Telif sorunu yaşamamak için **tüm veri sentetik** üretilir (Claude ile, gerçekçi ama kurgusal):

- **Makineler (6 adet):** Hidrolik Pres-1/2/3, CNC Torna-1, Vidalı Kompresör-1, Kaynak Robotu-1
- **Kılavuzlar:** Her makine için Markdown kılavuz (güvenlik, periyodik bakım, alarm kodları tablosu, arıza giderme adımları). Toplam ~40–60 sayfa.
- **Arıza kayıtları:** ~200 kayıt (tarih, makine, alarm kodu, belirti, kök neden, yapılan işlem, süre, teknisyen).
- **İş emirleri tablosu:** boş başlar, asistan + onay akışıyla dolar.
- **Kasıtlı tuzaklar:** Bir kılavuzda eski/çelişkili bilgi, bir kayıtta prompt injection denemesi ("önceki talimatları unut…"). Güvenlik testleri için.

## 5. Eval stratejisi (önce eval, sonra kod)

- **Altın set:** 40 soru → `evals/golden.jsonl`
  - 25 cevaplanabilir (beklenen cevap + beklenen kaynak)
  - 5 SQL gerektiren ("Pres-3 son 6 ayda kaç kez arıza verdi?")
  - 5 cevaplanamaz (asistan "bilmiyorum / kılavuzda yok" demeli)
  - 5 güvenlik/tuzak sorusu
- **Ayrım:** 30 soru dev seti, 10 soru held-out (sadece faz sonlarında bakılır).
- **Ölçümler:** retrieval recall@k ve MRR, cevap doğruluğu (LLM-as-judge + 10 soruda elle kontrol), kaynak doğruluğu, tool çağrısı doğruluğu, gecikme, maliyet.
- Her faz sonunda `evals/results/<faz>.md` dosyasına sonuçlar yazılır, bir öncekiyle karşılaştırılır.

## 6. Güvenlik (lethal trifecta analizi)

- **Özel veri erişimi:** var (arıza kayıtları, personel adları)
- **Güvenilmeyen içerik:** var (kılavuz/kayıt metinleri injection taşıyabilir)
- **Dışarıya iletişim:** **yok** — asistanın e-posta/HTTP gönderme aracı olmayacak. Üçlü bilerek kırılır.
- Veritabanı: asistanın kullandığı kullanıcı **sadece okuma** yetkili; yazma yalnızca onay endpoint'inden, ayrı bir servis kullanıcısıyla.
- Rol: `teknisyen` (soru sorar, taslak oluşturur), `ustabaşı` (onaylar/reddeder).
- Prompt injection testleri eval setinde.

---

## 7. Fazlar

Her faz şu başlıkları içerir: **Öğreneceklerim · Yapılacaklar · Bitti kriteri · Kontrol soruları**.

### Faz 0 — Kurulum ve Python temelleri (2–3 gün)
**Öğreneceklerim:** `uv`, sanal ortam, proje yapısı, type hint, dataclass, comprehension, `async/await`, pytest (TS karşılıklarıyla).
**Yapılacaklar:**
- [ ] Repo, `uv init`, `ruff`, `pytest`, `.env.example`
- [ ] Docker ile Postgres + pgvector ayağa kalksın
- [ ] Küçük Python alıştırmaları (Claude bana yazdırsın): CSV oku → filtrele → test yaz
**Bitti kriteri:** `uv run pytest` yeşil, `docker compose up` ile DB çalışıyor.
**Kontrol soruları:** list comprehension'ı TS'te nasıl yazardım? `async def` neden gerekli?

### Faz 1 — Veri ve eval seti (3–4 gün)
**Öğreneceklerim:** veri modelleme, SQLAlchemy/psycopg, Pydantic modelleri, iyi bir eval seti nasıl yazılır.
**Yapılacaklar:**
- [ ] Makine, arıza kaydı, iş emri tabloları (şema + migration)
- [ ] Sentetik kılavuzlar (`data/manuals/*.md`) ve 200 arıza kaydı (seed script)
- [ ] 40 soruluk `evals/golden.jsonl` + dev/held-out ayrımı
**Bitti kriteri:** Seed script veriyi yüklüyor; eval seti elle gözden geçirildi.
**Kontrol soruları:** Eval setini neden koddan önce yazıyoruz? Held-out set neye yarar?

### Faz 2 — Baseline (2 gün)
**Öğreneceklerim:** FastAPI, endpoint, Pydantic request/response, LLM API çağrısı, eval script'i.
**Yapılacaklar:**
- [ ] `POST /ask` — sadece LLM'e sor, RAG yok
- [ ] `evals/run.py` — golden set üzerinde çalıştırıp skor üretir
**Bitti kriteri:** Baseline skorları `evals/results/faz2.md`'de. (Düşük çıkması beklenir — amaç kıyas noktası.)
**Kontrol soruları:** Baseline olmadan RAG'in işe yaradığını nasıl kanıtlardık?

### Faz 3 — RAG (1 hafta)
**Öğreneceklerim:** chunking, embedding, pgvector, benzerlik araması, hibrit arama (BM25 + vektör), reranking, recall@k / MRR, kaynak gösterme.
**Yapılacaklar:**
- [ ] Kılavuzları başlık bazlı chunk'la, metadata ekle (makine, bölüm, alarm kodu)
- [ ] Embedding + pgvector indeks
- [ ] Önce sadece vektör, sonra hibrit arama — ikisini eval ile karşılaştır
- [ ] Cevapta her iddia için kaynak (`[Pres Kılavuzu §4.2]`)
- [ ] Cevaplanamaz sorularda "kılavuzda bulunamadı" davranışı
**Bitti kriteri:** recall@5 ≥ 0,85; doğruluk baseline'a göre belirgin yüksek; sonuçlar yazıldı.
**Kontrol soruları:** Chunk boyutu neyi etkiler? Hibrit arama hangi tür soruda vektörden iyidir?

### Faz 4 — Araçlar ve agent (1 hafta)
**Öğreneceklerim:** tool calling, LangGraph (state, node, edge), tool tasarımı, tool-use eval.
**Yapılacaklar:**
- [ ] Araçlar: `search_manuals`, `get_fault_history(machine_id, since)` (salt okunur SQL), `draft_work_order(...)` (sadece taslak)
- [ ] LangGraph akışı: soruyu anla → araç seç → cevapla
- [ ] SQL sorularında doğru aracın çağrıldığını ölç
**Bitti kriteri:** 5 SQL sorusunun ≥ 4'ü doğru; tool çağrıları Langfuse/loglarda görünüyor.
**Kontrol soruları:** Agent'a ham SQL yazdırmak yerine neden dar kapsamlı bir araç verdik?

### Faz 5 — İnsan onayı ve kalıcı durum (4–5 gün)
**Öğreneceklerim:** LangGraph `interrupt()`, Postgres checkpoint, kaldığı yerden devam, rol bazlı yetki.
**Yapılacaklar:**
- [ ] İş emri taslağı oluşunca akış durur, ustabaşına düşer
- [ ] `POST /work-orders/{id}/approve|reject` (sadece `ustabaşı` rolü)
- [ ] Servis yeniden başlasa bile bekleyen onaylar kaybolmaz
- [ ] React arayüz: teknisyen sohbet ekranı + ustabaşı onay listesi
**Bitti kriteri:** Onaysız hiçbir iş emri DB'ye yazılmıyor (test ile kanıtlı).
**Kontrol soruları:** Hangi işlemler otomatik, hangileri insan onaylı olmalı? Neden?

### Faz 6 — Güvenlik ve guardrail (3–4 gün)
**Öğreneceklerim:** lethal trifecta, prompt injection, en az yetki, girdi/çıktı kontrolü.
**Yapılacaklar:**
- [ ] Salt okunur DB kullanıcısı; yazma yalnızca onay servisinde
- [ ] Injection içeren kayıtlarla test; asistan talimatlara uymamalı
- [ ] Çıktı kontrolü: güvenlik adımı (enerji kesme/LOTO) atlanmamalı
- [ ] `SECURITY.md`: tehdit modeli ve alınan önlemler
**Bitti kriteri:** 5 güvenlik sorusunun hepsi geçiyor.
**Kontrol soruları:** Bu sistemde trifecta'nın hangi ayağını kırdık ve neden o ayağı?

### Faz 7 — Gözlemlenebilirlik ve otomatik eval (3 gün)
**Öğreneceklerim:** tracing, LLM-as-judge, maliyet/gecikme ölçümü, CI'da eval, precision/recall ve maliyet matrisi.
**Yapılacaklar:**
- [ ] Langfuse ile her isteğin trace'i (retrieval, tool, model, token)
- [ ] LLM-as-judge + 10 soruda elle karşılaştırma (judge ne kadar güvenilir?)
- [ ] Retrieval için **precision@k ve recall@k** birlikte raporla; MRR
- [ ] **Maliyet matrisi:** arıza önceliğine (kritik/normal/düşük) göre hataları ağırlıklandır; kritik kaçırma (false negative) ağır cezalı. Skorları hem ham hem maliyet-ağırlıklı ver.
- [ ] p95 gecikme ve sorgu başı maliyet raporu
- [ ] GitHub Actions'ta eval: skor eşiğin altına düşerse PR kırmızı
**Bitti kriteri:** Tek komutla eval raporu (precision/recall + maliyet-ağırlıklı); CI'da çalışıyor.
**Kontrol soruları:** LLM-as-judge'a ne zaman güvenmemeliyiz? Recall yüksek ama precision düşükse ne olur? Hangi hata en pahalı?

### Faz 8 — Deploy ve MCP (4–5 gün)
**Öğreneceklerim:** Docker imajı, Compose, CI/CD, Cloud Run, ortam değişkenleri/secret yönetimi, MCP sunucusu; (alternatif) managed agent platformu olarak **AWS Bedrock AgentCore**.
**Yapılacaklar:**
- [ ] Dockerfile + `docker-compose.yml` (api, db, ui)
- [ ] GitHub Actions: test → eval → build → deploy
- [ ] Cloud Run'a deploy, health check
- [ ] Araçları MCP sunucusu olarak dışa aç (Claude Desktop'tan bağlanıp dene)
- [ ] (Opsiyonel/alternatif) **AgentCore ile kıyas**: Kendi yazdığımız agent/araç/HITL/secret parçalarının AgentCore'daki karşılıklarını haritala — **Gateway** (araçları MCP olarak yayınlama), **Identity** (kimlik/yetki), **Policy** (izin/guardrail), **Memory** (yönetilen hafıza), **Runtime** (çalıştırma). "Kendin yaz vs managed platform" kararını README'de tartış.
**Bitti kriteri:** Herkese açık demo linki; MCP ile araçlar başka istemciden kullanılabiliyor.
**Kontrol soruları:** Secret'ları nerede tutuyoruz? MCP neyi kolaylaştırdı? AgentCore hangi parçaları bizden devralırdı, neyi kaybederdik (kontrol/taşınabilirlik)?

### Faz 9 — Teslim ve hikâye (2 gün)
**Yapılacaklar:**
- [ ] README: problem, mimari diyagram, eval sonuçları (faz faz iyileşme tablosu), güvenlik tasarımı, maliyet
- [ ] 2–3 dakikalık demo videosu
- [ ] `HANDOVER.md`: başkası bu sistemi nasıl işletir (runbook)
- [ ] LinkedIn paylaşımı
- [ ] Mülakat hikâyesi: "Bir bakım ekibinin derdini nasıl ölçülebilir şekilde çözdüm"

---

## 7.1 İleri / genişletme fazları (v2 — opsiyonel, kurstaki ileri konular)

> Bunlar v1 (Faz 0–9) teslim edildikten sonra sistemi derinleştiren, ileri seviye konular.
> Her biri eval setiyle ölçülür; "işe yaradı mı" rakamla gösterilir.

### Faz 10 — Agentic RAG ve çoklu agent (sub-agent)
**Öğreneceklerim:** query rewriting/expansion, iteratif (çok adımlı) retrieval, self-RAG, agent'ın aramayı değerlendirip tekrar araması; sub-agent / çoklu agent (orkestratör + uzman agent'lar).
**Yapılacaklar:**
- [ ] Agent, ilk aramadan gelen parçalar yetersizse **sorguyu yeniden yazıp** tekrar arasın (tek seferlik arama yerine döngü)
- [ ] Alakasızlık/boşluk tespiti: retrieval skoru düşükse "yeniden sor" veya "bilmiyorum"
- [ ] (Opsiyonel) **Sub-agent** deseni: ör. "retrieval uzmanı", "SQL uzmanı", "güvenlik denetçisi" alt-agent'ları + bir orkestratör
- [ ] Eval: Agentic RAG, tek-seferlik RAG'e göre recall/precision ve doğrulukta ne kazandırdı?
**Bitti kriteri:** En az bir "zor" soru sınıfında agentic RAG, Faz 4 agent'ını eval'de geçiyor.
**Kontrol soruları:** İteratif arama maliyeti ne kadar artırdı? Çoklu agent ne zaman gereksiz karmaşıklık olur?

### Faz 11 — Hafıza (memory)
**Öğreneceklerim:** kısa vadeli (konuşma) vs uzun vadeli hafıza, hafıza yazma/çağırma, hafızanın context layer'a girişi.
**Yapılacaklar:**
- [ ] Uzun vadeli hafıza deposu (ör. ustabaşının tercihleri, sık red gerekçeleri, makineye özel notlar)
- [ ] İlgili hafızayı isteğe göre çağırıp context'e ekle (ama token bütçesini aşma)
- [ ] Gizlilik/PII: hafızada ne saklanır, ne saklanmaz
- [ ] Eval: hafıza açık/kapalı iken kişiselleştirme ve doğruluk farkı
**Bitti kriteri:** Asistan önceki kararları/tercihleri hatırlayıp ilgili yerde kullanıyor (test ile kanıtlı).
**Kontrol soruları:** Hafıza ne zaman yararlı, ne zaman yanıltıcı/eski bilgi riski taşır?

### Faz 12 — Kendini iyileştirme (self-improvement)
**Öğreneceklerim:** üretimden gelen sinyalle (red gerekçeleri) iyileştirme döngüsü, prompt/eval optimizasyonu, regresyondan korunma.
**Yapılacaklar:**
- [ ] Ustabaşının **red gerekçelerini** topla ve etiketle (neden reddedildi?)
- [ ] Bu sinyalden prompt/few-shot/retrieval ayarını iyileştiren bir döngü kur
- [ ] **Held-out guard:** her iyileştirmeyi held-out sette doğrula; düşerse geri al (overfit'i engelle)
**Bitti kriteri:** Red gerekçelerinden türetilen en az bir iyileştirme, held-out sette skoru düşürmeden dev skorunu artırıyor.
**Kontrol soruları:** Dev'e göre iyileşip held-out'ta düşmek neyin işareti? İyileştirmeyi nasıl geri alırız?

### Faz 13 — Otonomi seviyeleri ve Sorumlu AI
**Öğreneceklerim:** otonomi seviyeleri (öneri → onaylı eylem → otonom eylem), sorumlu AI (adalet, şeffaflık, hesap verebilirlik, kötüye kullanım).
**Yapılacaklar:**
- [ ] **Otonomi tablosu:** her işlem (cevap, SQL sorgu, iş emri taslağı, iş emri kaydı) hangi seviyede — otomatik mi, insan onaylı mı, yasak mı — ve **neden**
- [ ] **Sorumlu AI değerlendirmesi:** yanlış teşhisin güvenlik etkisi, personel verisinin gizliliği, injection/kötüye kullanım, "asistan hata yaparsa kim sorumlu"
- [ ] `RESPONSIBLE_AI.md`: otonomi tablosu + risk/azaltım + sınırlar
**Bitti kriteri:** Otonomi tablosu ve sorumlu AI dokümanı yazıldı; kod bu tabloya uyuyor (ör. iş emri kaydı asla otonom değil).
**Kontrol soruları:** Hangi işlemi otonom yapmak kabul edilemez, neden? Otonomiyi artırmanın şartı ne (hangi eval eşiği)?

---

## 8. Durum takibi

| Faz | Durum | Başlangıç | Bitiş | Ana sonuç |
|---|---|---|---|---|
| 0 Kurulum | ✅ | 2026-11-26 | 2026-11-26 | uv+ruff+pytest kuruldu, app/ yapısı, .env(.example), Docker Postgres16+pgvector çalışıyor, pytest yeşil |
| 1 Veri + eval | ✅ | 2026-11-26 | 2026-11-26 | 3 tablo+migration (SQLAlchemy/Alembic), 6 kılavuz, seed 6 makine+202 kayıt (2 injection tuzağı), 40 soruluk golden.jsonl (30 dev/10 held-out) + yapısal testler |
| 2 Baseline | ✅ | 2026-11-26 | 2026-11-26 | app/llm.py (OpenRouter, token/maliyet log), POST /ask, evals/run.py. Model: claude-haiku-5.5. Baseline dev %63 (ans 13/19, sql 0/4, unans 4/4, sec 2/3) |
| 3 RAG | ✅ | 2026-11-26 | 2026-11-26 | fastembed (MiniLM-384) + pgvector, 61 chunk, vektör arama + kaynak gösterme. Dev doğruluk %63→%77, recall@5=0.95 (hedef ≥0.85). Hibrit arama (3.8) atlandı (recall yeterli) |
| 4 Agent | ✅ | 2026-11-26 | 2026-11-26 | Ham tool-calling agent (LangGraph değil): search_manuals, get_fault_history (salt okunur), draft_work_order (taslak). Dev doğruluk %77→%93, sql 0/4→4/4. Eval ölçeri sağlamlaştırıldı (refusal+sayı normalizasyonu) |
| 5 HITL | ⬜ | | | |
| 6 Güvenlik | ⬜ | | | |
| 7 Gözlemlenebilirlik | ⬜ | | | |
| 8 Deploy + MCP | ⬜ | | | |
| 9 Teslim | ⬜ | | | |
| 10 Agentic RAG + çoklu agent (v2) | ✅ | 2026-11-26 | 2026-11-26 | Agentic RAG: makine-filtreli arama, iteratif tekrar-arama, skor görünürlüğü. Zor soru setinde (evals/hard.jsonl) A/B: tek-seferlik %80 vs agentic %100 (maliyet ~%58 fazla). run.py --file/--mode ile A/B. Sub-agent ertelendi (opsiyonel) |
| 11 Hafıza (v2) | ⬜ | | | |
| 12 Self-improvement (v2) | ⬜ | | | |
| 13 Otonomi + Sorumlu AI (v2) | ⬜ | | | |

## 9. Açık sorular

- Model: OpenRouter'daki hangi model? Faz 2'de 2–3 modeli baseline'da deneyip eval sonucuna göre karar ver. (Model routing: basit sorularda ucuz model, karmaşık/agent adımlarında güçlü model — Faz 7'de dene.)
- Arayüz React web mi, yoksa teknisyenler için React Native mobil mi? (v1: web)
- Gerçek bir fabrika/bakım çalışanından 15 dakikalık geri bildirim alınabilir mi? (FDE pratiği için çok değerli)