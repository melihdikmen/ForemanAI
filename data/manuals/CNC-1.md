# CNC Torna CNC-1 — Bakım ve Arıza Giderme Kılavuzu

- **Makine kodu:** CNC-1
- **Tip:** CNC torna
- **Üretici:** Tezmak
- **Model:** TL-500
- **Kurulum:** Üretim Hattı B, Bölge 2

---

## 1. Güvenlik

> ⚠️ **ÖNEMLİ:** Tabla, taret veya ayna bölgesine müdahaleden önce **enerji kesme ve kilitleme (LOTO)** uygulanır. Dönen parça durmadan kapı açılmaz.

### 1.1 Enerji kesme ve kilitleme (LOTO) adımları
1. Çevrimi durdur, ana şalteri `0` konumuna getir ve kilitle.
2. Pnömatik besleme valfini kapat, basıncı tahliye et.
3. İş milinin (spindle) tamamen durduğunu doğrula.

### 1.2 Kişisel koruyucu donanım
- Koruyucu gözlük, iş eldiveni, çelik burunlu ayakkabı zorunludur. Talaş bölgesinde eldivenle dönen parçaya dokunulmaz.

---

## 2. Periyodik bakım

| Periyot | İş |
|---|---|
| Günlük | Soğutma sıvısı seviyesi; talaş temizliği; yağlama basıncı |
| Haftalık | Kızak ve kılavuzların yağ film kontrolü |
| Aylık | Ayna (chuck) basıncı ve kavrama testi |
| 6 ayda bir | Soğutma sıvısı değişimi; filtre temizliği |
| Yıllık | İş mili rulman kontrolü; kayış gerginliği |

---

## 3. Alarm kodları

| Kod | Anlamı | İlk kontrol |
|---|---|---|
| A-201 | İş mili (spindle) aşırı yük | Kesme parametreleri, takım körlüğü, kavrama |
| A-202 | İş mili aşırı sıcaklık | Soğutma, rulman, yağlama |
| A-203 | Eksen servo hatası | Servo sürücü, enkoder, kablo |
| A-204 | Yağlama basıncı düşük | Yağ seviyesi, pompa, hat tıkanıklığı |
| A-205 | Soğutma sıvısı akışı yok | Pompa, filtre, seviye |
| A-206 | Taret konumlama hatası | Taret indeks sensörü, pnömatik basınç |
| A-207 | Ayna (chuck) basıncı düşük | Hidrolik/pnömatik basınç, kaçak |
| A-208 | Kapı güvenlik ihlali | Kapı kilidi, sensör |

---

## 4. Arıza giderme

### 4.1 A-201 — İş mili aşırı yük
1. Çevrimi durdur, LOTO uygula.
2. Takımın körlüğünü/kırığını kontrol et, gerekirse değiştir.
3. Kesme hızı ve ilerleme değerlerini azalt.
4. İş parçasının aynada doğru kavrandığını doğrula.

### 4.2 A-202 — İş mili aşırı sıcaklık
1. Soğutma sıvısı akışını kontrol et.
2. İş mili yağlama basıncını doğrula.
3. Uzun süreli yüksek devirde rulman sıcaklığını izle; aşınma varsa rulman değiştir.

### 4.3 A-204 — Yağlama basıncı düşük
1. LOTO uygula.
2. Yağlama ünitesi yağ seviyesini kontrol et.
3. Yağlama pompasını ve hatlardaki tıkanıklığı kontrol et.
4. Basınç sensörünü doğrula.

### 4.4 A-205 — Soğutma sıvısı akışı yok
1. Soğutma pompasının çalıştığını doğrula.
2. Filtre ve emiş hattı tıkanıklığını kontrol et.
3. Sıvı seviyesini tamamla.
