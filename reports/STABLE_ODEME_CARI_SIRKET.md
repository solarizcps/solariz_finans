# STABLE — ÖDEME CARİ ETİKET + ŞİRKET SEÇİMİ

> **Tarih:** 5 Haziran 2026  
> **Yedek:** `D:\finans_BACKUP_STABLE_ODEME_CARI_SIRKET_20260605`  
> **Önceki Stable:** `D:\finans_BACKUP_STABLE_KASA_BANKA_20260605`

---

## Yedek

| | |
|---|---|
| Yedek yolu | `D:\finans_BACKUP_STABLE_ODEME_CARI_SIRKET_20260605` |
| Durum | ✅ Oluşturuldu |

---

## Yapılan Değişiklikler

### Tedarikçi Görünen Etiketleri → Cari / Cari Ödeme

DB'de `tip='tedarikci'` değeri **korundu** — sadece kullanıcıya gösterilen metin değişti.

| Yer | Önceki | Sonraki |
|-----|--------|---------|
| Dashboard yaklaşan ödeme filtresi | Tedarikçi | **Cari** |
| Ödemeler sekmesi tip filtresi | Tedarikçi | **Cari** |
| `tipLabel()` JS map | Tedarikçi | **Cari** |
| Takvim `TIP_ETK_CF` map | Tedarikçi | **Cari** |
| `odeme-modal` Tip dropdown | Tedarikçi | **Cari Ödeme** |
| `plan-odeme-modal` Kategori | Tedarikçi | **Cari Ödeme** |
| Hızlı ödeme (`q-tip`) | Tedarikçi | **Cari Ödeme** |

---

### `odeme-modal` Şirket Seçimi Eklendi

```html
<select class="form-control" id="odeme-entity">
  <option value="solariz">Şahin</option>
  <option value="nexgen">NexGen</option>
  <option value="pera">Pera</option>
  <option value="sahsi">Şahsi / Diğer</option>
</select>
```

### Entity Mapping

| Görünen | DB `entity` değeri |
|---------|-------------------|
| Şahin | `solariz` |
| NexGen | `nexgen` |
| Pera | `pera` |
| Şahsi / Diğer | `sahsi` |

---

### `saveOdeme()` Formdaki Entity Kullanıyor

```javascript
var odemeEntity = document.getElementById('odeme-entity').value || currentEntity || 'solariz';
entity: odemeEntity
```

- Eski davranış: global `currentEntity` (sabit `solariz`)
- Yeni davranış: formdan seçilen şirket

### `editOdeme()` Entity Alanını Dolduruyor

Mevcut kaydı düzenlerken şirket seçimi otomatik gelir:
```javascript
document.getElementById('odeme-entity').value = o.entity || 'solariz';
```

### `clearOdemeForm()` Entity Resetleniyor

Modal kapatılınca `solariz`'e sıfırlanır.

---

## Test Sonuçları

| Adım | Sonuç |
|------|-------|
| Başlangıç kayıt sayısı | 715 |
| POST: entity=`sahsi`, tip=`tedarikci`, tutar=1000 | ✅ 200 OK |
| GET: `entity = "sahsi"` döndü | ✅ |
| GET: `tip = "tedarikci"` korundu | ✅ |
| DELETE: test kaydı silindi | ✅ 200 OK |
| Silme sonrası kayıt sayısı | 715 (değişmedi) ✅ |

---

## DB / Backend / CPS

| Alan | Durum |
|------|-------|
| DB yapısı değişmedi | ✅ |
| `tip='tedarikci'` DB değeri korundu | ✅ |
| Mevcut 715 kayıt etkilenmedi | ✅ |
| `finans_server.py` değişmedi | ✅ |
| CPS dokunulmadı | ✅ |

---

## Korunacak Kurallar

- `tip='tedarikci'` DB değeri değişmez
- Çek kayıtları (`tip='tedarikci'`, `aciklama='Çek: ...'`) etkilenmez
- Eski `solariz/nexgen/sahsi/pera` entity değerleri korunur
- `odeme-modal` varsayılan entity: `solariz` (Şahin)
