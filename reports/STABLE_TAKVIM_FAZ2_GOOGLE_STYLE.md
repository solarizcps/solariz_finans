# STABLE — TAKVİM FAZ2 GOOGLE STYLE

> **Tarih:** 5 Haziran 2026  
> **Stable yedek:** `D:\finans_BACKUP_STABLE_TAKVIM_FAZ2_GOOGLE_STYLE_20260605` (14 dosya / 1029 KB)  
> **DB:** Dokunulmadı | **finans_server.py:** Dokunulmadı | **CPS:** Dokunulmadı

---

## Stable Kontrol Sonuçları

| Kontrol | Sonuç |
|---------|-------|
| Takvim açılıyor mu? | ✅ HTTP 200, sunucu hatası yok |
| `renderCalSidebar` fonksiyonu | ✅ |
| `goToday` (Bugün butonu) | ✅ |
| `renderCalendar` (event kartları) | ✅ |
| Filtre checkboxları (4 adet) | ✅ |
| Sağ panel `cal-sidebar-list` | ✅ |
| CSS `.cal-event` | ✅ |
| CSS `.cal-event-more` | ✅ |
| CSS `.cal-sidebar` | ✅ |
| CSS `.cal-sb-item` | ✅ |
| CSS `.cal-filters` | ✅ |
| `/api/odemeler` (715 kayıt) | ✅ |
| Bekleyen kayıtlar (136) | ✅ |
| Faz1 stable yedek koruması | ✅ |
| Linter hatası | ✅ Sıfır |

---

## Değişen Dosya

`D:\finans\finans_yonetim.html` — tek dosya, ~160 satır değişim/ekleme

---

## Event Kart Sistemi

### Gün Kutusu
- `min-height`: 72px → **110px**
- Her gün içinde max **3 event kartı** görünür
- 3'ten fazla varsa **`+N daha`** badge gösterilir
- Bugünün numarası **mavi daire** içinde

### Event Kart Yapısı (`.cal-event`)
```css
border-radius: 3px; padding: 2px 5px;
font-size: 10px; font-weight: 600; color: #fff;
white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
```
- Açıklama 16 karakterde kesilir, `title` tooltip'i tam metni gösterir
- Tıklanınca `showCalDay()` açılır

### Renk Mantığı (Faz1'den Korundu)

| Tip | Renk |
|-----|------|
| Gecikmiş (tüm tipler) | 🔴 `#dc2626` |
| Kredi / Taksit | 🔵 `#2563eb` |
| Çek (`Çek:` prefix) | 🟣 `#7c3aed` |
| Tedarikçi (çek değil) | 🟠 `#ea580c` |
| Maaş | 🔷 `#0891b2` |
| Tahsilat | 🟢 `#16a34a` |

---

## Filtre Checkboxları

| ID | Etiket | Renk |
|----|--------|------|
| `#cf-odemeler` | Ödemeler | 🟠 `#ea580c` |
| `#cf-cekler` | Çekler | 🟣 `#7c3aed` |
| `#cf-krediler` | Krediler | 🔵 `#2563eb` |
| `#cf-tahsilat` | Tahsilatlar | 🟢 `#16a34a` |

`onchange` → `calFilters.X = this.checked` → `renderCalendar()` — anlık güncelleme.

---

## Sağ Panel — En Yakın Finans Hareketleri

Eski yapı (6 KPI kart) → Yeni yapı (event listesi):

| Alan | Değer |
|------|-------|
| Gösterilen kayıt sayısı | Max 30 |
| Sıralama | Gecikmiş önce → Tarih artan |
| Her satır | Gün+Ay + Tip badge + Açıklama + Tutar |
| Tıklanınca | `showCalDay()` açılır |
| Kaydırma | `max-height: 620px`, overflow-y: auto |
| Filtre uyumu | `calFilters` state'e bağlı |

---

## Korunan Fonksiyonlar (Değişmedi)

| Fonksiyon | Açıklama |
|-----------|---------|
| `calTipRenk(o)` | Renk mantığı — korundu |
| `fmtK(n)` | Tutar kısaltma — korundu |
| `changeCalMonth(dir)` | Ay navigasyonu — korundu |
| `showCalDay(dateStr)` | Tıklama detayı — korundu |

---

## Yedek Geçmişi

| Yedek | Durum |
|-------|-------|
| `D:\finans_BACKUP_STABLE_TAKVIM_FAZ1_20260605` | ✅ Korunuyor |
| `D:\finans_BACKUP_BEFORE_FAZ2_TAKVIM_20260605` | ✅ Korunuyor |
| `D:\finans_BACKUP_STABLE_TAKVIM_FAZ2_GOOGLE_STYLE_20260605` | ✅ Bu stable |

---

## Korunacak Kurallar

- `calTipRenk()` renk fonksiyonu — **değiştirilmeyecek**
- Çek ayrımı: `aciklama.indexOf('ek:') === 1` — **değiştirilmeyecek**
- `calFilters` state varsayılanı: hepsi `true` (tüm tipler açık)
- Event kart max görünüm: `MAX_EVENTS = 3` — ihtiyaçta artırılabilir
- `fmtK()` sidebar tutarları için kullanılıyor — **değiştirilmeyecek**
- DB şeması değişmedi, entity kolonları korundu

---

*Stable: `D:\finans_BACKUP_STABLE_TAKVIM_FAZ2_GOOGLE_STYLE_20260605`*
