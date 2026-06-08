# TAKVİM FAZ2 — GOOGLE CALENDAR TARZI TASARIM ANALİZİ

> **Tarih:** 5 Haziran 2026  
> **Mevcut Stable:** `D:\finans_BACKUP_STABLE_TAKVIM_FAZ1_20260605`  
> **Kapsam:** `D:\finans\finans_yonetim.html`  
> **DB:** Dokunulmayacak | **CPS:** Dokunulmayacak

---

## 1. Mevcut Yapı (Faz1 Stable)

### CSS — Takvim Bölümü (satır 433–483)

```css
.calendar-grid { display:grid; grid-template-columns:repeat(7,1fr); gap:3px; }
.cal-day       { min-height:72px; padding:5px 6px; overflow:hidden; }
/* İçerik: gün numarası + nokta dizisi + küçük tutar metni */
.cal-day .day-dots { ... }        /* renkli nokta dizisi */
.cal-day .day-tutar { font-size:9px; } /* çok küçük tutar */
.cal-kpi-panel { ... }            /* sağ panel: 6 KPI kartı */
```

**Sorun:** `min-height:72px` + `font-size:9px` nokta+tutar yaklaşımı → kalabalık, okunaksız.  
Google Calendar'da her event kendi satırında kart olarak durur.

### HTML Yapısı (satır 953–1039)

```
tab-takvim
├── sol kolon (flex:1)
│   ├── panel-header (başlık + ay nav)
│   ├── renk açıklaması (6 küçük nokta)
│   ├── cal-header-row (Pzt Sal ... Paz)
│   ├── cal-grid (gün kutuları)
│   └── cal-detail-panel (seçili gün detayı — panelin ALTINDA)
└── sağ kolon (min-width:180px)
    └── cal-kpi-panel (6 KPI kartı: Bugün/7Gün/30Gün/Çek/Taksit/Gecikmiş)
```

**Eksikler:**
- Üst filtre checkbox'ları yok
- "Bugün" butonu yok
- Sağ panel KPI kartları, istenen "En Yakın Finans Hareketleri" listesi değil

### JavaScript Fonksiyonları

| Fonksiyon | Satır | İş | Faz2'de |
|-----------|-------|----|---------|
| `calTipRenk(o)` | 3036 | Renge karar verir | ✅ KORUNACAK |
| `renderCalendar()` | 3047 | Grid oluşturur | ⚠️ BÜYÜK DEĞİŞİM |
| `fmtK(n)` | 3105 | Tutar kısaltma | ✅ KORUNACAK |
| `renderCalKPI()` | 3113 | Sağ panel 6 KPI | 🔄 YENİDEN YAZILACAK |
| `changeCalMonth()` | 3145 | Ay navigasyonu | ✅ KORUNACAK |
| `showCalDay()` | 3152 | Tıklama detayı | ⚠️ GÜNCELLENECEk |

### Veri Kaynakları (Faz2'de Değişmiyor)

| Kaynak | Kullanım |
|--------|---------|
| `entityData().odemeler` | Ödemeler, çekler, krediler (tip bazlı) |
| `_planCache` (kategori='gelir') | Tahsilatlar |
| `calYear`, `calMonth` | Gösterilen ay |
| `daysUntil(vade)` | Gecikme hesabı |

---

## 2. Google Calendar Yapısı — Ne Değişir?

### 2.1 — Cal-Day: Kutular Büyüyecek

**Mevcut:**
```css
.cal-day { min-height: 72px; padding: 5px 6px; }
/* İçerik: sayı + 6 nokta + 9px yazı */
```

**Yeni (Google Cal tarzi):**
```css
.cal-day { min-height: 120px; padding: 4px 4px 6px; }
/* İçerik: sayı + event kart dizisi */
.cal-event {
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 1px 0;
  cursor: pointer;
}
.cal-day-num-wrap { /* bugün için daire */
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--accent); /* sadece bugün */
  color: #fff; display:flex; align-items:center; justify-content:center;
}
```

**Değişen CSS satırı sayısı:** ~25 satır değişim / ~20 satır ekleme = ~45 satır

### 2.2 — Event Kartları (renderCalendar değişimi)

**Mevcut gün kutusu:**
```html
<div class="cal-day">
  <div class="day-num">15</div>
  <div class="day-dots">●●●</div>
  <div class="day-tutar">-750K</div>
</div>
```

**Yeni Google Cal tarzi:**
```html
<div class="cal-day">
  <div class="day-num-wrap">15</div>
  <div class="cal-event" style="background:#dc2626">🔴 ABC Firma ₺250K</div>
  <div class="cal-event" style="background:#7c3aed">🟣 Çek ₺750K</div>
  <div class="cal-event" style="background:#2563eb">🔵 Kredi ₺120K</div>
  <div class="cal-event-more">+2 daha</div>  <!-- overflow için -->
</div>
```

**`renderCalendar()` değişimi:**
- Mevcut: 55 satır, nokta + toplam tutar
- Yeni: ~90 satır, event kart döngüsü + overflow (+N daha) + filtre kontrolü

**Kritik detay — kaç event sığar?**  
`min-height:120px` ile gün kutusuna yaklaşık 3-4 event kartı sığar. 5+ olursa `+N daha` gösterilmeli.

### 2.3 — Filtre State Değişkeni (Yeni)

```javascript
var calFilters = { odemeler: true, cekler: true, krediler: true, tahsilat: true };
```

Checkbox `onchange` → `calFilters.X = !calFilters.X` → `renderCalendar()`

Filtreleme:
- `odemeler`: tip = tedarikci (çek olmayan) + maas + vergi + diger
- `cekler`: tip = tedarikci + aciklama 'Çek:' ile başlıyor
- `krediler`: tip = taksit veya kredi
- `tahsilat`: _planCache kategori='gelir'

### 2.4 — Sağ Panel: En Yakın Finans Hareketleri (renderCalKPI → renderCalSidebar)

**Mevcut:** 6 KPI kartı (Bugün/7Gün/30Gün/Çek/Taksit/Gecikmiş)  
**Yeni:** Tarih sıralı event listesi (bugünden itibaren)

```html
<div class="cal-sidebar">
  <div class="cal-sidebar-title">📌 En Yakın Hareketler</div>
  <div id="cal-sidebar-list">
    <!-- renderCalSidebar() tarafından doldurulur -->
    <div class="cal-sb-item">
      <span class="cal-sb-date">15 Haz</span>
      <span class="cal-sb-badge" style="background:#7c3aed">Çek</span>
      <span class="cal-sb-aciklama">Viyolet Matbaa</span>
      <span class="cal-sb-tutar">₺750K</span>
    </div>
    ...
  </div>
</div>
```

Gösterilecek kayıt: `bugünden >= tarih`, sıralı, ilk 20 kayıt.

### 2.5 — Bugün Butonu (Yeni)

```html
<div class="month-nav">
  <button onclick="changeCalMonth(-1)">‹</button>
  <span class="month-label" id="cal-month-label">-</span>
  <button onclick="changeCalMonth(1)">›</button>
  <button onclick="goToday()">Bugün</button>   <!-- YENİ -->
</div>
```

```javascript
function goToday() {
  calYear = today.getFullYear();
  calMonth = today.getMonth();
  renderCalendar();
}
```

---

## 3. Etkilenen Bileşenler — Tam Liste

| Bileşen | Etki | Satır Tahmini |
|---------|------|--------------|
| CSS `.cal-day` | Yükseklik, padding değişimi | ~5 satır değişim |
| CSS `.cal-event` (yeni sınıf) | Event kart stili | ~12 satır ekleme |
| CSS `.cal-day-num-wrap` (yeni) | Bugün dairesi | ~8 satır ekleme |
| CSS `.cal-sidebar` (yeni) | Sağ panel listesi | ~15 satır ekleme |
| CSS `.cal-kpi-panel` | Kaldırılacak veya korunacak | ~5 satır değişim |
| HTML `tab-takvim` üst kısım | Filtre checkboxları + Bugün butonu | ~15 satır ekleme |
| HTML `cal-kpi-panel` | Yeni sidebar yapısına dönüşüm | ~20 satır değişim |
| HTML renk açıklaması satırı | Güncellenecek | ~5 satır değişim |
| HTML `cal-detail-panel` | Korunacak (tıklama detayı) | Değişim yok |
| JS `calFilters` değişkeni | Yeni state | ~3 satır ekleme |
| JS `renderCalendar()` | Büyük yeniden yazım | ~90 satır (55→90) |
| JS `renderCalKPI()` → `renderCalSidebar()` | Yeniden yazım | ~50 satır (30→50) |
| JS `goToday()` | Yeni fonksiyon | ~5 satır ekleme |
| JS `changeCalMonth()` | Değişim yok | 0 |
| JS `calTipRenk()` | Değişim yok | 0 |
| JS `fmtK()` | Değişim yok | 0 |
| JS `showCalDay()` | Küçük güncelleme (filtre uyumu) | ~5 satır değişim |

**Toplam tahmini değişim:** ~240 satır (değişim + ekleme)  
**Etkilenen dosya:** Sadece `finans_yonetim.html`  
**DB değişikliği:** Sıfır  
**Backend değişikliği:** Sıfır

---

## 4. Risk Analizi

### Düşük Risk ✅
- Veri kaynakları değişmiyor (`entityData()`, `_planCache`)
- Renk kodları korunuyor (`calTipRenk()`)
- Ay navigasyonu korunuyor (`changeCalMonth()`)
- `showCalDay()` sadece küçük güncelleme alıyor
- Diğer sekmeler (Ödemeler, Krediler, Çekler, Planlama) ETKİLENMİYOR

### Orta Risk ⚠️
| Risk | Açıklama | Önlem |
|------|---------|-------|
| Event overflow | Ayda yoğun günlerde 10+ event olabilir (ör: 1 Haziran 15 taksit var) | `+N daha` göster, max 3-4 kart sığar |
| Kutu yüksekliği | 6 haftalı ay = 6 satır × 120px = 720px → sayfa uzar | `min-height:120px` yerine `height:calc((100vh - 300px)/6)` denenebilir |
| Filtre state | `calFilters` uygulama yüklenince sıfırlanır | localStorage'a kaydetmek gerekebilir (Faz3) |
| Sidebar performans | 715 kayıt tarih sıralaması | `sort()` + ilk 25 kayıt göster |

### Yüksek Risk ❌
- **YOK** — tüm değişiklikler client-side, DB ve API etkilenmiyor

---

## 5. Minimum Değişiklik Planı (Seçenek Karşılaştırması)

### Seçenek A — Tam Google Cal (önerilen)
- Event kartları, Bugün butonu, filtre checkboxları, sidebar liste
- ~240 satır değişim
- Görsel fark maksimum

### Seçenek B — Yarım Yol
- Sadece event kartları (filtre ve sidebar yok)
- ~120 satır değişim
- Faz2b olarak filtre ve sidebar eklenebilir

### Seçenek C — Minimal
- Sadece kutu yüksekliği büyütme + event kart stili
- ~60 satır değişim
- Checkbox ve sidebar sonraya bırakılır

---

## 6. Uygulama Sırası (Onay Gelirse)

1. **Yedek al:** `D:\finans_BACKUP_BEFORE_FAZ2_YYYYMMDD`
2. **CSS:** `.cal-day` yükseklik + `.cal-event` sınıfı + sidebar stilleri
3. **HTML:** Filtre checkboxları + Bugün butonu + sidebar HTML
4. **JS:** `calFilters` state + `renderCalendar()` event kartları + `goToday()`
5. **JS:** `renderCalKPI()` → `renderCalSidebar()` yeniden yazım
6. **Test:** Haziran 2026, filtreleme, Bugün butonu, sidebar sıralaması

---

## 7. Mevcut Veri Dağılımı (Takvimde Gösterilecek)

| Kaynak | Bekleyen | Gösterim |
|--------|---------|---------|
| `odemeler` (tedarikci, çek olmayan) | ~90 kayıt | Turuncu kart |
| `odemeler` (çek — tip=tedarikci + Çek:) | 22 bekleyen | Mor kart |
| `odemeler` (taksit + kredi) | ~66 bekleyen | Mavi kart |
| `_planCache` (kategori=gelir) | 36 kayıt | Yeşil kart |
| Toplam aktif görüntülenecek | ~214 kayıt | — |

En yoğun tahmin: aylık ~30-40 event → ortalama gün başına 1-2 kart. Sığdırılabilir.

---

## 8. Önerilen Yapı Diyagramı

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 Finans Takvimi   [‹] Haziran 2026 [›]  [Bugün]             │
│  ☑ Ödemeler  ☑ Çekler  ☑ Krediler  ☑ Tahsilatlar             │
├────────────────────────────────────────────┬────────────────────┤
│                                            │ 📌 En Yakın        │
│  Pzt   Sal   Çar   Per   Cum   Cmt   Paz  │ Hareketler         │
│ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ │ ─────────────────  │
│ │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │ │ 6 │ │ 7 │ │ 10 Haz            │
│ │🔵 │ │   │ │🔴 │ │   │ │   │ │   │ │   │ │ 🟣 Çek            │
│ │Krd│ │   │ │Öd │ │   │ │   │ │   │ │   │ │ Viyolet ₺750K     │
│ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ │ ─────────────────  │
│ ┌───┐ ┌─⬤─┐ ...                           │ 15 Haz            │
│ │   │ │(5)│ bugün dairesi                  │ 🔵 Taksit         │
│ │   │ │🟣 │                                │ Garanti ₺225K     │
│ │   │ │+2 │ ← overflow                     │ ─────────────────  │
│ └───┘ └───┘                                │ ...               │
├────────────────────────────────────────────┤                    │
│  ▼ Seçili Gün Detayı (tıklanınca açılır)  │                    │
└────────────────────────────────────────────┴────────────────────┘
```

---

## 9. Sonuç

**Faz2 uygulanabilir.** Tek dosya değişimi, DB yok, backend yok.

| Alan | Değer |
|------|-------|
| Etkilenen dosya | `finans_yonetim.html` (tek) |
| Toplam değişim tahmini | ~240 satır |
| DB değişikliği | Sıfır |
| Backend değişikliği | Sıfır |
| Faz1 stable bozulur mu | Hayır (yedek alınarak korunur) |
| En büyük risk | Event overflow — `+N daha` ile yönetilir |
| Öneri | Seçenek A (tam Google Cal) tek seferde |

**Kod değişikliği için onay bekliyor.**

---

*Rapor: `D:\finans\reports\TAKVIM_FAZ2_GOOGLE_STYLE_ANALIZ.md`*
