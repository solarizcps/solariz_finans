# ÖDEME — CARİ ETİKET + ŞİRKET SEÇİMİ ANALİZİ

> **Tarih:** 5 Haziran 2026  
> **Mevcut Stable:** `D:\finans_BACKUP_STABLE_KASA_BANKA_20260605`  
> **DB:** Dokunulmadı (analiz) | **CPS:** Dokunulmadı

---

## 1. DB — `odemeler` Tablosu

### İlgili Kolonlar

| Kolon | Tip | Mevcut Değerler |
|-------|-----|-----------------|
| `entity` | TEXT, **notnull=1** | `solariz` (594), `sahsi` (118), `nexgen` (3) |
| `tip` | TEXT | `tedarikci` (211), `taksit` (197), `diger` (150), `kredi` (119), `vergi` (20), `maas` (18) |

### Entity Değer Dağılımı (715 kayıt)

| Entity | Kayıt | Karşılık |
|--------|-------|---------|
| `solariz` | 594 | Şahin (mevcut ana şirket) |
| `sahsi` | 118 | Şahsi / kişisel — Altan'ın "Pera" mı, yoksa ayrı kategori mi? |
| `nexgen` | 3 | NexGen |
| `pera` | **0** | Kayıt yok — henüz kullanılmamış |

**Önemli:** `pera` entity henüz hiç kullanılmamış. `sahsi` 118 kayıtla ayrı bir kategori — Altan ile netleştirilmesi gerekiyor:  
> `sahsi` → Pera mı olacak? Ayrı mı kalacak? Yeni `sirket` seçiminde listelenmeli mi?

### `tip='tedarikci'` Tanımı

DB'de `tip` kolonu `tedarikci` değeri tutuyor. Bu **kod/iş mantığı** değeri — label değil.  
Çek kayıtları da `tip='tedarikci'` kullanıyor: `aciklama = 'Çek: ...'`

```
tip='tedarikci' → 211 kayıt
  - Çek kayıtları (aciklama='Çek: ...'): ~41 kayıt
  - Normal tedarikçi/cari ödemeler: ~170 kayıt
```

---

## 2. Backend — `finans_server.py`

### POST `/api/odemeler` — Mevcut Durum

```python
conn.execute('''INSERT OR REPLACE INTO odemeler
    (id, entity, aciklama, tip, tutar, para, vade, odeme_tarihi,
     durum, tekrar, not_, kaydeden, kayit_tarihi, banka, cek_no)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
    (oid, d.get('entity'), d.get('aciklama'), d.get('tip'), ...))
```

- `entity` kabul ediyor ✅
- `tip` kabul ediyor ✅ (herhangi bir string kabul eder — validation yok)
- **Backend değişikliği gerekmez.** Şirket seçimi frontend'den `entity` olarak gönderilebilir.

---

## 3. Frontend — `finans_yonetim.html`

### `odeme-modal` Mevcut Alanlar

```
Açıklama | Tip
Tutar    | Para Birimi
Vade Tarihi | Ödeme Tarihi
Durum   | Tekrar
Not
```

**Entity/Şirket alanı → YOK.**

### `saveOdeme()` — Entity Nereden Geliyor?

```javascript
var payload = {
  entity: currentEntity,   // ← global değişken — formdan gelmiyor
  ...
};
```

`currentEntity` değişkeni global scope'ta tanımlı. Şirket seçimi kaldırıldığından bu değer artık `'solariz'` veya başka sabit bir değere kilitli.

**Sorun:** Formda şirket seçimi olmadığı için tüm yeni ödemeler `currentEntity` değerine (büyük ihtimalle `solariz`) kaydediliyor.

### `Tedarikçi` Etiketi Kaç Yerde Var?

| Satır | Konum | Kullanım |
|-------|-------|---------|
| 794 | Ana dashboard `upcoming-tip-filter` dropdown | filtre seçeneği |
| 865 | Ödemeler sekmesi filtre dropdown | filtre seçeneği |
| 1276 | `plan-odeme-modal` Tip dropdown | planlı ödeme formu |
| 1353 | `odeme-modal` Tip dropdown | ana ödeme formu |
| 1626 | Başka bir filtre alanı | — |
| 1870 | `var map = { tedarikci: 'Tedarikçi', ... }` | JS tip-label eşleşme haritası |
| 3518 | `TIP_ETK_CF` takvim filtre map | takvim renk/etiket |

**Toplam 7 yer** — hepsi `'tedarikci'` DB değerini `'Tedarikçi'` olarak gösteriyor.  
DB değeri değişmeyecek, **sadece label** değişecek.

### `currentEntity` Değeri Ne?

```javascript
// Şirket seçimi kaldırıldıktan sonra, giriş yapan kullanıcıya bağlı olabilir
// veya sabit 'solariz' kalmış olabilir
```

İnceleme: `currentEntity` şu an büyük ihtimalle login sonrası atanıyor ve `solariz`.

---

## 4. Mevcut 715 Kayıt Etkilenir mi?

| Değişiklik | Kayıt Etkisi |
|-----------|-------------|
| `Tedarikçi` → `Cari` label değişimi | ❌ Yok — DB değeri `tedarikci` kalıyor |
| Şirket seçimi eklenmesi | ❌ Yok — eski kayıtlar entity bilgisini koruyor |
| `entity` değer dönüşümü | ❌ GEREKMİYOR — mevcut `solariz/nexgen/sahsi` kalıyor |
| Yeni `pera` entity | ❌ Yok — sadece yeni kayıtlar için |

**715 kayıt tamamen korunur.**

---

## 5. Minimum Değişiklik Planı

### Değişiklik 1 — `Tedarikçi` → `Cari` Etiket (7 yer)

DB değişikliği yok. Sadece HTML/JS label güncelleme:

```javascript
// Önce:
{ tedarikci: 'Tedarikçi', ... }

// Sonra:
{ tedarikci: 'Cari', ... }
```

Dropdown `value` değerleri **değişmez** (`tedarikci` kalır), sadece görünen metin değişir.

### Değişiklik 2 — `odeme-modal`'a Şirket Seçimi

`odeme-modal`'a yeni bir `select` alanı eklenir:

```html
<div class="form-group">
  <label class="form-label">Şirket</label>
  <select class="form-control" id="odeme-entity">
    <option value="solariz">Şahin</option>
    <option value="nexgen">NexGen</option>
    <option value="pera">Pera</option>
  </select>
</div>
```

`saveOdeme()` içinde `currentEntity` yerine `odeme-entity` değeri kullanılır:

```javascript
// Önce:
entity: currentEntity

// Sonra:
entity: document.getElementById('odeme-entity').value
```

### Değişiklik 3 — `editOdeme()` Şirket Alanını Doldurur

```javascript
document.getElementById('odeme-entity').value = o.entity || 'solariz';
```

### Değişiklik 4 — `clearOdemeForm()` Reset

```javascript
document.getElementById('odeme-entity').value = 'solariz';
```

---

## 6. Açık Soru — `sahsi` Entity

Mevcut 118 kayıt `entity='sahsi'`. Bu:
- **Şahsi** (kişisel, Altan'a ait) mi kalacak?
- **Pera** mı olacak?
- Yeni şirket listesine dahil mi edilmeli?

**Öneri:** `sahsi` ayrı tutulsun. Şirket dropdown'una 4. seçenek olarak eklenebilir:

```html
<option value="sahsi">Şahsi</option>
```

Ya da istenmiyorsa kaldırılır — eski kayıtlar `sahsi` olarak kalır.

---

## 7. Risk Analizi

| Alan | Etki | Risk |
|------|------|------|
| Mevcut 715 ödeme | DB değeri değişmez | ✅ Sıfır |
| Çek kayıtları (`tip='tedarikci'`) | `tedarikci` DB değeri korunuyor | ✅ Sıfır |
| Takvim renk/etiket (`TIP_ETK_CF`) | `tedarikci` key korunuyor, sadece value değişir | ✅ Sıfır |
| `editOdeme()` | Entity field eklenmesi gerekiyor | ⚠️ Unutulursa mevcut kayıt entity'si sıfırlanabilir |
| `currentEntity` | Artık kullanılmıyor — eski kayıtlar etkilenmez | ✅ |

---

## 8. Özet Karar Tablosu

| Soru | Cevap |
|------|-------|
| DB `tedarikci` değeri değişecek mi? | ❌ Hayır |
| Kaç label değişecek? | 7 yer (dropdown option text + JS map) |
| Entity seçimi formda var mı? | ❌ Yok — eklenmesi gerekiyor |
| Backend değişikliği? | ❌ Gerekmez |
| DB değişikliği? | ❌ Gerekmez |
| 715 kayıt etkilenir mi? | ❌ Hayır |
| `sahsi` entity ne olacak? | ❓ Altan kararı |

---

*Analiz: `D:\finans\reports\ODEME_CARI_SIRKET_ANALIZ.md` — Kod değişikliği için onay bekliyor.*
