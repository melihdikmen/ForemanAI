# Hidrolik Pres PRES-1 — Bakım ve Arıza Giderme Kılavuzu

- **Makine kodu:** PRES-1
- **Tip:** Hidrolik pres
- **Üretici:** Hidromak
- **Model:** HP-250
- **Kapasite:** 250 ton
- **Kurulum:** Üretim Hattı A, Bölge 2

---

## 1. Güvenlik

> ⚠️ **ÖNEMLİ:** Herhangi bir bakım veya arıza müdahalesinden önce **enerji kesme ve kilitleme (LOTO)** prosedürü uygulanmalıdır. Hidrolik sistemde basınç varken asla müdahale edilmez.

### 1.1 Enerji kesme ve kilitleme (LOTO) adımları
1. Presi durdur, ana şalteri `0` konumuna getir.
2. Ana şalteri kilitle ve kendi kilidini tak, etiketini as.
3. Hidrolik akümülatör basıncını boşaltma valfinden tahliye et (manometre `0 bar` göstermeli).
4. Koçun (ram) alt ölü noktada veya mekanik destek üzerinde olduğunu doğrula.

### 1.2 Kişisel koruyucu donanım
- Çelik burunlu ayakkabı, iş eldiveni, koruyucu gözlük zorunludur.

---

## 2. Periyodik bakım

| Periyot | İş |
|---|---|
| Günlük | Yağ seviyesi ve kaçak kontrolü; acil durdurma (E-stop) testi |
| Haftalık | Işık perdesi (ışık bariyeri) fonksiyon testi |
| Aylık | Hidrolik yağ sıcaklık ve basınç değerlerinin kaydı |
| 6 ayda bir | Hidrolik yağ filtresi değişimi; hortum ve rakor kontrolü |
| Yıllık | Hidrolik yağ değişimi (ISO VG 46); valf bakımı |

---

## 3. Alarm kodları

| Kod | Anlamı | İlk kontrol |
|---|---|---|
| E-101 | Hidrolik basınç düşük | Yağ seviyesi, pompa, basınç valfi |
| E-102 | Hidrolik yağ sıcaklığı yüksek | Soğutucu/fan, yağ seviyesi, ortam sıcaklığı |
| E-103 | Koç (ram) geri dönmüyor | Yön valfi, geri dönüş yayı/silindir, sensör |
| E-104 | Yağ seviyesi düşük | Depo seviyesi, kaçak kontrolü |
| E-105 | Acil durdurma (E-stop) aktif | E-stop butonları, reset |
| E-106 | Güvenlik ihlali (ışık perdesi/kapı) | Işık perdesi hizası, kapı sensörü |
| E-107 | Pompa motoru aşırı akım | Motor, kaplin, aşırı yük |
| E-108 | Basınç valfi arızası | Valf bobini, kablo, kirlilik |

---

## 4. Arıza giderme

### 4.1 E-101 — Hidrolik basınç düşük
1. LOTO uygula, sistemi emniyete al.
2. Hidrolik yağ seviyesini kontrol et; düşükse ISO VG 46 ile tamamla.
3. Pompa emiş filtresinde tıkanıklık olup olmadığına bak.
4. Basınç ayar valfinin (relief valve) ayarını ve sızdırmazlığını kontrol et.
5. Sorun sürerse pompa debisini ölç; pompa aşınmışsa değiştir.

### 4.2 E-102 — Hidrolik yağ sıcaklığı yüksek
1. Yağ soğutucu fanının çalıştığını doğrula.
2. Soğutucu peteklerini temizle, hava akışını kontrol et.
3. Yağ seviyesini kontrol et (düşük seviye ısınmayı artırır).
4. Ortam sıcaklığı 40°C üstündeyse havalandırmayı iyileştir.

### 4.3 E-103 — Koç (ram) geri dönmüyor
1. LOTO uygula.
2. Yön kontrol valfinin bobinini ve elektriksel bağlantısını kontrol et.
3. Geri dönüş silindiri/yayı mekanik olarak serbest mi, kontrol et.
4. Pozisyon sensörünün sinyal verdiğini doğrula.

### 4.4 E-105 — Acil durdurma aktif
1. Basılı kalan bir E-stop butonu var mı, tüm istasyonları kontrol et.
2. Butonu serbest bırak, panelden reset ver.
3. Reset sonrası alarm sürerse E-stop röle/kontak devresini ölç.
