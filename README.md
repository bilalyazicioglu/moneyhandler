# MoneyHandler

<p align="center">
  <img src="assets/logo.png" alt="MoneyHandler Logo" width="120">
</p>

<p align="center">
  <b>Kişisel Finans Yönetimi Uygulaması</b><br>
  Gelir, gider ve hesaplarınızı kolayca takip edin
</p>

---

## Özellikler

- **Çoklu Para Birimi** - TRY, USD, EUR desteği
- **Hesap Yönetimi** - Banka, nakit, kredi kartı hesapları
- **Gelir/Gider Takibi** - Kategorili işlem kaydı
- **Planlanan İşlemler** - Gelecek ödemeleri takip edin
- **Inline Düzenleme** - Split-pane detay paneli ile hızlı düzenleme

## Kurulum

### Geliştirme
```bash
git clone https://github.com/bilalyazicioglu/moneyhandler.git
cd moneyhandler
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Build (Executable Oluşturma)
```bash
pip install pyinstaller
pyinstaller build.spec --clean --noconfirm
```
Çıktı: `dist/MoneyHandler.app` (macOS) veya `dist/MoneyHandler.exe` (Windows)

## Teknoloji

| Teknoloji | Kullanım |
|-----------|----------|
| Python 3 | Backend |
| PyQt6 | GUI Framework |
| SQLite | Veritabanı |
| PyInstaller | Executable Build |

## Proje Yapısı

```
moneyhandler/
├── main.py              # Uygulama giriş noktası
├── config.py            # Ayarlar ve sabitler
├── assets/              # Logo ve ikonlar
├── controllers/         # İş mantığı
├── models/              # Veri modelleri
├── views/               # PyQt6 arayüzleri
├── data/                # Veritabanı işlemleri
└── build.spec           # PyInstaller yapılandırması
```

## Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.
