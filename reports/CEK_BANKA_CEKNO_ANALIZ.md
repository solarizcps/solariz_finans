# ÇEK BANKA + ÇEK NO ANALİZİ

> **Tarih:** 5 Haziran 2026  
> **Kapsam:** `D:\finans` bağımsız sistem  
> **DB:** Dokunulmadı (analiz) | **CPS:** Dokunulmadı

---

## 1. `odemeler` Tablosu Mevcut Kolon Listesi

| # | Kolon | Tip | `banka`/`cek_no` var mı? |
|---|-------|-----|--------------------------|
| 0 | `id` | TEXT | — |
| 1 | `entity` | TEXT | — |
| 2 | `aciklama` | TEXT | — |
| 3 | `tip` | TEXT | — |
| 4 | `tutar` | REAL | — |
| 5 | `para` | TEXT | — |
| 6 | `vade` | TEXT | — |
| 7 | `odeme_tarihi` | TEXT | — |
| 8 | `durum` | TEXT | — |
| 9 | `tekrar` | TEXT | — |
| 10 | `not_` | TEXT | — |
| 11 | `kaydeden` | TEXT | — |
| 12 | `kayit_tarihi` | TEXT | — |
| 13 | `guncelleyen` | TEXT | — |
| 14 | `guncelleme` | TEXT | — |

**`banka` kolonu: YOK. `cek_no` kolonu: YOK.**  
Karşılaştırma: `krediler` tablosunda `banka TEXT` kolonu **VAR** ve aktif kullanılıyor.

---

## 2. Mevcut `not_` Kolon Durumu

```
Çek kayıtlarında not_ = 'Çek'  →  41 / 41 kayıt (sabit metin)
not_ max uzunluk (tüm tablo)   →  40 karakter
Çek aciklama içinde '|' olan   →  0 kayıt
Çek aciklama içinde banka adı  →  0 kayıt (hiç banka bilgisi girilmemiş)
```

`not_` şu an sadece `'Çek'` değeri taşıyor — marker olarak kullanılıyor, içerik taşımıyor.

---

## 3. Seçenek Karşılaştırması

### Seçenek A — `aciklama` alanına boru (`|`) ile gömmek

**Format:**
```
aciklama = "Çek: Firma Adı | Garanti | 12345678"
```

**Avantajları:**
- DB değişikliği yok
- Backend değişikliği yok

**Dezavantajları:**
- `renderCekler()` firmasını çekmek için `split('|')[0]` parse gerekir
- Mevcut 41 kayıt: `"Çek: Nexgen Kimya"` — düz format
- Yeni format: `"Çek: Nexgen Kimya | Garanti | 12345"` — karışık
- Rapor/filtre yazmak zorlaşır
- Gelecekte boru işareti içeren firma adı çakışabilir
- `aciklama` max şu an 57 karakter — uzayacak

**Karar: ⚠️ Çalışır ama kirli çözüm.**

---

### Seçenek B — `not_` alanını banka+no için kullanmak

**Format:**
```
not_ = "Garanti | 12345678"
```

**Avantajları:**
- DB değişikliği yok
- Backend değişikliği yok (not_ zaten POST/PUT'ta var)

**Dezavantajları:**
- Mevcut 41 kayıtta `not_ = 'Çek'` → format farklı, parse karmaşık
- `not_='Çek'` → marker, `not_='Garanti | 12345'` → veri: iki farklı anlam
- Yeni girişlerde çek tespiti `not_` üzerinden yapılamaz (artık `'Çek'` olmayacak)
- Sayısal sıralama, filtreleme, raporlama zor

**Karar: ❌ Önerilmez. Semantik karışıklık yaratır.**

---

### Seçenek C — DB'ye `banka TEXT` + `cek_no TEXT` kolonu eklemek ✅ ÖNERİLEN

```sql
ALTER TABLE odemeler ADD COLUMN banka  TEXT;
ALTER TABLE odemeler ADD COLUMN cek_no TEXT;
```

**Avantajları:**
- Mevcut 41 çek kaydı: `banka=NULL`, `cek_no=NULL` — **bozulmaz**
- Diğer 674 ödeme kaydı: aynı şekilde NULL — **etkilenmez**
- Çek listeleme: `<banka> — <cek_no>` ayrı sütun olarak gösterilebilir
- `krediler` tablosunda `banka` kolonu zaten var → tutarlı mimari
- Sıralama/filtreleme (banka bazlı) kolaylaşır
- İleride rapor çıkarmak temiz

**Dezavantajları:**
- DB değişikliği gerekiyor → **yedek zorunlu**
- Backend `POST /api/odemeler` ve `PUT /api/odemeler/<id>` güncellenmeli
- Frontend `cek-modal` ve `renderCekler()` güncellenmeli
- SQLite 3.x'te `ADD COLUMN` geri alınamaz (ama `DROP COLUMN` SQLite 3.35+ destekli; mevcut versiyon: **3.50.4** → DROP destekli)

**Etkilenen Değişiklik Zinciri:**

| Katman | Değişiklik |
|--------|-----------|
| `finans.db` | `ALTER TABLE odemeler ADD COLUMN banka TEXT` |
| `finans.db` | `ALTER TABLE odemeler ADD COLUMN cek_no TEXT` |
| `finans_server.py` — POST | `banka` ve `cek_no` parametresi eklenir |
| `finans_server.py` — PUT | `banka` ve `cek_no` güncelleme eklenir |
| `finans_yonetim.html` — `cek-modal` | 2 yeni input alanı |
| `finans_yonetim.html` — `saveCek()` | payload'a `banka`, `cek_no` eklenir |
| `finans_yonetim.html` — `renderCekler()` | tablo satırında banka/no gösterimi |

**Karar: ✅ En temiz çözüm.**

---

## 4. Mevcut 41 Çek Etkilenir mi?

### Seçenek A (aciklama): ⚠️
- Mevcut kayıtlar değişmez ama format tutarsız olur.
- `renderCekler()` parse mantığı çatallanır.

### Seçenek B (not_): ❌
- Mevcut `not_='Çek'` marker değeri bozulur.
- Yeni kayıtlarda çek tespiti için ek mantık gerekir.

### Seçenek C (ADD COLUMN): ✅
- `ALTER TABLE ADD COLUMN` → NULL default
- Mevcut 41 çek: `banka=NULL, cek_no=NULL` — veri KAYBI YOK
- Mevcut filtre `aciklama.indexOf('Çek:')===0` — ETKİLENMEZ
- Mevcut `renderCekler()` — ETKİLENMEZ (yeni kolonlar opsiyonel gösterilir)

---

## 5. Minimum Güvenli Çözüm

**Önerilen sıra:**

1. Yedek al: `D:\finans_BACKUP_BEFORE_CEK_BANKA_YYYYMMDD`
2. `finans.db` → `ALTER TABLE odemeler ADD COLUMN banka TEXT`
3. `finans.db` → `ALTER TABLE odemeler ADD COLUMN cek_no TEXT`
4. `finans_server.py` → `POST /api/odemeler` + `PUT /api/odemeler/<id>` güncelle
5. `finans_yonetim.html` → `cek-modal` 2 alan ekle + `saveCek()` güncelle
6. `finans_yonetim.html` → `renderCekler()` tablo satırında banka/no göster (NULL ise `-`)
7. Test: yeni çek ekle, banka+no göster, eski 41 çek bozulmadı mı kontrol et

**Toplam etkilenen dosya:** 3 (`finans.db` + `finans_server.py` + `finans_yonetim.html`)

---

## 6. SQLite `ALTER TABLE` Güvenliği

```
SQLite version: 3.50.4
ALTER TABLE ADD COLUMN: ✅ Destekleniyor (v2.x'ten beri)
DROP COLUMN:            ✅ Destekleniyor (v3.35.0+, mevcut v3.50.4)
Mevcut veri etkisi:     NULL default → sıfır veri kaybı
```

Geri alma senaryosu (ihtiyaç olursa):
```sql
-- SQLite 3.35+ ile DROP COLUMN mümkün
ALTER TABLE odemeler DROP COLUMN banka;
ALTER TABLE odemeler DROP COLUMN cek_no;
```

---

## 7. Özet Karar Tablosu

| Seçenek | DB Değişikliği | Mevcut Veri | Temizlik | Öneri |
|---------|---------------|------------|---------|-------|
| A — aciklama içine göm | ❌ Yok | ⚠️ Format karışır | ⚠️ Kirli | ❌ |
| B — not_ kullan | ❌ Yok | ⚠️ Marker bozulur | ❌ Kötü | ❌ |
| C — ADD COLUMN | ✅ Gerekli | ✅ Etkilenmez | ✅ Temiz | **✅ Önerilen** |

---

*Analiz: `D:\finans\reports\CEK_BANKA_CEKNO_ANALIZ.md` — Kod ve DB değişikliği için onay bekliyor.*
