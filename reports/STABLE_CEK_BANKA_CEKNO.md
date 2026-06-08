# STABLE — ÇEK BANKA + ÇEK NO

> **Tarih:** 5 Haziran 2026  
> **Stable yedek:** `D:\finans_BACKUP_STABLE_CEK_BANKA_CEKNO_20260605` (14 dosya / 1043 KB)  
> **CPS:** Dokunulmadı

---

## Son Kontrol

| Kontrol | Sonuç |
|---------|-------|
| Sunucu çalışıyor | ✅ 5058 |
| `banka` alanı API'de | ✅ VAR |
| `cek_no` alanı API'de | ✅ VAR |
| Mevcut çek sayısı | ✅ 41 |

---

## Yapılan Değişiklikler

### `finans.db`
```sql
ALTER TABLE odemeler ADD COLUMN banka  TEXT;  -- mevcut 41 çek: NULL (etkilenmedi)
ALTER TABLE odemeler ADD COLUMN cek_no TEXT;  -- mevcut 41 çek: NULL (etkilenmedi)
```

### `finans_server.py`
- `POST /api/odemeler` → INSERT sorgusuna `banka`, `cek_no` eklendi
- `PUT /api/odemeler/<id>` → UPDATE sorgusuna `banka`, `cek_no` eklendi
- `GET /api/odemeler` → `SELECT *` olduğundan otomatik döndürüyor

### `finans_yonetim.html`
- `cek-modal` → Banka + Çek No input alanları eklendi
- `openCekModal()` → Yeni alanlar sıfırlanıyor
- `saveCek()` → payload'a `banka`, `cek_no` eklendi
- `renderCekler()` → tablo başlığına **Banka** + **Çek No** sütunları eklendi
- Listede: dolu → mavi badge / monospace; boş → `-`

---

## Mevcut 41 Çek — Korundu

- `banka = NULL` → listede `-` gösterilir
- `cek_no = NULL` → listede `-` gösterilir
- Veri kaybı: **sıfır**
- Çek filtresi (`aciklama.indexOf('Çek:')===0`): **bozulmadı**

---

## Test Sonuçları

| Test | Sonuç |
|------|-------|
| POST `banka='GARANTI TEST'`, `cek_no='TEST123'` | ✅ ok=True |
| Çek sayısı 41 → 42 | ✅ |
| `banka` + `cek_no` doğru kaydedildi | ✅ |
| Takvim çek filtresi bozulmadı | ✅ 42 kayıt (test dahil) |
| DELETE test kaydı | ✅ ok=True |
| Çek sayısı 41'e döndü | ✅ |

---

## Takvim Durumu

- Çek rengi mor (`#7c3aed`) → **bozulmadı**
- `calTipRenk()` çek tespiti → **bozulmadı**
- Takvim sidebar çek listesi → **bozulmadı**

---

## Yedek Geçmişi

| Yedek | Durum |
|-------|-------|
| `Faz1 stable` (20260605) | ✅ Korunuyor |
| `Faz2 Google Style stable` (20260605) | ✅ Korunuyor |
| `Before Çek Banka/No` (20260605) | ✅ Korunuyor |
| **`Çek Banka/No stable` (20260605)** | ✅ **Bu nokta** |

---

## Korunacak Kurallar

- Çek konvansiyonu: `tip='tedarikci'` + `aciklama='Çek: ...'` — değiştirilmeyecek
- `banka` + `cek_no` opsiyonel — NULL geçerli
- `renderCekler()` filtresi — değiştirilmeyecek
- DB şema: `odemeler` tablosunda `banka TEXT`, `cek_no TEXT` mevcut

---

*Stable: `D:\finans_BACKUP_STABLE_CEK_BANKA_CEKNO_20260605` — CPS dokunulmadı*
