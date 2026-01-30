#!/bin/bash

# MoneyHandler Deploy Script
# Uygulamayı derler ve Applications klasörüne kopyalar

echo "MoneyHandler derleniyor..."

source venv/bin/activate
pyinstaller build.spec --noconfirm

if [ $? -eq 0 ]; then
    echo "Derleme başarılı!"
    echo "Applications klasörüne kopyalanıyor..."
    rm -rf /Applications/MoneyHandler.app
    cp -R dist/MoneyHandler.app /Applications/
    
    echo "Tamamlandı! MoneyHandler.app güncellendi."
else
    echo "Derleme başarısız!"
    exit 1
fi
