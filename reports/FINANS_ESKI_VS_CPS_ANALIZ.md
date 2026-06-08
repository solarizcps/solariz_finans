# FİNANS: ESKİ SİSTEM vs CPS KARŞILAŞTIRMA RAPORU

> **Tarih:** 5 Haziran 2026  
> **Kapsam:** `d:\finans` (eski bağımsız finans) vs `CPS_GIT_TEST/app/modules/finans` (canlı CPS)  
> **Yöntem:** Kaynak kodu + HTML + script okuma; kod değişikliği yapılmamıştır.

---

## Workspace Envanteri (`d:\finans`)

| Dosya | Rol |
|-------|-----|
| `finans_server.py` | Flask API, port 5058, SQLite `finans.db` |
| `finans_yonetim.html` | ~3896 satır SPA arayüzü |
| `finans_import.py` | Excel → DB toplu aktarım (6 sayfa) |
| `finans_planlama_import.py` | Ödeme Tablo → `planlama` tablosu |
| `finans_kredi_reimport.py` | Kredi/taksit yeniden yükleme |
| `finans_kredi_duzelt.py` | Nakit İhtiyacı, UGG, Işık düzeltmeleri |
| `finans_son_duzelt.py` | Nakit İhtiyacı toplam düzeltme |
| `planlama_server.py` | **Üretim planlama** (finans değil, port 5057) |
| `planlama_cps.html` | **Üretim planlama** arayüzü (finans değil) |
| `finans_kur_ve_baslat.bat`, `FinansServer_Task.xml`, `KURULUM.txt` | Kurulum |

> `planlama_server.py` ve `planlama_cps.html` finans modülü değildir; MSSQL üzerinden sipariş/görev/numune/kalite yönetir. Bu rapor kapsamı dışındadır.

---

## 1. Eski Finans Ne Yapıyordu?

### Mimari
- **Sunucu:** `finans_server.py`, port **5058**, bağımsız Flask + CORS
- **DB:** SQLite `finans.db` (otomatik oluşur, `init_db()`)
- **UI:** Tek HTML dosyası (`finans_yonetim.html`), `API_BASE = http://192.168.1.16:5058`
- **Firma entity'leri:** solariz, nexgen, pera, sahsi (header sekmeleri)

### Veritabanı Tabloları

| Tablo | Amaç |
|-------|------|
| `odemeler` | Tüm ödeme kalemleri (taksit, çek, tedarikçi, vergi, maaş, kredi-karti…) |
| `krediler` | Kredi özet kayıtları (ad, banka, toplam, taksit sayısı, kalan…) |
| `planlama` | 12 ay planlama — firma, kategori, gelir/gider |
| `kasa` | Nakit giriş/çıkış hareketleri |
| `kur_cache` | TCMB USD/EUR/XAU günlük önbellek |
| `kullanicilar` | altan/adem plaintext şifre auth |

### API Uçları
`/api/login` · `/api/kurlar` · `/api/kasa` · `/api/odemeler` · `/api/krediler` · `/api/planlama` · `/api/import` · `/api/ozet`

### Ekranlar — 8 Sekme (`finans_yonetim.html`)

| # | Sekme | Ne yapıyor |
|---|-------|-----------|
| 1 | **Özet** | Aylık ödeme kartları, geciken/ödenen sayaçlar, kredi/çek progress bar'ları |
| 2 | **Ödemeler** | Filtreli liste, CRUD, "ödendi" işaretleme, Excel export |
| 3 | **Krediler** | Kredi kartları, taksit timeline, otomatik taksit üretimi |
| 4 | **Çekler** | `odemeler` içinde `Çek:` prefix'li kayıtlar, aylık accordion, ödeme işaretleme |
| 5 | **Kasa** | TCMB kurları + nakit giriş/çıkış + canlı bakiye |
| 6 | **Takvim** | Aylık ödeme takvimi, vade bazlı renkler |
| 7 | **Nakit Akışı** | 6 aylık şerit, günlük bakiye timeline, kritik gün uyarıları, manuel gelir ekleme |
| 8 | **12 Ay Planlama** | Firma × kategori × ay ızgara görünümü, tekrarlayan ödemeler |

### Excel Import Mantığı (`finans_import.py`)

Kaynak dosya: `Genel Durum 20.02.2026.xlsx`

| Sayfa | Hedef tablo | Veri tipi |
|-------|------------|-----------|
| Altan | `odemeler` (solariz) | Şahsi borçlar |
| Krediler / Krediler (2) | `krediler` (özet) + `odemeler` (taksit) | Banka kredisi taksitleri |
| Çekler | `odemeler` tip=`tedarikci`, aciklama=`Çek: {alıcı}` | Verilen çekler |
| Extra | `odemeler` (nexgen/solariz) | Tedarikçi ödemeleri |
| Ödeme Tablo | `odemeler` (birim eşlemesi ile) | Karma ödemeler |

Durum mantığı: `kalan==0` → `odendi`; vade `< 2026-04-11` → `gecikti`.

### Planlama Import (`finans_planlama_import.py`)
- Aynı Excel, **Ödeme Tablo** sayfası
- `KASA` + gelir sütunu → `planlama` kategori=`gelir` (tahsilat)
- Gider sütunu → kategori eşlemesi (maaş, kredi, vergi, fatura…)
- Ay bazlı gelir/gider/net özeti çıktısı

### Kredi Özel Scriptleri
| Script | Yaptığı |
|--------|---------|
| `finans_kredi_reimport.py` | `ozet_eslesme` sözlüğü ile Excel özet adı ↔ taksit adı eşleştirme; DELETE + yeniden yükleme |
| `finans_kredi_duzelt.py` | Nakit İhtiyacı -2/-3/-4 ayrımı, UGG duplike temizliği, Işık toplam güncelleme |
| `finans_son_duzelt.py` | Nakit İhtiyacı prefix matching ile toplam güncelleme |

### Tahsilat / Nakit Akışı Mimarisi
- **Tahsilat (Excel):** `finans_planlama_import.py` → `planlama` tablosuna gelir olarak yazılır
- **Nakit akışı gelirleri:** `_cfGelirler` dizisi — **sadece tarayıcı belleğinde**, DB'ye kaydedilmez
- **Başlangıç bakiyesi:** Sabit `2500000` TL (`renderNakit()` — TODO yorumu var)
- **Kasa API:** `/api/kasa` gerçek DB'ye yazar; ancak nakit akış ekranı kasa bakiyesini **kullanmaz**

---

## 2. CPS'e Taşınan Özellikler ✅

| Özellik | Eski konum | CPS konumu |
|---------|-----------|------------|
| Finans modülü (blueprint) | `finans_server.py` | `app/modules/finans/routes.py` → `/finans/*` |
| Auth entegrasyonu | Ayrı login (altan/adem plaintext) | `before_request` guard + `yetki('finans')` + sidebar rol sistemi |
| Entity filtreleme | `finans_yonetim.html` entity tab'ları | `takvim_service._entity_yetki_filtre`, manuel ödeme CRUD'u |
| Takvim görünümü | `renderCalendar()` | `/finans/takvim` + `takvim_service.py` (CARI/KART/MANUEL; boşsa DEMO) |
| Manuel ödemeler CRUD | `odemeler` genel listesi | `/finans/manuel-odemeler` + `finans_manuel_odeme` tablosu |
| Kredi kartı yönetimi | Genel `kredi` tipi vardı | `/finans/kredi-kartlari` + ekstre/hareket CRUD — **CPS'te yeni** |
| Kredi listesi (Excel migration) | `krediler` + reimport scriptleri | `/finans/konsol` → `kredi_anlasma_liste()` (`KaynakModul LIKE 'EXCEL%'`) |
| TCMB / kur | `/api/kurlar` | CPS `sistem_kur` servisi |
| Geciken ödemeler | `gecikti` durumu / özet | `/finans/geciken-odemeler` |
| Excel import (kısmi) | `Genel Durum` tam import | `/finans/cin-ofis` → `cin_ofis_excel.py` — **Çin ofis Excel'i, Genel Durum değil** |
| Çek veri modeli (ticari) | `odemeler` içinde string prefix | `Cek_Senet` + `finans_odeme_cek` (anlaşma ödeme planına bağlı) |
| Ödeme planı (müşteri tahsilat) | `planlama` gelir satırları | `finans_odeme_plan` + `Durum='GELDI'` tahsilat mantığı |
| Maliyet simülatörü | Yoktu | `/finans/simulator` — **CPS'te yeni** |
| Cari entegrasyon | Yoktu | `/finans/cari`, `/finans/cari-odemeler`, `Cari_Har` bağlantısı — **CPS'te yeni** |
| Anlaşma modeli | Yoktu | `/finans/anlasma`, `finans_anlasma`, model/avans/mahsup — **CPS'te yeni** |
| Çin ofis takibi | Yoktu | `/finans/cin-ofis` onay akışlı Excel import — **CPS'te yeni** |

---

## 3. Eksik Kalan Özellikler ❌

| Özellik | Eski konum | Neden önemli |
|---------|-----------|--------------|
| **Genel Durum Excel tam import** | `finans_import.py` (6 sayfa) | Tüm borç/çek/kredi/taksit verisinin tek seferde yüklenmesi |
| **Planlama import (Ödeme Tablo → gelir/gider matris)** | `finans_planlama_import.py` | 12 aylık nakit planının Excel'den otomatik kurulması |
| **Kredi reimport + düzeltme scriptleri** | `finans_kredi_reimport.py`, `finans_kredi_duzelt.py`, `finans_son_duzelt.py` | Nakit İhtiyacı gruplama, UGG duplike temizliği, özet↔taksit eşleştirme |
| **Çekler sekmesi (aylık accordion UI)** | `renderCekler()` | Verilen çeklerin vade bazlı takibi ve ödeme işaretleme — konsol boş |
| **Nakit akış ekranı** | `renderNakit()` | 6 aylık şerit, günlük bakiye timeline, kritik gün uyarıları; konsol placeholder |
| **12 Ay Planlama matrisi** | `renderPlanlama()` + `/api/planlama` | Firma × kategori × ay ızgara görünümü; konsol placeholder |
| **Kasa modülü** | `/api/kasa` + `renderKasa()` | Nakit giriş/çıkış + bakiye; konsol `kasa` sekmesi placeholder |
| **Ödemeler genel listesi** | `/api/odemeler` + ödemeler sekmesi | CPS konsol `odemeler` paneli: "FAZ 4'te aktif olacak" notu var |
| **Tek sayfa SPA (8 sekme)** | `finans_yonetim.html` | CPS'te konsol iskelet mevcut; çoğu sekme boş/placeholder |
| **Toplu API import endpoint** | `POST /api/import` | CPS'te JSON bulk import endpoint'i yok |
| **Tahsilat → nakit akış entegrasyonu** | `_cfGelirler` + planlama gelir | Birleşik nakit projektsiyon sistemi CPS'te yok |
| **Excel export (client-side XLSX)** | `exportData()` | Ödemeler listesinden XLSX indirme; CPS'te yok |
| **Özet dashboard (operasyonel)** | `renderOzet()` — 8 kart | Geciken/ödenen/bu ay özet kartları; CPS konsol KPI'ları farklı kaynaklara bağlı |

---

## 4. Eski Finans'ta CPS'ten Daha İyi Olan Yerler

### 1. Tek ekranda 8 fonksiyonel modül
Özet, ödemeler, krediler, çekler, kasa, takvim, nakit akışı, planlama aynı SPA'da çalışır. Sekme geçişi anlık, state korunur. CPS konsol'da çoğu sekme "FAZ X'te gelecek" placeholder'dır.

### 2. Genel Durum Excel pipeline (6 sayfa)
`finans_import.py` + `finans_planlama_import.py` + 3 kredi düzeltme scripti. Muhasebe Excel'inden tek komutla 715 ödeme / 27 kredi + taksit yüklenebilir. CPS'te bu pipeline **yok**.

### 3. Çek takibi (operasyonel)
Çekler `odemeler` tablosunda ayrı UI ile aylık gruplanır, vade renkleri var, "ödendi" işaretlenir. CPS `Cek_Senet` modeli ticari anlaşma çeklerine bağlıdır; konsol çek sekmesi **boş**.

### 4. Nakit akış simülasyonu (tam fonksiyonel)
6 aylık şerit, günlük bakiye hesaplama, kritik gün (bakiye < 0) listesi, manuel gelir ekleme (`cfGelirEkle`). CPS konsol roadmap'te "sıfırdan yazılacak" notu var; ekran **yok**.

### 5. Kredi + taksit birleşik model
`krediler` (özet) + `odemeler.tip=taksit` (detay) + `ozet_eslesme` eşleştirme sözlüğü. Taksit timeline görselleştirilmiş. CPS'te banka KOBİ kredisi/taksit modeli `finans_anlasma` üzerinden farklı kurgulanmış.

### 6. Hızlı ve bağımsız kurulum
`finans_kur_ve_baslat.bat` + Windows Task Scheduler XML; CPS bağımlılığı olmadan çalışır.

### 7. Excel export
`exportData()` ile client-side XLSX indirme; ödemeler listesi anlık Excel'e aktarılabilir.

---

## 5. CPS'te Daha İyi Olan Yerler

### 1. Kurumsal auth ve rol/yetki sistemi
Tek login, `sistem_rol` tabanlı yetki (`yetki('finans')`), admin/adem/altan/Muhasebe guard, audit log. Eski sistemde plaintext şifre.

### 2. Ticari finans modeli (anlaşma odaklı)
`finans_anlasma`, model, avans, mahsup, ödeme planı, çek detayı; müşteri projesi bazlı tahsilat takibi eski sistemde **yoktu**.

### 3. Cari / Korgun entegrasyonu
`/finans/cari`, `/finans/cari-odemeler`, `Cari_Har` bağlantısı — gerçek cari hesap izleme.

### 4. Maliyet simülatörü
`/finans/simulator` — proje maliyet senaryoları. Eski sistemde **yok**.

### 5. Çin ofis Excel import (onay akışlı)
Kur override, önizleme, onay adımları olan kontrollü import. Eski sistem import'u direkt DB'ye yazardı.

### 6. Kredi kartı modülü (ayrı)
`finans_kredi_karti`, ekstre, hareket CRUD. Eski sistemde yalnızca genel `kredi` tipi vardı.

### 7. Service katmanı (temiz mimari)
`konsol_service`, `takvim_service`, `manuel_odeme_service`, `cin_ofis_excel.py`; eski sistemde tüm mantık tek `finans_server.py` + 3896 satır HTML JS içindeydi.

### 8. Ölçeklenebilir veri mimarisi
MSSQL veya mock DB; modüler tablo yapısı. Eski sistem tek SQLite dosyası.

---

## 6. Taşınması Gereken Ekranlar (Öncelik Sırasıyla)

| Öncelik | Ekran | Gerekçe |
|---------|-------|---------|
| 🔴 1 | **Nakit Akışı** | Günlük karar ekranı; CPS'te hiç yok |
| 🔴 2 | **Genel Durum Excel import** | Veri girişini saatlerden dakikalara indirir |
| 🔴 3 | **Çekler sekmesi** | Operasyonel çek vadeleri günlük kullanımda; konsol boş |
| 🟠 4 | **12 Ay Planlama matrisi** | Gelir/gider projektsiyon; konsol placeholder |
| 🟠 5 | **Ödemeler genel listesi** | Tüm tip/birim/firma filtreli ödeme yönetimi |
| 🟠 6 | **Kasa modülü** | TCMB + nakit hareket + bakiye; nakit akışla birleşmeli |
| 🟡 7 | **Kredi + taksit yönetimi** | `ozet_eslesme` ve Nakit İhtiyacı gruplama mantığı dahil |
| 🟡 8 | **Özet dashboard** | Geciken/ödenen kartları + kredi/çek progress bar'ları |

---

## 7. Taşınmaması Gereken Eski Kodlar

| Kod | Neden taşınmamalı |
|-----|------------------|
| `finans_server.py` auth (`kullanicilar` tablosu, plaintext) | CPS `sistem_rol` / session ile değiştirilmeli; plaintext şifre güvensiz |
| `finans_yonetim.html` tamamı (tek dosya SPA) | CPS native `base.html` extend pattern'ına uymaz; copy-paste kod mirası oluşturur |
| `finans.db` doğrudan production import | Eski DB referans/arşiv olarak tutulmalı; CPS tabloları farklı şema |
| Senkron XHR (`apiGet` false async) | CPS'te modern async fetch pattern kullanılıyor |
| `_cfGelirler` bellek içi gelir dizisi | Sayfa yenilenince kaybolur; DB tablosuna taşınmalı, olduğu gibi kullanılamaz |
| Sabit `baslangicBakiye = 2500000` | Hardcoded değer; CPS'te kasa API'den dinamik okunmalı |
| `planlama_server.py` + `planlama_cps.html` | Üretim planlama sistemi; finans modülü değil, ayrı tutulacak |
| Port 5058 paralel sunucu | Migration tamamlanınca kapatılacak; iki sistem uzun süre paralel kalırsa veri çatışması riski |

---

## 8. Riskler

| Risk | Olası Etki | Önerilen Aksiyon |
|------|-----------|------------------|
| **İki paralel finans sistemi (5058 + 8080)** | Veri çatışması; kullanıcılar hangi ekrana bakacağını bilemez | Tek kaynak (CPS) kararı; 5058 read-only → kapatma takvimi |
| **Genel Durum Excel import kaybı** | 700+ ödeme / 27 kredi manuel giriş yükü; haftalık güncelleme yapılamaz | Genel Durum import'unu CPS service olarak yeniden yaz veya arşiv DB'den kontrollü migration |
| **Nakit akış ekranı yok** | Nakit açığı kararları eski sisteme bağımlı kalır; CPS'e geçilirse kör kalınır | `nakit_akisi_service` öncelikli geliştirme |
| **Takvim DEMO fallback** | DB boşken sahte veri gösterilir (`_demo_kayitlar`); yanlış güven oluşturur | CEK/KREDI DB kaynakları tamamlanana kadar DEMO modu açıkça etiketlenmeli |
| **Farklı çek modelleri** | Operasyonel çekler (`Çek:` prefix) ile anlaşma çekleri (`Cek_Senet`) karışır | İki çek tipini açıkça ayır; konsol için ayrı tablo |
| **Kredi model uyumsuzluğu** | `krediler+odemeler` ile `finans_anlasma` şemaları farklı; taksit takibi çakışır | Veri eşleme haritası + test migration script |
| **Tahsilat mantığı dağınık** | Planlama gelir vs `odeme_plan GELDI` vs bellek geliri — üç ayrı kaynak | Tek "gelir/tahsilat" tablosu, nakit akışa bağlama |
| **`kullanicilar` tablosu plaintext şifre** | Güvenlik açığı; production'a taşınmamalı | Eski sistemdeki hash'siz şifreler CPS'e geçişte sıfırlanmalı |
| **`SOLARIZ_CPS_SERVER` workspace'te yok** | Bu analiz `CPS_GIT_TEST` üzerinden yapıldı; canlı production farklı olabilir | Canlı CPS kodunu workspace'e ekleyin veya doğru path'i belirtin |

---

## Özel Kontrol Sonuçları

| Kontrol | Durum | Detay |
|---------|-------|-------|
| **Excel mantığı** | ⚠️ Kısmen kayboldu | Eski `finans_import.py` (6 sayfa Genel Durum) CPS'te yok. Yalnızca Çin ofis Excel'i ve `EXCEL%` anlaşma migration'ı var. |
| **Ödeme planlama** | ❌ Farklı | Eski: `planlama` tablosu + 12 ay ızgara + Excel import. CPS: `finans_odeme_plan` anlaşma bazlı; konsol planlama sekmesi placeholder. |
| **Çek sistemi** | ❌ Farklı | Eski: `odemeler` + `Çek:` prefix + tam UI + aylık accordion. CPS: `Cek_Senet`/`finans_odeme_cek` ticari anlaşmaya bağlı; konsol çek sekmesi boş. |
| **Kredi hesapları** | ⚠️ Farklı model | Eski: `krediler` + `taksit` odemeler + 3 düzeltme scripti. CPS: `finans_anlasma` EXCEL migration + ayrı `finans_kredi_karti` modülü. |
| **Tahsilat mantığı** | ⚠️ Kısmen duruyor | Eski: planlama gelir + bellek geliri. CPS: `finans_odeme_plan GELDI` anlaşma tahsilatı var; nakit/tahsilat birleşimi yok. |
| **Nakit akış ekranı** | ❌ Aynı sonucu vermiyor | Eski: tam fonksiyonel (6 ay, günlük, kritik gün uyarıları). CPS: konsol sekmesi placeholder; roadmap "sıfırdan yazılacak". |

---

## CPS Finans Route Özeti (Mevcut)

**Ticari finans:**  
`/finans/` · `/finans/cari` · `/finans/anlasma` · `/finans/geciken-odemeler` · `/finans/simulator` · `/finans/cin-ofis`

**Native konsol (5058 taşıma hedefi):**  
`/finans/konsol` · `/finans/cari-odemeler` · `/finans/kredi-kartlari` · `/finans/takvim` · `/finans/manuel-odemeler` · `/finans/kart-borc-raporu` · `/finans/api/konsol-kpi`

**CPS DB finans tabloları:**  
`finans_anlasma` · `finans_anlasma_model` · `finans_avans` · `finans_avans_mahsup` · `finans_odeme_plan` · `finans_odeme_cek` · `finans_simulasyon` · `Banka_Kart` · `Kasa_Kart` · `Cek_Senet` · `finans_manuel_odeme` · `finans_kredi_karti` · `finans_kredi_karti_ekstre` · `finans_kredi_karti_hareket` · `finans_cari_odeme_durum`

---

*Rapor `d:\finans\reports\FINANS_ESKI_VS_CPS_ANALIZ.md` — Kaynak kod okuması, kod değişikliği yapılmamıştır.*
