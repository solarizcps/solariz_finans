# ÖDEME CARİ ETİKET + ŞİRKET SEÇİMİ UYGULAMA RAPORU

> **Tarih:** 5 Haziran 2026  
> **Stable Referans:** `D:\finans_BACKUP_STABLE_KASA_BANKA_20260605`  
> **DB:** Dokunulmadı | **Backend:** Dokunulmadı | **CPS:** Dokunulmadı

---

## Değişen Dosya

| Dosya | Değişiklik sayısı |
|-------|------------------|
| `D:\finans\finans_yonetim.html` | 11 değişiklik |

---

## 1. Etiket Değişiklikleri (`Tedarikçi` → `Cari`)

DB'de `tip='tedarikci'` değeri **aynen korundu**. Sadece görünen metin değişti.

| Satır | Yer | Önceki | Sonraki |
|-------|-----|--------|---------|
| ~794 | Dashboard yaklaşan ödeme filtresi | `Tedarikçi` | `Cari` |
| ~865 | Ödemeler sekmesi tip filtresi | `Tedarikçi` | `Cari` |
| ~1276 | `plan-odeme-modal` Kategori | `Tedarikçi` | `Cari Ödeme` |
| ~1353 | `odeme-modal` Tip | `Tedarikçi` | `Cari Ödeme` |
| ~1626 | Hızlı ödeme modalı (`q-tip`) | `Tedarikçi` | `Cari Ödeme` |
| ~1870 | `tipLabel()` JS map | `'Tedarikçi'` | `'Cari'` |
| ~3518 | `TIP_ETK_CF` takvim map | `'Tedarikçi'` | `'Cari'` |

**Kural uygulandı:**
- Kısa/filtre alanları → `Cari`
- Form başlığı/tip alanı → `Cari Ödeme`

---

## 2. `odeme-modal` Şirket Seçimi (YENİ)

"Not" alanının yanına eklendi (`form-row` içinde yan yana):

```html
<select class="form-control" id="odeme-entity">
  <option value="solariz">Şahin</option>
  <option value="nexgen">NexGen</option>
  <option value="pera">Pera</option>
  <option value="sahsi">Şahsi / Diğer</option>
</select>
```

### Entity Mapping

| Görünen | DB entity değeri |
|---------|-----------------|
| Şahin | `solariz` |
| NexGen | `nexgen` |
| Pera | `pera` |
| Şahsi / Diğer | `sahsi` |

---

## 3. `saveOdeme()` Değişikliği

```javascript
// Önce (global değişken):
entity: currentEntity

// Sonra (formdan alıyor, fallback korunuyor):
var odemeEntity = (document.getElementById('odeme-entity')
  ? document.getElementById('odeme-entity').value
  : null) || currentEntity || 'solariz';
entity: odemeEntity
```

---

## 4. `editOdeme()` Değişikliği

Mevcut kaydın entity değeri düzenleme modalında seçili gelir:

```javascript
if (document.getElementById('odeme-entity'))
  document.getElementById('odeme-entity').value = o.entity || 'solariz';
```

---

## 5. `clearOdemeForm()` Değişikliği

Modal kapatılınca entity `solariz`'e sıfırlanır:

```javascript
if (document.getElementById('odeme-entity'))
  document.getElementById('odeme-entity').value = 'solariz';
```

---

## Test Sonuçları

| Adım | Sonuç |
|------|-------|
| Başlangıç kayıt sayısı | 715 |
| POST: entity=`sahsi`, aciklama=`TEST CARI`, tip=`tedarikci` | ✅ 200 OK — id: `3f9bbb1e-1` |
| GET: `entity = "sahsi"` döndü | ✅ |
| GET: `tip = "tedarikci"` (değişmedi) | ✅ |
| DELETE | ✅ 200 OK |
| Silme sonrası kayıt sayısı | 715 (eski haline döndü) ✅ |

---

## DB / Backend / CPS

| Alan | Durum |
|------|-------|
| DB değişikliği | ❌ Yok |
| `finans_server.py` değişikliği | ❌ Yok |
| CPS dokunuldu | ❌ Hayır |
| Mevcut 715 kayıt etkilendi | ❌ Hayır |
| Eski `solariz/nexgen/sahsi` entity değerleri | ✅ Korunuyor |
