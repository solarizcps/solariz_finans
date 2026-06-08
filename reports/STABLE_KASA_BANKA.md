# STABLE — KASA BANKA ALANI

> **Tarih:** 5 Haziran 2026  
> **Yedek:** `D:\finans_BACKUP_STABLE_KASA_BANKA_20260605`  
> **Önceki Stable:** `D:\finans_BACKUP_STABLE_KREDI_TAKSIT_DUZENLEME_20260605`

---

## Yedek

| | |
|---|---|
| Yedek yolu | `D:\finans_BACKUP_STABLE_KASA_BANKA_20260605` |
| Durum | ✅ Oluşturuldu |

---

## Yapılan Değişiklikler

### Kasa Tablosuna `banka TEXT` Eklendi

```sql
ALTER TABLE kasa ADD COLUMN banka TEXT;
```

- Kolon başarıyla eklendi
- Mevcut 1 kayıt `banka = NULL` olarak korundu — **bozulmadı**
- Güncel kolon sırası: `id, entity, aciklama, tutar, para, tarih, tip, not_, kaydeden, kayit_tarihi, banka`

### Mevcut 1 Kayıt Korundu

Mevcut kayıt (`Lcw gelen odem`, 5.000.000 TL, 2026-06-05) değiştirilmedi.  
`banka = NULL` → listede `—` olarak gösteriliyor.

### Kasa Formuna Banka Alanı Eklendi

`+ Giriş` / `- Çıkış` formunda yeni input:  
```
Açıklama | Tutar | Para Birimi | Banka | Tarih | [Kaydet]
```

### Kasa Listesinde Banka Sütunu Görünüyor

```
Açıklama | Tarih | Banka | Para | Tutar | Tip | (sil)
```

Banka dolu → mavi badge `[Garanti]`  
Banka boş → gri `—`

### API Banka Dönüyor

`GET /api/kasa` — `SELECT *` ile `banka` alanı otomatik dönüyor.  
`POST /api/kasa` — `banka` parametresi kabul ediliyor ve DB'ye yazılıyor.

### Test Kayıt Eklendi / Silindi

| Adım | Sonuç |
|------|-------|
| POST: aciklama=`TEST KASA BANKA`, banka=`GARANTI TEST`, tutar=1000 | ✅ 200 OK |
| GET: `banka = "GARANTI TEST"` döndü | ✅ |
| DELETE: test kaydı silindi | ✅ 200 OK |
| Kayıt sayısı geri döndü: 1 | ✅ |

---

## DB / Backend / CPS

| Alan | Durum |
|------|-------|
| `finans.db` — `kasa.banka` kolonu | ✅ Eklendi |
| Mevcut kayıt sayısı | 1 (değişmedi) |
| `finans_server.py` — POST güncellendi | ✅ |
| CPS dokunuldu | ❌ Hayır |

---

## Korunacak Kurallar

- `kasa.banka` opsiyonel — boş bırakılabilir, listede `—` gösterilir
- Mevcut kayıtlar `NULL` kalabilir
- `GET /api/kasa` her zaman `banka` alanını döner
