# ŞİRKET MANTIĞI DEĞİŞİM ANALİZ RAPORU

> **Tarih:** 5 Haziran 2026  
> **Kapsam:** `D:\finans` bağımsız finans sistemi  
> **Hedef:** Üst şirket filtresi kaldırılacak → "Şahin Taban AYK Finans Konsolu"  
> **Karar:** Mevcut veriler silinmeyecek. Entity alanları korunacak. Sadece görünüm değişecek.  
> **Kod değişikliği:** Onay bekleniyor.

---

## 1. Şirket Seçimi Nerede Tutuluyor?

### A) HTML — Görsel Butonlar

**Dosya:** `finans_yonetim.html` satır 553–565

```html
<div class="entity-tabs">
  <button class="entity-tab active" data-entity="solariz" onclick="switchEntity('solariz')">Solariz</button>
  <button class="entity-tab" data-entity="nexgen"  onclick="switchEntity('nexgen')">NexGen</button>
  <button class="entity-tab" data-entity="pera"    onclick="switchEntity('pera')">Pera</button>
  <button class="entity-tab" data-entity="sahsi"   onclick="switchEntity('sahsi')">Şahsi</button>
</div>
```

Ayrıca **CSS** satır 36–39: her şirket için renk değişkeni:
```css
--solariz: #2563eb;
--nexgen:  #7c3aed;
--pera:    #ea580c;
--sahsi:   #16a34a;
```

Aktif tab CSS satır 104–107:
```css
.entity-tab.active[data-entity="solariz"] { background: #eff6ff; ... }
.entity-tab.active[data-entity="nexgen"]  { background: #f5f3ff; ... }
...
```

### B) JavaScript — `currentEntity` ve `entityData()`

**Dosya:** `finans_yonetim.html`

| Konum | Satır | İçerik |
|-------|-------|--------|
| Başlangıç değeri | 1588 | `var currentEntity = 'solariz';` |
| Değiştirme fonksiyonu | 1599 | `function switchEntity(e) { currentEntity = e; refreshAll(); }` |
| Filtreleme fonksiyonu | 1647 | `function entityData()` — tüm veriyi `currentEntity`'e göre filtreler |
| Yeni kayıt eklerken | 3049, 3394, 3418, 3558, 3577 | `entity: currentEntity` ile yazılıyor |

`entityData()` şu şekilde çalışıyor:
```javascript
function entityData() {
  var all = loadData();  // tüm 715 ödeme + 27 kredi
  return {
    odemeler: all.odemeler.filter(o => o.entity === currentEntity),
    krediler: all.krediler.filter(k => k.entity === currentEntity),
  };
}
```

**`entityData()` şu 10 render fonksiyonu tarafından çağrılıyor:**

| Fonksiyon | Satır | Ne Gösteriyor |
|-----------|-------|--------------|
| `renderAlerts` | 2310 | Gecikmiş/yaklaşan uyarılar |
| `renderSummaryCards` | 2338 | Özet KPI kartları (bu ay, gecikti, ödendi) |
| `renderUpcoming` | 2429 | Yaklaşan ödemeler listesi |
| `renderCreditSummary` | 2468 | Kredi özet kartları |
| `renderMonthlyChart` | 2501 | Aylık grafik |
| `renderOdemeler` | 2571 | Ödemeler sekmesi tam liste |
| `renderKrediler` | 2697 | Krediler sekmesi |
| `renderKasa` | 3059 | Kasa bakiyesi (API'ye `?entity=currentEntity` gönderir) |
| `renderCalendar` | 2942 | Takvim sekmesi |
| `renderNakit` | 3177 | Nakit akışı ekranı |

**`entityData()` KULLANMAYAN 2 fonksiyon:**

| Fonksiyon | Satır | Açıklama |
|-----------|-------|---------|
| `renderCekler` | 1696 | Tüm `odemeler`'den `Çek:` prefix'li kayıtları alıyor — entity filtresi yok |
| `renderPlanlama` | 1933 | `planlama` tablosundan alıyor; kendi `plan-firma-filter` dropdown'ı var |

### C) API — Server Tarafı

**Dosya:** `finans_server.py`

| Endpoint | Entity Kullanımı |
|----------|----------------|
| `GET /api/odemeler` | `?entity=` parametresi — boşsa tümünü döner |
| `GET /api/krediler` | `?entity=` parametresi — boşsa tümünü döner |
| `GET /api/kasa` | `?entity=` — zorunlu, varsayılan `'solariz'` |
| `GET /api/ozet` | `?entity=` — boşsa SQL hatası (bilinen bug) |
| `POST /api/odemeler` | `entity` alanı JSON body'den alınır |
| `POST /api/krediler` | `entity` alanı JSON body'den alınır |
| `POST /api/kasa` | `entity` alanı JSON body'den alınır |

### D) Veritabanı — Tablo Kolonları

| Tablo | Kolon Adı | Tip | Zorunlu |
|-------|-----------|-----|---------|
| `odemeler` | `entity` | TEXT | NOT NULL |
| `krediler` | `entity` | TEXT | NOT NULL |
| `kasa` | `entity` | TEXT | NOT NULL |
| `planlama` | `firma` | TEXT | — |

---

## 2. Hangi Tablolar Entity Kolonuna Bağlı?

### Mevcut DB Verisi (5 Haziran 2026)

**odemeler tablosu:**
| Entity | Kayıt | Toplam Tutar |
|--------|-------|-------------|
| solariz | 594 | 174.063.548 TL |
| sahsi | 118 | 35.135.140 TL |
| nexgen | 3 | 4.654.490 TL |

**krediler tablosu:**
| Entity | Kayıt | Toplam |
|--------|-------|--------|
| solariz | 27 | 55.271.979 TL |

**planlama tablosu (firma kolonu):**
| Firma | Kayıt | Toplam |
|-------|-------|--------|
| solariz | 346 | 106.560.837 TL |
| nexgen | 84 | 26.261.767 TL |
| pera | 24 | 927.472 TL |

**kasa tablosu:** 0 kayıt (entity kolonu var ama boş).

---

## 3. Üst Filtre Kaldırılırsa Etki Analizi

### Mevcut Sorun
`currentEntity = 'solariz'` varsayılan — filtre kaldırılmazsa:
- Nexgen (3 ödeme / 4.6M TL) hiçbir zaman görünmez
- Sahsi (118 ödeme / 35M TL) başka entity'e geçilmeden görünmez
- Krediler yalnızca solariz gösteriyor (nexgen/pera kredisi zaten yok)

### Filtre Kaldırılırsa Her Ekrana Etki

| Ekran / Fonksiyon | Etkilenir mi? | Etki Açıklaması |
|-------------------|-------------|----------------|
| **Özet kartları** | ✅ Evet | Şu an yalnızca solariz rakamı. Tümü gösterilince toplam artar |
| **Kredi toplamı** | ✅ Evet | Şu an: 55.2M TL (solariz). Tümü: Aynı (nexgen/pera kredisi yok) |
| **Çek toplamı** | ❌ Hayır | `renderCekler` zaten entity filtresi kullanmıyor |
| **Ödemeler listesi** | ✅ Evet | Solariz:594 + Sahsi:118 + Nexgen:3 = 715 kayıt görünür |
| **Nakit akışı** | ✅ Evet | 35M TL sahsi + 4.6M nexgen ödemesi de hesaba katılır |
| **12 Ay Planlama** | ❌ Hayır | Kendi `plan-firma-filter` var; entityData'ya bağlı değil |
| **Kasa** | ✅ Evet | API `/api/kasa?entity=currentEntity` gönderiliyor; entity kalkınca değişecek |
| **Takvim** | ✅ Evet | Tüm vadeleri gösterecek |
| **Uyarı banner'ı** | ✅ Evet | Tüm şirketlerin gecikmiş ödemeleri görünecek |

---

## 4. Minimum Değişiklik Planı

### Hedef
- Header'daki 4 entity butonu → "Şahin Taban AYK" başlığı
- Tüm veriler **aynı anda** gösterilecek (entity filtresi bypass)
- Kayıt içindeki `entity` alanı korunacak (silme yok)
- Yeni kayıt eklerken entity alanı: dropdown ile kullanıcı seçecek (ekleme modallarında hâlâ olacak)

### Değişecek Dosyalar

Yalnızca `finans_yonetim.html` — `finans_server.py` ve `finans.db`'ye dokunulmayacak.

---

### DEĞİŞİKLİK 1 — Header Başlığı ve Entity Tab'ları

**Konum:** Satır 549–566 (header logo + entity-tabs)

**Mevcut:**
```html
<div class="logo">FIN<span>.</span>KONSOL</div>
<div class="entity-tabs">
  <button class="entity-tab active" data-entity="solariz" onclick="switchEntity('solariz')">Solariz</button>
  <button class="entity-tab" data-entity="nexgen"  onclick="switchEntity('nexgen')">NexGen</button>
  <button class="entity-tab" data-entity="pera"    onclick="switchEntity('pera')">Pera</button>
  <button class="entity-tab" data-entity="sahsi"   onclick="switchEntity('sahsi')">Şahsi</button>
</div>
```

**Yeni:**
```html
<div class="logo">ŞAHİN TABAN AYK<span>.</span>FİNANS</div>
<div style="font-size:11px;color:var(--muted);padding:4px 12px;background:var(--surface2);border-radius:8px;border:1px solid var(--border);">
  Tüm Şirketler
</div>
```

---

### DEĞİŞİKLİK 2 — `entityData()` Fonksiyonu

**Konum:** Satır 1647–1652

**Mevcut:**
```javascript
function entityData() {
  var all = loadData();
  return {
    odemeler: all.odemeler.filter(o => o.entity === currentEntity),
    krediler: all.krediler.filter(k => k.entity === currentEntity),
  };
}
```

**Yeni (filtre yok, tümünü döndür):**
```javascript
function entityData() {
  var all = loadData();
  return {
    odemeler: all.odemeler,
    krediler: all.krediler,
  };
}
```

Bu tek değişiklik tüm 10 render fonksiyonunu etkiler — hepsi otomatik tüm şirket verisini gösterir.

---

### DEĞİŞİKLİK 3 — `currentEntity` Başlangıç Değeri

**Konum:** Satır 1588

**Mevcut:**
```javascript
var currentEntity = 'solariz';
```

**Yeni:**
```javascript
var currentEntity = 'solariz';  // Yeni kayıt ekleme modallarında varsayılan
```
> Değişmeyecek. `currentEntity` sadece yeni kayıt ekleme sırasında kullanılıyor (ekleme modallarında entity dropdown'u ile kullanıcı seçecek).

---

### DEĞİŞİKLİK 4 — `switchEntity()` Fonksiyonu (İsteğe Bağlı)

**Konum:** Satır 1599

Butonlar kaldırılınca `switchEntity` çağrılmayacak. Fonksiyon olduğu gibi bırakılabilir (zarar vermez).

---

### DEĞİŞİKLİK 5 — Kasa API Çağrısı

**Konum:** `renderKasa()` satır 3062

**Mevcut:**
```javascript
var res = apiGet('/api/kasa?entity=' + currentEntity);
```

**Yeni:**
```javascript
var res = apiGet('/api/kasa');  // Tüm kasa hareketleri
```

Server tarafı: `GET /api/kasa` entity parametresi yoksa tümünü döner (satır 201: `entity = request.args.get('entity', 'solariz')` — bu da değişmeli: varsayılan kalkmalı).

---

### Değişmeyecekler

| Bileşen | Durum |
|---------|-------|
| `finans.db` şeması | Dokunulmaz |
| `odemeler.entity` kolonu | Korunur |
| `krediler.entity` kolonu | Korunur |
| `planlama.firma` kolonu | Korunur |
| Ekleme modallarındaki entity/firma dropdown'ları | Korunur — kullanıcı kayıt eklerken şirket seçer |
| `renderCekler` | Zaten entity filtresi yok — değişmez |
| `renderPlanlama` firma filtresi | Kendi dropdown'u var — değişmez |
| CSS `--solariz`, `--nexgen` vb. renk değişkenleri | Korunur — kayıt renklerinde kullanılıyor |

---

## Özet: Değişiklik Sayısı

| # | Dosya | Satır | Değişiklik |
|---|-------|-------|-----------|
| 1 | `finans_yonetim.html` | ~549 | Header logo metni |
| 2 | `finans_yonetim.html` | ~553–565 | entity-tabs div → başlık span |
| 3 | `finans_yonetim.html` | 1648–1652 | `entityData()` filtresi kaldır |
| 4 | `finans_yonetim.html` | ~3062 | `renderKasa` entity param kaldır |
| 5 | `finans_server.py` | 201 | `/api/kasa` varsayılan entity kaldır |

**Toplam: 5 küçük değişiklik — 2 dosya.**  
DB'ye dokunulmaz. Mevcut veri kaybolmaz.

---

*Rapor: `D:\finans\reports\SIRKET_MANTIGI_DEGISIM_ANALIZ.md` — Kod değişikliği için onay bekleniyor.*
