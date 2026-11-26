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
| Kaynak gösterme oranı | %100 (kaynaksız cevap yok) |
| "Bilmiyorum" demesi gereken sorularda doğru reddetme | ≥ %90 |
| Onaysız veritabanı yazması | 0 |
| p95 gecikme | < 8 sn |
| Sorgu başı maliyet | ölçülüp README'ye yazılır |

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
**Öğreneceklerim:** tracing, LLM-as-judge, maliyet/gecikme ölçümü, CI'da eval.
**Yapılacaklar:**
- [ ] Langfuse ile her isteğin trace'i (retrieval, tool, model, token)
- [ ] LLM-as-judge + 10 soruda elle karşılaştırma (judge ne kadar güvenilir?)
- [ ] p95 gecikme ve sorgu başı maliyet raporu
- [ ] GitHub Actions'ta eval: skor eşiğin altına düşerse PR kırmızı
**Bitti kriteri:** Tek komutla eval raporu; CI'da çalışıyor.
**Kontrol soruları:** LLM-as-judge'a ne zaman güvenmemeliyiz?

### Faz 8 — Deploy ve MCP (4–5 gün)
**Öğreneceklerim:** Docker imajı, Compose, CI/CD, Cloud Run, ortam değişkenleri/secret yönetimi, MCP sunucusu.
**Yapılacaklar:**
- [ ] Dockerfile + `docker-compose.yml` (api, db, ui)
- [ ] GitHub Actions: test → eval → build → deploy
- [ ] Cloud Run'a deploy, health check
- [ ] Araçları MCP sunucusu olarak dışa aç (Claude Desktop'tan bağlanıp dene)
**Bitti kriteri:** Herkese açık demo linki; MCP ile araçlar başka istemciden kullanılabiliyor.
**Kontrol soruları:** Secret'ları nerede tutuyoruz? MCP neyi kolaylaştırdı?

### Faz 9 — Teslim ve hikâye (2 gün)
**Yapılacaklar:**
- [ ] README: problem, mimari diyagram, eval sonuçları (faz faz iyileşme tablosu), güvenlik tasarımı, maliyet
- [ ] 2–3 dakikalık demo videosu
- [ ] `HANDOVER.md`: başkası bu sistemi nasıl işletir (runbook)
- [ ] LinkedIn paylaşımı
- [ ] Mülakat hikâyesi: "Bir bakım ekibinin derdini nasıl ölçülebilir şekilde çözdüm"

---

## 8. Durum takibi

| Faz | Durum | Başlangıç | Bitiş | Ana sonuç |
|---|---|---|---|---|
| 0 Kurulum | ✅ | 2026-11-26 | 2026-11-26 | uv+ruff+pytest kuruldu, app/ yapısı, .env(.example), Docker Postgres16+pgvector çalışıyor, pytest yeşil |
| 1 Veri + eval | ⬜ | | | |
| 2 Baseline | ⬜ | | | |
| 3 RAG | ⬜ | | | |
| 4 Agent | ⬜ | | | |
| 5 HITL | ⬜ | | | |
| 6 Güvenlik | ⬜ | | | |
| 7 Gözlemlenebilirlik | ⬜ | | | |
| 8 Deploy + MCP | ⬜ | | | |
| 9 Teslim | ⬜ | | | |

## 9. Açık sorular

- Model: OpenRouter'daki hangi model? Faz 2'de 2–3 modeli baseline'da deneyip eval sonucuna göre karar ver. (Model routing: basit sorularda ucuz model, karmaşık/agent adımlarında güçlü model — Faz 7'de dene.)
- Arayüz React web mi, yoksa teknisyenler için React Native mobil mi? (v1: web)
- Gerçek bir fabrika/bakım çalışanından 15 dakikalık geri bildirim alınabilir mi? (FDE pratiği için çok değerli)