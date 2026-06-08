# ÇEK BANKA + ÇEK NO — UYGULAMA RAPORU

> **Tarih:** 5 Haziran 2026  
> **Yedek:** `D:\finans_BACKUP_BEFORE_CEK_BANKA_CEKNO_20260605` (14 dosya)  
> **DB:** Değiştirildi (ADD COLUMN) | **CPS:** Dokunulmadı

---

## Yapılan Değişiklikler

### 1. `finans.db` — ALTER TABLE

```sql
ALTER TABLE odemeler ADD COLUMN banka  TEXT;
ALTER TABLE odemeler ADD COLUMN cek_no TEXT;
```

| Kontrol | Sonuç |
|---------|-------|
| Kolon var mıydı? | Hayır — eklendi |
| Mevcut 41 çek etkilendi mi? | Hayır — `banka=NULL, cek_no=NULL` |
| Diğer 674 ödeme etkilendi mi? | Hayır — NULL |
| SQLite version | 3.50.4 |

### 2. `finans_server.py` — POST + PUT Güncellendi

**`POST /api/odemeler`** — INSERT sorgusuna eklendi:
```python
(id,entity,aciklama,tip,tutar,para,vade,odeme_tarihi,durum,tekrar,not_,
 kaydeden,kayit_tarihi, banka, cek_no)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
```
- `d.get('banka','') or None` — boş string → NULL
- `d.get('cek_no','') or None` — boş string → NULL

**`PUT /api/odemeler/<id>`** — UPDATE sorgusuna eklendi:
```python
banka=?, cek_no=?
```

**`GET /api/odemeler`** — `SELECT *` kullandığından otomatik döndürüyor. Değişiklik yok.

### 3. `finans_yonetim.html` — 3 Bölüm Güncellendi

#### `cek-modal` HTML — 2 yeni alan eklendi
```html
<div class="form-row">
  <input id="cek-banka"  placeholder="ör: Garanti, Akbank...">
  <input id="cek-no"     placeholder="ör: 123456789">
</div>
```

#### `openCekModal()` — Yeni alanlar sıfırlanıyor
```javascript
document.getElementById('cek-banka').value = '';
document.getElementById('cek-no').value = '';
```

#### `saveCek()` — Payload'a eklendi
```javascript
banka:  banka || null,
cek_no: cekNo || null,
```

#### `renderCekler()` — Tablo başlıkları + satırları güncellendi

**Yeni sütunlar:**

| Sütun | NULL ise | Dolu ise |
|-------|---------|---------|
| Banka | `-` (gri) | Mavi badge |
| Çek No | `-` (gri) | Monospace metin |

---

## Test Sonuçları

| Test | Sonuç |
|------|-------|
| Önceki çek sayısı | 41 |
| POST: `banka='GARANTI TEST'`, `cek_no='TEST123'` | ✅ ok=True, id=9b835cae-5 |
| Çek sayısı → 42 | ✅ +1 |
| Kayıt: `banka='GARANTI TEST'` | ✅ |
| Kayıt: `cek_no='TEST123'` | ✅ |
| Kayıt: `aciklama='Çek: TEST CEK'` | ✅ |
| Kayıt: `durum='bekliyor'` | ✅ |
| Takvim çek filtresi (`substr(1,3)='ek:'`) | ✅ 42 kayıt (test dahil) |
| DELETE test kaydı | ✅ ok=True |
| Final çek sayısı → 41 | ✅ Başlangıçla aynı |
| DB kolonları `banka` + `cek_no` | ✅ VAR |

---

## Mevcut Çek Durumu (Sonrası)

| Alan | Değer |
|------|-------|
| Toplam çek | 41 |
| banka dolu | 0 (tümü NULL — eski kayıtlar) |
| cek_no dolu | 0 (tümü NULL — eski kayıtlar) |
| Yeni eklenen çeklerde | banka + cek_no opsiyonel |

---

## Değişen Dosyalar

| Dosya | Değişiklik |
|-------|-----------|
| `finans.db` | `banka TEXT` + `cek_no TEXT` ADD COLUMN |
| `finans_server.py` | POST INSERT + PUT UPDATE güncellendi |
| `finans_yonetim.html` | Modal 2 alan + openCekModal + saveCek + renderCekler |

---

## CPS Durumu

CPS'e dokunulmadı.

---

*Yedek: `D:\finans_BACKUP_BEFORE_CEK_BANKA_CEKNO_20260605`*
