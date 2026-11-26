# CLAUDE.md — Fabrika Bakım Asistanı

Plan ve fazlar için: `PROCESS.md`. Her oturumda önce PROCESS.md'deki "Durum takibi" tablosuna bak, hangi fazdayız ondan devam et.

## Öğrenme modu (en önemli kural)

Ben bu projeyi **öğrenmek için** yapıyorum. Hedefim Forward Deployed Engineer / AI Engineer rollerine hazırlanmak.

- Benim geçmişim: 7 yıl mobil (React Native, TypeScript). **Python'a yeniyim.**
- Her adımda önce **ne** yapacağımızı ve **neden** yaptığımızı Türkçe, kısa anlat; sonra kodu yaz.
- Python kavramlarını **TypeScript karşılığıyla** açıkla (ör. `list comprehension` ≈ `array.map/filter`).
- Büyük kod blokları yazma. **Küçük parçalarla** ilerle; her parçadan sonra dur ve "sorun var mı?" diye sor.
- Her fazda en az 1–2 küçük kısmı **bana yazdır** (alıştırma); sonra benim kodumu incele ve geri bildirim ver.
- Yeni bir kütüphane/kavram geldiğinde 3–4 cümlelik bir açıklama yap; gerekirse küçük bir örnek göster.
- Bir faz bitince: kısa özet + PROCESS.md'deki kontrol sorularını bana sor + durum tablosunu güncelle.
- Ben "hızlı geç" dersem açıklamaları kısalt; "detaylı anlat" dersem derinleş.

## Mühendislik kuralları

- Python 3.12, paket yönetimi `uv`. Lint `ruff`, test `pytest`.
- **Kodda asla Türkçe kullanma.** Tüm tanımlayıcılar (değişken/fonksiyon/sınıf adları), yorumlar (comment), docstring'ler, log mesajları ve kod içi string'ler **İngilizce** olacak. Türkçe sadece: (a) bana yaptığın sohbet/açıklamalar, (b) kullanıcıya gösterilecek ürün metinleri (asistanın teknisyene verdiği cevaplar, UI metinleri) ve (c) sentetik veri (kılavuzlar, arıza kayıtları — bunlar Türkçe fabrika içeriği). Markdown dokümanlar (CLAUDE.md, PROCESS.md, README) Türkçe kalabilir.
- Tüm fonksiyonlarda type hint. Veri modelleri Pydantic.
- **Her fonksiyon, sınıf ve modül bir docstring içermeli** (İngilizce, en az tek satır: ne yaptığını — ve önemliyse neden yaptığını — anlat). Parametreler ve dönüş değeri önemliyse docstring'de açıkla.
- **Her değişken açıklayıcı olmalı:** ya kendini anlatan bir isim taşısın ya da tanımlandığı satırda kısa bir yorum (comment) ile ne tuttuğu açıklansın. Sihirli sayı/kısaltma kullanma.
- LLM çağrıları **OpenRouter** üzerinden: `openai` SDK + `base_url="https://openrouter.ai/api/v1"`, anahtar `OPENROUTER_API_KEY`, model adı `LLM_MODEL` env değişkeninden. Model adını koda gömme; tüm çağrılar tek bir `app/llm.py` modülünden geçsin (token ve maliyet loglansın).
- Gizli bilgiler `.env`'de; asla koda veya commit'e yazma. `.env.example` güncel tutulsun.
- Asistanın kullandığı DB kullanıcısı **salt okunur**. Yazma yalnızca onay endpoint'inden.
- Asistana **dışarıya veri gönderen araç** (e-posta, HTTP POST vb.) ekleme. (Lethal trifecta'nın bu ayağı bilerek kapalı.)
- Her davranış değişikliğinden sonra `uv run python evals/run.py --split dev` çalıştır, sonucu söyle.
- Held-out sete sadece faz sonlarında ve ben istediğimde bak.
- Commit mesajları kısa ve açıklayıcı; bir commit = bir mantıklı değişiklik.

## Proje yapısı (hedef)

```
app/            # FastAPI, agent, araçlar
  api/
  agent/
  tools/
  rag/
data/
  manuals/      # sentetik kılavuzlar (md)
  seed/         # arıza kayıtları seed script
evals/
  golden.jsonl
  run.py
  results/
ui/             # React + Vite
tests/
```