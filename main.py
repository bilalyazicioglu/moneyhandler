#!/usr/bin/env python3
"""
Kişisel Finans Yönetim Sistemi

Ana uygulama giriş noktası (Entry Point).
PyQt6 ile geliştirilmiş, MVC mimarili masaüstü uygulaması.

Özellikler:
- Çoklu para birimi desteği (TRY, USD, EUR)
- Nakit ve banka hesapları takibi
- Gelir/gider işlemleri yönetimi
- Planlanan işlemleri gerçek işlemlere dönüştürme
- Dashboard ile özet görüntüleme

Kullanım:
    python main.py
    
Author: Kişisel Finans Projesi
Version: 1.0.0
"""

import sys
from typing import NoReturn

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from controllers.main_controller import MainController
from views.main_window import MainWindow


def main() -> NoReturn:
    """
    Uygulamanın ana fonksiyonu.
    
    PyQt6 uygulamasını başlatır, controller ve ana pencereyi oluşturur.
    """
    # Qt uygulaması oluştur
    app = QApplication(sys.argv)
    
    # Uygulama meta bilgileri
    app.setApplicationName("Kişisel Finans Yönetimi")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MoneyHandler")
    
    # Varsayılan font ayarla (sistem fontu)
    font = QFont()
    font.setPointSize(13)
    app.setFont(font)
    
    # Controller oluştur
    controller = MainController()
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow(controller)
    window.show()
    
    # Uygulama kapatıldığında temizlik
    def cleanup() -> None:
        """Uygulama kapatılırken temizlik yapar."""
        controller.close()
    
    app.aboutToQuit.connect(cleanup)
    
    # Uygulama döngüsünü başlat
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
