#!/bin/bash

# MoneyHandler Deploy Script
# Uygulamayı derler ve Applications klasörüne kopyalar

echo "🔨 MoneyHandler derleniyor..."

# Virtual environment aktifleştir
source venv/bin/activate

# PyInstaller ile derle
pyinstaller build.spec --noconfirm

if [ $? -eq 0 ]; then
    echo "Derleme başarılı!"
    
    # Eski uygulamayı sil ve yenisini kopyala
    echo "Applications klasörüne kopyalanıyor..."
    rm -rf /Applications/MoneyHandler.app
    cp -R dist/MoneyHandler.app /Applications/
    
    echo "Tamamlandı! MoneyHandler.app güncellendi."
else
    echo "Derleme başarısız!"
    exit 1
fi
