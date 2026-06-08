# STABLE — TAKVİM FAZ1

> **Tarih:** 5 Haziran 2026  
> **Stable yedek:** `D:\finans_BACKUP_STABLE_TAKVIM_FAZ1_20260605` (14 dosya / 988 KB)  
> **Kapsam:** `D:\finans` bağımsız finans sistemi  
> **CPS:** Dokunulmadı.  

---

## Yapılan Değişiklikler (Bu Oturumda)

### 1. Login Düzeltmesi
| Dosya | Satır | Değişiklik |
|-------|-------|-----------|
| `finans_yonetim.html` | 1515 | `API_BASE = 'http://192.168.1.16:5058'` → `API_BASE = ''` |

**Sebep:** Sunucu `192.168.110.186:5058`'de çalışırken tüm API çağrıları eski üretim IP'si olan `192.168.1.16:5058`'e gidiyordu. Senkron XHR timeout nedeniyle tarayıcı donuyordu.

---

### 2. Şirket Üst Filtresi Kaldırıldı
| Dosya | Değişiklik |
|-------|-----------|
| `finans_yonetim.html` | Header'daki Solariz/NexGen/Pera/Şahsi butonları → "Şahin Taban AYK Finans" başlığı |
| `finans_yonetim.html` | `entityData()` filtresi kaldırıldı — tüm veri görünür |
| `finans_yonetim.html` | `renderKasa()` entity parametresi kaldırıldı |
| `finans_server.py` | `/api/kasa` entity opsiyonel hale getirildi |

**Sebep:** Tek yönetim ekranı; firma ayrımı kayıt içinde `entity` alanıyla korunuyor.

---

### 3. Takvim Faz1 — Finans Karar Ekranı

#### CSS Değişiklikleri
| Öncesi | Sonrası |
|--------|---------|
| `aspect-ratio: 1` (kare) | `min-height: 72px` (dikdörtgen) |
| Sadece 5px nokta | Nokta + tutar + net |
| Tek arka plan rengi | `has-overdue` (kırmızı) / `has-payment` (sarı) ayrımı |
| — | Yeni CSS: `.cal-kpi-card`, `.day-tutar`, `.day-gelir`, `.day-net-pos/neg` |

#### HTML Değişiklikleri
| Bölüm | Öncesi | Sonrası |
|-------|--------|---------|
| Takvim başlığı | `📅 Ödeme Takvimi` | `📅 Finans Takvimi` |
| Layout | Tek sütun | 2 sütun (takvim sol + KPI sağ) |
| Renk açıklaması | Yok | Üstte renk legend satırı |
| Sağ panel | Yok | 6 KPI kartı |

#### Yeni/Güncellenen JS Fonksiyonları
| Fonksiyon | Tip | Açıklama |
|-----------|-----|---------|
| `calTipRenk(o)` | Yeni | Ödeme tipine göre renk döndürür |
| `fmtK(n)` | Yeni | Tutar kısaltma: 1.250.000→1.25M, 85.000→85K |
| `renderCalKPI(odemeler, plan)` | Yeni | Sağ panel 6 KPI kartını doldurur |
| `renderCalendar()` | Güncellendi | Renk + tutar + net + tahsilat noktası |
| `showCalDay(dateStr)` | Güncellendi | Tip rozeti + gün özeti + tahsilat satırı |

#### Renk Mantığı (Faz1)
| Tip | Renk | Kod |
|-----|------|-----|
| Gecikmiş (tüm tipler) | Kırmızı | `#dc2626` |
| Taksit / Kredi | Mavi | `#2563eb` |
| Çek (`Çek:` prefix) | Mor | `#7c3aed` |
| Tedarikçi (çek değil) | Turuncu | `#ea580c` |
| Maaş | Teal | `#0891b2` |
| Tahsilat (planlama gelir) | Yeşil | `#16a34a` |
| Diğer | Gri | `#6b7280` |

---

## Çalışan Ekranlar (5 Haziran 2026)

| Ekran | Durum | Veri |
|-------|-------|------|
| Login (altan/adem) | ✅ | HTTP 200, <25ms |
| Özet | ✅ | Tüm şirketler: 715 ödeme |
| Ödemeler | ✅ | 715 kayıt, filtreli liste |
| Krediler | ✅ | 27 kredi |
| Çekler | ✅ | 41 kayıt (`Çek:` prefix) |
| Kasa | ✅ | Endpoint çalışıyor, 0 kayıt |
| Takvim | ✅ | Faz1: renk + tutar + KPI |
| Nakit Akışı | ⚠️ | Çalışıyor, bakiye hardcoded (2.5M TL) |
| 12 Ay Planlama | ✅ | Firma filtresi: Tüm/Solariz/NexGen/Pera AŞ |
| TCMB Kurlar | ✅ | USD:45.97 EUR:53.42 XAU:0.0 |

---

## KPI Verileri (5 Haziran 2026 itibarıyla)

| KPI | Değer |
|-----|-------|
| Bugün çıkacak | 0 kayıt / 0 TL |
| 7 gün ödeme | 0 kayıt / 0 TL |
| 30 gün ödeme | 14 kayıt / 3.473.024 TL |
| Bekleyen çek | 22 kayıt / 4.777.586 TL |
| Bekleyen taksit | 66 kayıt / 20.399.666 TL |
| Gecikmiş toplam | 67 kayıt / 28.942.495 TL |

---

## Korunacak Kurallar

### Mimari
- `D:\finans` bağımsız sistem — CPS'e entegre edilmeyecek
- Port: `5058`
- DB: `finans.db` (SQLite) — şema değiştirilmeyecek
- `entity` kolonu: `odemeler`, `krediler`, `kasa` tablolarında korunuyor
- `planlama.firma` kolonu korunuyor

### Firma Mantığı
- Üst tab filtresi **kaldırıldı** — tüm şirket verisi tek ekranda
- 12 Ay Planlama'daki firma dropdown'u **rapor filtresi** olarak kalıyor
- Kayıt eklerken entity/firma dropdown'ları **korunuyor** (ileride kayıt bazlı filtre için)

### Takvim Faz1 Kuralları
- `calTipRenk()` — renk fonksiyonu dokunulmayacak
- `renderCalKPI()` — KPI hesabı `entityData()` + `_planCache` üzerinden
- Çek ayrımı: `aciklama.indexOf('ek:') === 1` (Ç**ek:** prefix kontrolü)
- Gün tutar kısaltması: `fmtK()` — milyon için M, bin için K

### Eksik / Sonraki Faz
- Nakit akışı başlangıç bakiyesi hardcoded (2.5M TL) — Faz2'de kasa tablosundan okunacak
- Tahsilat verisi (planlama gelir) tüm kayıtlar geçmişe ait — ilerisi için girilmeli
- `XAU` kuru = 0.0 — TCMB parse sorunu
- `kasa` tablosu boş

---

## Dosya Envanteri (`D:\finans`)

| Dosya | Son Değişiklik | Durum |
|-------|---------------|-------|
| `finans_server.py` | Bu oturum | Kasa entity opsiyonel |
| `finans_yonetim.html` | Bu oturum | Login + entity kaldırma + Takvim Faz1 |
| `finans.db` | 14.04.2026 | Dokunulmadı |
| `finans_import.py` | 11.04.2026 | Dokunulmadı |
| `finans_kredi_reimport.py` | 11.04.2026 | Dokunulmadı |
| `finans_planlama_import.py` | 11.04.2026 | Dokunulmadı |
| `finans_kredi_duzelt.py` | 11.04.2026 | Dokunulmadı |
| `finans_son_duzelt.py` | 11.04.2026 | Dokunulmadı |

---

*Stable: `D:\finans_BACKUP_STABLE_TAKVIM_FAZ1_20260605`*
