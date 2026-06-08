# KASA BANKA ALANI ANALİZİ

> **Tarih:** 5 Haziran 2026  
> **Mevcut Stable:** `D:\finans_BACKUP_STABLE_KREDI_TAKSIT_DUZENLEME_20260605`  
> **DB:** Dokunulmadı (analiz) | **CPS:** Dokunulmadı

---

## 1. DB — `kasa` Tablosu

### Mevcut Kolon Yapısı

| # | Kolon | Tip | Doluluk |
|---|-------|-----|---------|
| 0 | `id` | TEXT | — |
| 1 | `entity` | TEXT | zorunlu |
| 2 | `aciklama` | TEXT | Hareketi açıklar |
| 3 | `tutar` | REAL | Tutar |
| 4 | `para` | TEXT | default 'TL' |
| 5 | `tarih` | TEXT | Hareket tarihi |
| 6 | `tip` | TEXT | `giris` / `cikis` |
| **7** | **`not_`** | **TEXT** | **Var — genellikle boş** |
| 8 | `kaydeden` | TEXT | — |
| 9 | `kayit_tarihi` | TEXT | — |

**`banka` kolonu → YOK.**

### Gelen/Çıkan Ayrımı

`tip` kolonu ile yapılıyor:
- `tip = 'giris'` → kasaya gelen para
- `tip = 'cikis'` → kasadan çıkan para

### Mevcut Kayıt Sayısı

**1 kayıt** — yeni sistem, henüz az kullanılmış.

```
id=f6b33e7c-7  aciklama='Lcw gelen odem'  tutar=5,000,000  tip='giris'
tarih=2026-06-05  not_=''
```

---

## 2. Backend — `finans_server.py`

| Endpoint | Method | Durum | Banka |
|----------|--------|-------|-------|
| `GET /api/kasa` | GET | ✅ Var | ❌ Yok |
| `POST /api/kasa` | POST | ✅ Var | ❌ Yok |
| `PUT /api/kasa/<id>` | PUT | **❌ Yok** | — |
| `DELETE /api/kasa/<id>` | DELETE | ✅ Var | — |

### POST `/api/kasa` Mevcut İşlenen Alanlar

```python
conn.execute('''INSERT INTO kasa
    (id, entity, aciklama, tutar, para, tarih, tip, not_, kaydeden, kayit_tarihi)
    VALUES (?,?,?,?,?,?,?,?,?,?)''',
    (kid, d.get('entity','solariz'), d.get('aciklama'),
     d.get('tutar',0), d.get('para','TL'), d.get('tarih', ...),
     d.get('tip','giris'), d.get('not',''),        # ← 'not' anahtarı
     d.get('kaydeden'), datetime.now().isoformat()))
```

`banka` alanı INSERT'te **yok** — eklenmesi gerekecek.  
`not` anahtarı kullanılıyor (`not_` değil) — çek/kredi modüllerindeki pattern ile aynı.

---

## 3. Frontend — `finans_yonetim.html`

### Kasa Formu (satır 982–1009)

**Mevcut alanlar:**

| Alan | Durum |
|------|-------|
| Açıklama | ✅ Var |
| Tutar | ✅ Var |
| Para Birimi | ✅ Var |
| Tarih | ✅ Var |
| **Banka** | **❌ Yok** |

Form inline (modal değil) — `+ Giriş` / `- Çıkış` butonlarıyla açılıyor.  
Grid: `2fr 1fr 1fr 1fr auto` — bir sütun daha eklenebilir.

### Kasa Listesi (`renderKasa()` — satır 3450)

**Mevcut tablo başlıkları:**

```
Açıklama | Tarih | Para | Tutar | Tip | (sil)
```

**Banka sütunu → YOK.**  
`h.banka` listede hiç kullanılmıyor.

### `kasaHareketEkle()` Fonksiyonu

```javascript
apiPost('/api/kasa', {
  entity: currentEntity, aciklama: aciklama, tutar: tutar,
  para: para, tarih: tarih, tip: tip,
  kaydeden: currentUser ? currentUser.ad : ''
  // ← banka gönderilmiyor
});
```

---

## 4. Önerilen Çözüm

### Seçenek A — `not_` Alanını Banka İçin Kullan (DB değişikliği yok)

`not_` alanı var ve genellikle boş. Banka bilgisini buraya yazabiliriz.

**Avantaj:** DB değişikliği yok, sıfır migration riski.  
**Dezavantaj:** `not_` semantik olarak yanlış kullanılıyor. İleride `not_` hem açıklama hem banka tutacak, karışır.

### Seçenek B — `ALTER TABLE kasa ADD COLUMN banka TEXT` (Önerilen)

Temiz çözüm. Yalnızca 1 kayıt mevcut, o da `NULL` kalır.

```sql
ALTER TABLE kasa ADD COLUMN banka TEXT;
```

**Avantaj:** Ayrı kolon, açık semantik, ileride filtre/gruplama kolaylaşır.  
**Dezavantaj:** Küçük DB değişikliği gerekir (ama 1 kayıt, sıfır risk).

**Öneri: Seçenek B** — tek satır ALTER TABLE, mevcut tek kayıt bozulmaz.

### Sonrasında Gerekli Değişiklikler (her iki seçenekte)

| Dosya | Değişiklik | Satır |
|-------|-----------|-------|
| `finans_server.py` | POST'a `banka` ekle | ~229 |
| `finans_yonetim.html` | Forma `banka` input ekle | ~984 |
| `finans_yonetim.html` | `kasaHareketEkle()` banka gönder | ~3439 |
| `finans_yonetim.html` | `renderKasa()` listede banka göster | ~3477 |

**Toplam:** 2 dosya, ~4 küçük değişiklik.

---

## 5. Risk Analizi

| Alan | Etki | Risk |
|------|------|------|
| Takvim (`renderCalendar`) | `kasa` tablosuna bakıyor mu? | ✅ Yok — takvim `odemeler`/`planlama` kullanıyor |
| Nakit akış KPI | Bakiye `res.bakiye` — `SUM tip` ile — `banka` eklense de değişmez | ✅ Yok |
| Özet kartlar | Kasa bakiyesi `kasa-tl-toplam` — `banka` etkilemez | ✅ Yok |
| Mevcut 1 kasa kaydı | `banka = NULL` kalır — listede `—` gösterilir | ✅ Yok |
| PUT endpoint yok | Kasa hareketi güncelleme şimdi yok | ⚠️ Bilgi (bu fazda kapsam dışı) |

**Genel risk: ÇOK DÜŞÜK.** `kasa` tablosu henüz 1 kayıtlı, yeni sistem.

---

## 6. Özet Karar Tablosu

| Soru | Cevap |
|------|-------|
| `kasa.banka` kolonu var mı? | ❌ Yok |
| `not_` fallback kullanılabilir mi? | ✅ Teknik olarak evet — ama önerilmez |
| DB ALTER TABLE gerekir mi? | ✅ Seçenek B: 1 satır, sıfır risk |
| Backend değişikliği? | ✅ POST `banka` alanı eklenecek (~3 satır) |
| Frontend değişikliği? | ✅ Form + liste (~4 değişiklik) |
| Takvim/KPI bozulur mu? | ❌ Hayır |
| Mevcut 1 kayıt etkilenir mi? | ❌ NULL kalır, sorun yok |

---

*Analiz: `D:\finans\reports\KASA_BANKA_ALANI_ANALIZ.md` — Kod/DB değişikliği için onay bekliyor.*
