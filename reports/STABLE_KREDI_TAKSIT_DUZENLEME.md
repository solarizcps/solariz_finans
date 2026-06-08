# STABLE — KREDİ TAKSİT DÜZENLEME (K1 + K2)

> **Tarih:** 5 Haziran 2026  
> **Yedek:** `D:\finans_BACKUP_STABLE_KREDI_TAKSIT_DUZENLEME_20260605`  
> **Önceki Stable:** `D:\finans_BACKUP_STABLE_CEK_BANKA_CEKNO_20260605`

---

## Yedek

| | |
|---|---|
| Yedek yolu | `D:\finans_BACKUP_STABLE_KREDI_TAKSIT_DUZENLEME_20260605` |
| Durum | ✅ Oluşturuldu |

---

## Uygulanan Değişiklikler

### Kredi Banka Görünürlüğü (K1)

Kredi kart başlığında banka badge **zaten mevcuttu** — mevcut stable'dan korundu.  
Her kredi satırında: `[İga Kredi] [Finansbank] [3 taksit kaldı]` formatında görünüyor.  
26 kredinin 25'inde banka bilgisi dolu.

---

### Taksit Banka Görünürlüğü (K1)

**Kaynak önceliği:** `odemeler.banka` → boşsa `odemeler.not_` → ikisi de boşsa `—`

Taksit tablosuna yeni **"Banka"** sütunu eklendi:
- 197 taksit kaydının tümünde `not_` = banka adı (import kalıntısı: Finansbank, Kuveytturk, Vakıf Katılım vb.)
- `odemeler.banka` kolonu taksitlerde şimdilik boş; `not_` fallback ile gösterim sağlandı
- Görünüm: mavi badge `[Kuveytturk]`, `[Vakıf Katılım]`, `[TEB Bankası]`

---

### Taksit Tarih Değiştirme (K2)

Her taksit satırına **✏ Düzenle** butonu eklendi.  
Modal: `taksit-duzenle-modal`  
- Üstte açıklama (readonly) + mevcut değer bilgi banner'ı
- `Vade Tarihi` input alanı
- `Taksit Tutarı` input alanı
- `Not / Açıklama` opsiyonel alan (düzeltme sebebi için)

Kaydet → `PUT /api/odemeler/<id>` — sadece seçilen taksit güncellenir.

---

### Taksit Tutar Değiştirme (K2)

Aynı modal üzerinden tutar da değiştirilebiliyor.  
Faiz, masraf, ara ödeme, banka güncellemesi senaryoları için kullanılabilir.  
Diğer taksitler ve kredi ana kaydı **değişmez.**

---

### Takvim Entegrasyonu

`saveTaksitDuzenle()` kaydet sonrası `renderCalendar()` çağırıyor.  
Taksit tarihi değişince takvim otomatik güncelleniyor — vade bazlı.  
Taksit tutarı değişince KPI otomatik güncelleniyor — tutar bazlı.

---

## Test Kaydı

| Alan | Değer |
|------|-------|
| Test taksit ID | `fd5019d9-4` |
| Taksit adı | Patch - ışık - Kalıp 3.Taksit |
| Banka | Vakıf Katılım (`not_` kaynağı) |
| **Test değiştir** | vade `2026-04-20` → `2026-04-21`, tutar `862,037` → `999,999` ✅ |
| **Geri al** | vade `2026-04-20`, tutar `862,037` ✅ |
| Diğer taksitler | Etkilenmedi ✅ |
| Toplam taksit sayısı | 197 (değişmedi) ✅ |

---

## Geri Alma Testi

Test taksit değiştirildi, ardından eski değerlerine restore edildi.  
DB'de son durum: vade=`2026-04-20`, tutar=`862037.3` (orijinal).

---

## DB / Backend / CPS Durumu

| Alan | Durum |
|------|-------|
| DB değişikliği | ❌ Yok |
| `finans_server.py` değişikliği | ❌ Yok |
| CPS dokunuldu | ❌ Hayır |
| K3 audit | ❌ Yapılmadı — ihtiyaç duyulursa sonraki fazda |

---

## DB Son Durum

| Tablo | Kayıt |
|-------|-------|
| `odemeler` (`tip='taksit'`) | 197 |
| `odemeler` (bekleyen taksit) | 66 |
| `krediler` | 26 |
| `krediler` (banka dolu) | 25 / 26 |

---

## Korunacak Kurallar

- Taksit düzenleme sadece seçilen satırı değiştirir
- Kredi ana kaydı (`krediler` tablosu) düzenleme modalından değişmez
- Diğer taksitler etkilenmez
- Takvim ve KPI otomatik güncellenir (`vade` / `tutar` bazlı hesap)
- `not_` alanı banka fallback olarak kullanılmaya devam eder
