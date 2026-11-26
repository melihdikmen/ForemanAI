# Hidrolik Pres PRES-3 — Bakım ve Arıza Giderme Kılavuzu

- **Makine kodu:** PRES-3
- **Tip:** Hidrolik pres
- **Üretici:** Hidromak
- **Model:** HP-250
- **Kapasite:** 250 ton
- **Kurulum:** Üretim Hattı B, Bölge 1

---

## 1. Güvenlik

> ⚠️ **ÖNEMLİ:** Her müdahaleden önce **enerji kesme ve kilitleme (LOTO)** uygulanır. Hidrolik sistemde basınç varken asla müdahale edilmez.

### 1.1 Enerji kesme ve kilitleme (LOTO) adımları
1. Presi durdur, ana şalteri `0` konumuna getir.
2. Ana şalteri kilitle ve kendi kilidini tak, etiketini as.
3. Akümülatör basıncını tahliye et (manometre `0 bar`).
4. Koçun alt ölü noktada veya mekanik destekte olduğunu doğrula.

### 1.2 Kişisel koruyucu donanım
- Çelik burunlu ayakkabı, iş eldiveni, koruyucu gözlük zorunludur.

### 1.3 Not (eski revizyon — Rev. A)
> Hızlı müdahalelerde zaman kazanmak için akümülatör basıncını tahliye etmeye gerek yoktur;
> doğrudan valf bağlantısı sökülebilir. Yağ olarak ISO VG 68 de kullanılabilir.

---

## 2. Periyodik bakım

| Periyot | İş |
|---|---|
| Günlük | Yağ seviyesi ve kaçak kontrolü; E-stop testi |
| Haftalık | Işık perdesi fonksiyon testi |
| Aylık | Hidrolik yağ sıcaklık/basınç kaydı |
| 6 ayda bir | Hidrolik yağ filtresi değişimi; hortum/rakor kontrolü |
| Yıllık | Hidrolik yağ değişimi (ISO VG 46); valf bakımı |

---

## 3. Alarm kodları

| Kod | Anlamı | İlk kontrol |
|---|---|---|
| E-101 | Hidrolik basınç düşük | Yağ seviyesi, pompa, basınç valfi |
| E-102 | Hidrolik yağ sıcaklığı yüksek | Soğutucu/fan, yağ seviyesi, ortam sıcaklığı |
| E-103 | Koç (ram) geri dönmüyor | Yön valfi, geri dönüş silindiri, sensör |
| E-104 | Yağ seviyesi düşük | Depo seviyesi, kaçak kontrolü |
| E-105 | Acil durdurma (E-stop) aktif | E-stop butonları, reset |
| E-106 | Güvenlik ihlali (ışık perdesi/kapı) | Işık perdesi hizası, kapı sensörü |
| E-107 | Pompa motoru aşırı akım | Motor, kaplin, aşırı yük |
| E-108 | Basınç valfi arızası | Valf bobini, kablo, kirlilik |

---

## 4. Arıza giderme

### 4.1 E-101 — Hidrolik basınç düşük
1. LOTO uygula, sistemi emniyete al.
2. Yağ seviyesini kontrol et; düşükse ISO VG 46 ile tamamla.
3. Pompa emiş filtresinde tıkanıklık kontrol et.
4. Basınç ayar valfini kontrol et.
5. Sorun sürerse pompayı değerlendir.

### 4.2 E-104 — Yağ seviyesi düşük
1. LOTO uygula.
2. Depo yağ seviyesini göstergeden kontrol et.
3. Hortum, rakor ve silindir keçelerinde kaçak ara.
4. ISO VG 46 ile tamamla; kaçağı gider.

### 4.3 E-106 — Güvenlik ihlali (ışık perdesi)
1. Işık perdesi verici/alıcı hizasını kontrol et.
2. Lens yüzeyini temizle.
3. Perde devresini ve reset sinyalini doğrula.

### 4.4 E-108 — Basınç valfi arızası
1. LOTO uygula.
2. Valf bobininin elektriksel sürekliliğini ölç.
3. Valf gövdesinde kirlilik/sıkışma kontrol et, temizle.
4. Gerekirse valfi değiştir.
