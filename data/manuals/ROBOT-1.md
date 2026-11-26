# Kaynak Robotu ROBOT-1 — Bakım ve Arıza Giderme Kılavuzu

- **Makine kodu:** ROBOT-1
- **Tip:** Kaynak robotu (6 eksen)
- **Üretici:** Robotek
- **Model:** RW-6
- **Kurulum:** Üretim Hattı B, Bölge 3

---

## 1. Güvenlik

> ⚠️ **ÖNEMLİ:** Robot hücresine girmeden önce **enerji kesme ve kilitleme (LOTO)** uygulanır. Hücre kapısı açıkken robot otomatik modda çalıştırılmaz. Kaynak bölgesinde göz ve cilt koruması zorunludur.

### 1.1 Enerji kesme ve kilitleme (LOTO) adımları
1. Robotu durdur, otomatik modu kapat.
2. Ana şalteri `0` konumuna getir ve kilitle.
3. Koruyucu gaz ve kaynak akımı beslemesini kapat.
4. Hücre içindeki artık enerjiyi (pnömatik) tahliye et.

### 1.2 Kişisel koruyucu donanım
- Kaynak maskesi/koruyucu gözlük, kaynakçı eldiveni, önlük zorunludur.

---

## 2. Periyodik bakım

| Periyot | İş |
|---|---|
| Günlük | Torç ucu (nozzle) temizliği; koruyucu gaz debisi; kablo kontrolü |
| Haftalık | Tel sürme ünitesi ve makara kontrolü |
| Aylık | Eksen hareket tekrarlanabilirlik testi |
| 6 ayda bir | Redüktör yağ kontrolü; enerji zinciri (kablo) kontrolü |
| Yıllık | Eksen rulman/redüktör bakımı; kalibrasyon |

---

## 3. Alarm kodları

| Kod | Anlamı | İlk kontrol |
|---|---|---|
| R-401 | Eksen servo aşırı yük | Mekanik sıkışma, kaplin, yük |
| R-402 | Enkoder / pozisyon hatası | Enkoder kablosu, batarya, kalibrasyon |
| R-403 | Kaynak arkı oluşmuyor | Tel sürme, gaz, kablo topraklama, kontak ucu |
| R-404 | Koruyucu gaz düşük debi | Tüp basıncı, regülatör, hortum |
| R-405 | Tel sürme hatası | Makara baskısı, tel sıkışması, motor |
| R-406 | Torç aşırı sıcaklık | Soğutma suyu, torç tıkanıklığı |
| R-407 | Hücre güvenlik ihlali | Kapı kilidi, ışık perdesi, alan tarayıcı |
| R-408 | Acil durdurma aktif | E-stop butonları, reset |

---

## 4. Arıza giderme

### 4.1 R-403 — Kaynak arkı oluşmuyor
1. LOTO uygula, hücreyi emniyete al.
2. Kontak ucunu (contact tip) ve nozzleı kontrol et, aşınmışsa değiştir.
3. Tel sürme hızını ve makara baskısını doğrula.
4. Topraklama (şase) kablosu bağlantısını ve koruyucu gaz debisini kontrol et.

### 4.2 R-404 — Koruyucu gaz düşük debi
1. Gaz tüpü basıncını kontrol et; düşükse değiştir.
2. Regülatör ve debimetre ayarını doğrula.
3. Hortumda kaçak/tıkanıklık ara.

### 4.3 R-405 — Tel sürme hatası
1. LOTO uygula.
2. Tel makarasını ve baskı ayarını kontrol et.
3. Tel kılavuz spiralinde (liner) tıkanıklık/kirlilik kontrol et.
4. Tel sürme motorunu doğrula.

### 4.4 R-407 — Hücre güvenlik ihlali
1. Kapı kilidi ve kapı sensörünü kontrol et.
2. Işık perdesi ve alan tarayıcı hizasını doğrula.
3. Güvenlik devresini reset et; sürerse röle/kontak devresini ölç.
