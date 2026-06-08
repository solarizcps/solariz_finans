# TAKVİM FİNANS DÖNÜŞÜM ANALİZ RAPORU

> **Tarih:** 5 Haziran 2026  
> **Kapsam:** `D:\finans` bağımsız finans sistemi  
> **Hedef:** Takvim sekmesi → Finans karar ekranı  
> **Kod değişikliği:** Onay bekleniyor.

---

## 1. Mevcut Yapı

### Takvim Fonksiyonu

| Bileşen | Detay |
|---------|-------|
| **Ana fonksiyon** | `renderCalendar()` — satır 2927 |
| **Gün tıklama** | `showCalDay(dateStr)` — satır 2972 |
| **Ay değiştirme** | `changeCalMonth(dir)` — satır 2959 |
| **Başlangıç değerleri** | `calMonth = new Date().getMonth()` (satır 1579) · `calYear = new Date().getFullYear()` (satır 1580) |

### Veri Akışı

```
Sayfa açılışı:
  reloadCache()
    → GET /api/odemeler      → _cache.odemeler (715 kayıt, RAM)
    → GET /api/krediler      → _cache.krediler (27 kayıt, RAM)

renderCalendar() çalışınca:
  entityData() → odemeler array (filtre kaldırıldı, artık 715'in tamamı)
  Her gün için: odemeler.filter(o => o.vade === dateStr)
  Sadece odemeler tablosu → sadece nokta gösterimi
```

### Kullanılan API ve Tablo

| Kaynak | Kullanım |
|--------|---------|
| `GET /api/odemeler` | Sayfa açılışında yükleniyor, sonra RAM'de |
| `odemeler` tablosu | Tek kaynak — tüm tipler burada |
| `krediler` tablosu | Takvimde **kullanılmıyor** (RAM'de var ama çizilmiyor) |
| `planlama` tablosu | Takvimde **kullanılmıyor** |
| `kasa` tablosu | Takvimde **kullanılmıyor** |

### Mevcut Renk Mantığı

| Durum | Renk | CSS Değişkeni |
|-------|------|---------------|
| `odendi` | Yeşil | `var(--green)` |
| `durum != odendi AND daysUntil < 0` | Kırmızı | `var(--red)` |
| Diğer bekliyor | Turuncu | `var(--orange)` |
| **Tip ayrımı (kredi/çek/tahsilat)** | **Yok** | — |

### Mevcut CSS Yapısı

```css
.calendar-grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 3px; }
.cal-day        { aspect-ratio: 1; padding: 4px; /* KÜÇÜK KARE */ }
.cal-day .day-dots { /* sadece 5px nokta */ }
```

**Sorun:** `aspect-ratio: 1` → kare kutular, sadece 4 nokta sığıyor. Tutar, açıklama, günlük net gösterilemiyor.

### Sabit/Demo Veri

**Yok.** Takvim tamamen `odemeler` DB verisinden çiziliyor.

### Mevcut Sağ Panel

Takvim sekmesinde sağ panel **yok**. Özet sekmesinde `renderUpcoming()` (30 günlük yaklaşan liste) var — takvimle bağlantısı yok.

---

## 2. Hangi Tablolar Bağlanacak?

### Yeni Hedef Veri Haritası

| Gösterilecek | Kaynak Tablo | Mevcut Bağlantı | Gerekli İşlem |
|-------------|-------------|-----------------|---------------|
| **Ödemeler** | `odemeler` | ✅ Var | Renk ayrımı ekle |
| **Krediler / Taksitler** | `odemeler` WHERE `tip='taksit'` | ⚠️ Var ama renksiz | Mavi renk + banka etiketi |
| **Çekler** | `odemeler` WHERE `tip='tedarikci'` AND `aciklama LIKE '%ek:%'` | ⚠️ Var ama renksiz | Mor renk + çek etiketi |
| **Tahsilat (giriş)** | `planlama` WHERE `kategori='gelir'` | ❌ Yok | Yeni: planlama API çağrısı |
| **Günlük net** | `odemeler` (giden) + `planlama.gelir` (gelen) | ❌ Yok | Hesaplama ekle |
| **Kasa hareketleri** | `kasa` | ❌ Yok (tablo boş) | Şimdilik gerek yok |

### Tablo Renk Eşleşmesi (Yeni)

| Tip | Renk | Kaynak |
|-----|------|--------|
| `odemeler.tip='taksit'` | Mavi `#2563eb` | Kredi/banka taksiti |
| `odemeler.tip='tedarikci'` + `Çek:` prefix | Mor `#7c3aed` | Verilen çek |
| `odemeler.tip='tedarikci'` (çek değil) | Turuncu `#ea580c` | Tedarikçi ödeme |
| `odemeler.tip='maas'` | Mavi-gri `#0891b2` | Maaş |
| `odemeler.tip='vergi'` | Turuncu kırmızı `#dc2626` | Vergi |
| `odemeler.tip='diger'` | Gri | Diğer |
| `planlama.kategori='gelir'` | Yeşil `#16a34a` | Tahsilat/giriş |
| Gecikmiş (tüm tipler) | Kırmızı `#dc2626` | Durum override |

---

## 3. Eksik Veri Analizi

### Mevcut DB Durumu (5 Haziran 2026 itibarıyla)

**Önümüzdeki 30 gün ödeme:**
| Tip | Kayıt | Toplam |
|-----|-------|--------|
| taksit (kredi) | 8 | 2.703.674 TL |
| tedarikci | 5 | 685.349 TL |
| kredi | 1 | 84.000 TL |

**Gecikmiş ödemeler:**
| Tip | Kayıt | Toplam |
|-----|-------|--------|
| diger | 17 | 5.870.100 TL |
| kredi | 19 | 7.812.679 TL |
| maas | 3 | 502.104 TL |
| taksit | 15 | 5.879.045 TL |
| tedarikci | 13 | 8.878.566 TL |

**Bu ay çek (Çek: prefix):** 5 adet — hepsi 30 Haziran vadeli  
- Çek: Pera — 210.117 TL  
- Çek: Altuğ Kimya — 200.000 TL  
- Çek: Nexgen Kimya (2x) — 175.232 TL  
- Çek: Güney Rulman — 100.000 TL  

**Planlama gelir (tahsilat) — önümüzdeki 30 gün:** **0 kayıt**  
> Tüm gelir kayıtları 2026 Ocak–Nisan dönemine ait; gelecek tahsilat girilmemiş.

### Eksikler

| Eksik | Etki | Çözüm |
|-------|------|-------|
| `planlama.gelir` boş (gelecek yok) | Tahsilat satırı takvimde görünmez | Kullanıcı yeni tahsilat eklemeli |
| `kasa` tablosu boş | Günlük açılış bakiyesi hesaplanamaz | Kasa bakiyesi girilmeli |
| Çek no / banka alanı yok | Çek detayı sınırlı | Sonraki fazda eklenecek |
| Takvim kutucukları `aspect-ratio:1` | Tutar/açıklama yazılamıyor | CSS değiştirilmeli |

---

## 4. Minimum Değişiklik Planı

### Değişmeyecekler
- Tablo şemaları (`odemeler`, `planlama`) — dokunulmaz
- `renderCalendar()` temel yapısı — genişletilecek
- `showCalDay()` detay popup — genişletilecek
- `changeCalMonth()` — değişmez

### Değişiklik Listesi (7 adım)

---

#### DEĞİŞİKLİK 1 — Takvim CSS: Kare → Dikdörtgen

**Dosya:** `finans_yonetim.html` satır ~449  
**Mevcut:** `aspect-ratio: 1; padding: 4px;`  
**Yeni:** `min-height: 80px; padding: 6px; align-items: flex-start;`

> Kutucuklar yükseltilince tutar ve etiket yazılabilir.

---

#### DEĞİŞİKLİK 2 — Tahsilat Verisi RAM'e Yükle

**Dosya:** `finans_yonetim.html` — `reloadCache()` satır 1556  
**Eklenecek:**
```javascript
var plan = apiGet('/api/planlama');
_planCache = plan || [];  // zaten var, ama takvim kullanmıyor
```
> `_planCache` zaten yükleniyor. Takvim fonksiyonundan erişilecek.

---

#### DEĞİŞİKLİK 3 — `renderCalendar()` Tip + Renk Ayrımı

**Mevcut:** Tek renk (durum bazlı)  
**Yeni mantık:**
```javascript
// Her ödeme için renk:
var renk = o.durum !== 'odendi' && daysUntil(o.vade) < 0
    ? '#dc2626'  // gecikmiş — her zaman kırmızı
    : o.tip === 'taksit'                          ? '#2563eb'  // mavi — kredi
    : o.tip === 'tedarikci' && isCek(o.aciklama) ? '#7c3aed'  // mor — çek
    : o.tip === 'tedarikci'                       ? '#ea580c'  // turuncu — tedarikçi
    : o.tip === 'maas'                            ? '#0891b2'  // teal — maaş
    : '#6b7280';  // gri — diğer

// Tahsilat için (planlama gelir):
var tahsilatRenk = '#16a34a';  // yeşil
```

---

#### DEĞİŞİKLİK 4 — Günlük Net Hesabı

**Gün kutusuna eklenecek:**
```javascript
var gunGiden = dayPayments
    .filter(o => o.durum !== 'odendi')
    .reduce((s,o) => s + parseFloat(o.tutar||0), 0);
var gunGelen = dayPlan  // planlama.gelir, aynı tarih
    .reduce((s,p) => s + parseFloat(p.tutar||0), 0);
var net = gunGelen - gunGiden;
// net > 0 → yeşil, net < 0 → kırmızı, net = 0 → gösterme
```

---

#### DEĞİŞİKLİK 5 — Gün Detayında Tüm Tipler

**`showCalDay()` güncellemesi:**  
Mevcut: yalnızca `odemeler` satırları  
Yeni:
- `odemeler` → ödeme satırları (tip rozeti ile)
- `planlama.gelir` → tahsilat satırları (yeşil arka plan)
- Gün özeti: Toplam giden / Toplam gelen / Net

---

#### DEĞİŞİKLİK 6 — Sağ Panel: Bugün / 7 Gün / 30 Gün KPI

**Dosya:** `finans_yonetim.html` — tab-takvim HTML bloğu (~satır 941)  
**Mevcut:** Sağ panel yok — takvim tek sütun  
**Yeni:** 2 sütun layout (takvim sol, KPI panel sağ)

```
Sağ panel içeriği:
┌────────────────────────────┐
│ Bugün çıkacak:  ₺X.XXX     │
│ 7 gün ödeme:    ₺XX.XXX    │
│ 30 gün ödeme:   ₺XXX.XXX   │
├────────────────────────────┤
│ Bekleyen çek:   ₺XX.XXX    │
│ Taksit:         ₺XX.XXX    │
│ Tedarikçi:      ₺XX.XXX    │
├────────────────────────────┤
│ Gecikmiş toplam:₺XXX.XXX   │
│ En yakın 5 ödeme listesi   │
└────────────────────────────┘
```

---

#### DEĞİŞİKLİK 7 — Panel Başlığı Güncelleme

**Mevcut:** `📅 Ödeme Takvimi`  
**Yeni:** `📅 Finans Takvimi — Şahin Taban AYK`

---

### Etkilenen Dosyalar

| Dosya | Değişiklik Sayısı | DB Değişimi |
|-------|------------------|-------------|
| `finans_yonetim.html` | 7 adım | Hayır |
| `finans_server.py` | 0 | Hayır |
| `finans.db` | 0 | Hayır |

---

## 5. Riskler

| Risk | Olasılık | Etki | Önlem |
|------|----------|------|-------|
| **CSS kare→dikdörtgen kırılması** | Orta | Takvim çizimi bozulabilir | CSS değişikliği öncesi test |
| **`_planCache` tarihleri** | Düşük | Planlama tarihleri `tarih` kolonu — `vade` değil | `tarih` alanıyla eşleşme |
| **Çek ayrımı false-positive** | Düşük | `aciklama LIKE '%ek:%'` → yanlış eşleşme | Prefix `Çek:` kontrolü `indexOf('ek:') === 1` |
| **Planlama gelir verisi boş** | Yüksek | Tahsilat satırları takvimde görünmez | Kullanıcı uyarısı ekle; gelecek tahsilat girişi gerekiyor |
| **Kasa tablosu boş** | Yüksek | Günlük açılış bakiyesi hesaplanamaz | Bakiye hardcoded kalır (2.5M TL sorunu korunur) |
| **Senkron XHR performans** | Orta | Ay geçişinde 715 kayıt re-filter — hızlı ama | RAM'de filtreleme, API çağrısı yok — kabul edilebilir |

---

## Özet: Önce Yapılacaklar

1. `aspect-ratio:1` CSS → `min-height:80px` (kutucuk boyutu)
2. `renderCalendar()` içine tip bazlı renk mantığı
3. Gün kutusuna tutar + net satırı
4. `showCalDay()` → tahsilat satırları + özet
5. Sağ panel HTML → Bugün/7gün/30gün KPI
6. Panel başlığı güncelleme

---

*Rapor: `D:\finans\reports\TAKVIM_FINANS_DONUSUM_ANALIZ.md` — Kod değişikliği için onay bekleniyor.*
