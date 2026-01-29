"""
Kişisel Finans Yönetim Sistemi - Konfigürasyon Modülü

Bu modül uygulama genelinde kullanılan sabitleri, renk paletini,
para birimi ayarlarını ve veritabanı yolunu içerir.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import sys
import os




def get_database_path() -> Path:
    """PyInstaller ve geliştirme modunda çalışan veritabanı yolu."""
    # PyInstaller bundle içinde mi?
    if getattr(sys, 'frozen', False):
        # Kullanıcı belgeler klasörüne kaydet
        app_data = Path.home() / ".moneyhandler"
    else:
        # Geliştirme modu - proje dizini
        app_data = Path(__file__).parent / "data"
    
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data / "finance.db"

DATABASE_PATH: Path = get_database_path()




@dataclass(frozen=True)
class Currency:
    """Para birimi veri sınıfı."""
    code: str
    symbol: str
    name: str


# Desteklenen para birimleri
CURRENCIES: Dict[str, Currency] = {
    "TRY": Currency(code="TRY", symbol="₺", name="Türk Lirası"),
    "USD": Currency(code="USD", symbol="$", name="Amerikan Doları"),
    "EUR": Currency(code="EUR", symbol="€", name="Euro"),
}

# Ana para birimi (Dashboard'da tüm varlıklar bu birime çevrilir)
BASE_CURRENCY: str = "TRY"

# Döviz kurları (1 birim -> TRY)
EXCHANGE_RATES: Dict[str, float] = {
    "TRY": 1.0,
    "USD": 43.50,  
    "EUR": 51.70, 
}


def convert_to_base_currency(amount: float, from_currency: str) -> float:
    """
    Verilen miktarı ana para birimine (TRY) çevirir.
    
    Args:
        amount: Çevrilecek miktar
        from_currency: Kaynak para birimi kodu (TRY, USD, EUR)
        
    Returns:
        TRY cinsinden miktar
        
    Raises:
        ValueError: Geçersiz para birimi kodu
    """
    if from_currency not in EXCHANGE_RATES:
        raise ValueError(f"Geçersiz para birimi: {from_currency}")
    
    return amount * EXCHANGE_RATES[from_currency]


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Bir para biriminden diğerine dönüştürür.
    
    Args:
        amount: Çevrilecek miktar
        from_currency: Kaynak para birimi kodu (TRY, USD, EUR)
        to_currency: Hedef para birimi kodu (TRY, USD, EUR)
        
    Returns:
        Hedef para birimi cinsinden miktar
        
    Raises:
        ValueError: Geçersiz para birimi kodu
    """
    if from_currency == to_currency:
        return amount
    
    if from_currency not in EXCHANGE_RATES or to_currency not in EXCHANGE_RATES:
        raise ValueError(f"Geçersiz para birimi")
    
    # Önce TRY'ye çevir, sonra hedef para birimine
    try_amount = convert_to_base_currency(amount, from_currency)
    return try_amount / EXCHANGE_RATES[to_currency]




@dataclass(frozen=True)
class Colors:
    """Uygulama renk paleti."""
    PRIMARY: str = "#7C3AED"
    PRIMARY_HOVER: str = "#8B5CF6"
    PRIMARY_DARK: str = "#6D28D9"
    SECONDARY: str = "#06B6D4"
    ACCENT: str = "#F43F5E"
    
    BG_DARK: str = "#0F0F1A"
    BG_CARD: str = "#1A1A2E"
    BG_ELEVATED: str = "#252542"
    BG_INPUT: str = "#2A2A4A"
    
    TEXT_PRIMARY: str = "#F8FAFC"
    TEXT_SECONDARY: str = "#94A3B8"
    TEXT_MUTED: str = "#64748B"
    
    SUCCESS: str = "#10B981"
    SUCCESS_LIGHT: str = "#34D399"
    DANGER: str = "#EF4444"
    DANGER_LIGHT: str = "#F87171"
    WARNING: str = "#F59E0B"
    INFO: str = "#3B82F6"
    
    BORDER: str = "#334155"
    BORDER_LIGHT: str = "#475569"
    
    GRADIENT_START: str = "#7C3AED"
    GRADIENT_END: str = "#06B6D4"



COLORS = Colors()




class TransactionType:
    """İşlem tipi sabitleri."""
    INCOME: str = "income"
    EXPENSE: str = "expense"





WINDOW_MIN_WIDTH: int = 1100
WINDOW_MIN_HEIGHT: int = 750

TABLE_ROW_HEIGHT: int = 48

UPCOMING_DAYS_THRESHOLD: int = 7




def get_stylesheet() -> str:
    """
    Uygulama genelinde kullanılacak Qt stil şablonunu döndürür.
    
    Returns:
        Qt stylesheet string
    """
    return f"""
        /* Ana pencere */
        QMainWindow {{
            background-color: {COLORS.BG_DARK};
        }}
        
        /* Widget'lar */
        QWidget {{
            background-color: {COLORS.BG_DARK};
            color: {COLORS.TEXT_PRIMARY};
            font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
        }}
        
        /* Sekmeler */
        QTabWidget::pane {{
            border: none;
            background-color: {COLORS.BG_DARK};
            border-radius: 0px;
        }}
        
        QTabBar {{
            background-color: {COLORS.BG_CARD};
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {COLORS.TEXT_SECONDARY};
            padding: 16px 32px;
            margin: 0px;
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: 500;
            font-size: 14px;
        }}
        
        QTabBar::tab:selected {{
            color: {COLORS.TEXT_PRIMARY};
            border-bottom: 3px solid {COLORS.PRIMARY};
            background-color: transparent;
        }}
        
        QTabBar::tab:hover:!selected {{
            color: {COLORS.TEXT_PRIMARY};
            background-color: rgba(124, 58, 237, 0.1);
        }}
        
        /* Butonlar */
        QPushButton {{
            background-color: {COLORS.PRIMARY};
            color: {COLORS.TEXT_PRIMARY};
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
        }}
        
        QPushButton:hover {{
            background-color: {COLORS.PRIMARY_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS.PRIMARY_DARK};
        }}
        
        QPushButton:disabled {{
            background-color: {COLORS.BG_INPUT};
            color: {COLORS.TEXT_MUTED};
        }}
        
        /* İkincil buton */
        QPushButton[class="secondary"] {{
            background-color: {COLORS.BG_ELEVATED};
            border: 1px solid {COLORS.BORDER};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: {COLORS.BG_INPUT};
            border-color: {COLORS.BORDER_LIGHT};
        }}
        
        /* Tehlike butonu */
        QPushButton[class="danger"] {{
            background-color: {COLORS.DANGER};
        }}
        
        QPushButton[class="danger"]:hover {{
            background-color: {COLORS.DANGER_LIGHT};
        }}
        
        /* Başarı butonu */
        QPushButton[class="success"] {{
            background-color: {COLORS.SUCCESS};
        }}
        
        QPushButton[class="success"]:hover {{
            background-color: {COLORS.SUCCESS_LIGHT};
        }}
        
        /* Tablolar */
        QTableWidget {{
            background-color: {COLORS.BG_CARD};
            border: 1px solid {COLORS.BORDER};
            border-radius: 12px;
            gridline-color: {COLORS.BORDER};
            outline: none;
        }}
        
        QTableWidget::item {{
            padding: 12px 16px;
            border: none;
            border-bottom: 1px solid {COLORS.BORDER};
        }}
        
        QTableWidget::item:selected {{
            background-color: rgba(124, 58, 237, 0.2);
            color: {COLORS.TEXT_PRIMARY};
        }}
        
        QTableWidget::item:hover {{
            background-color: rgba(124, 58, 237, 0.1);
        }}
        
        QHeaderView::section {{
            background-color: {COLORS.BG_ELEVATED};
            color: {COLORS.TEXT_SECONDARY};
            padding: 14px 16px;
            border: none;
            border-bottom: 1px solid {COLORS.BORDER};
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        QHeaderView::section:first {{
            border-top-left-radius: 12px;
        }}
        
        QHeaderView::section:last {{
            border-top-right-radius: 12px;
        }}
        
        /* Input alanları */
        QLineEdit, QDoubleSpinBox, QSpinBox, QDateEdit, QComboBox {{
            background-color: {COLORS.BG_INPUT};
            color: {COLORS.TEXT_PRIMARY};
            border: 1px solid {COLORS.BORDER};
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
        }}
        
        QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, 
        QDateEdit:focus, QComboBox:focus {{
            border: 2px solid {COLORS.PRIMARY};
            background-color: {COLORS.BG_ELEVATED};
        }}
        
        QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover,
        QDateEdit:hover, QComboBox:hover {{
            border-color: {COLORS.BORDER_LIGHT};
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: 12px;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS.TEXT_SECONDARY};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {COLORS.BG_CARD};
            color: {COLORS.TEXT_PRIMARY};
            selection-background-color: {COLORS.PRIMARY};
            border: 1px solid {COLORS.BORDER};
            border-radius: 8px;
            padding: 4px;
        }}
        
        /* Text Edit */
        QTextEdit {{
            background-color: {COLORS.BG_INPUT};
            color: {COLORS.TEXT_PRIMARY};
            border: 1px solid {COLORS.BORDER};
            border-radius: 8px;
            padding: 12px;
        }}
        
        QTextEdit:focus {{
            border: 2px solid {COLORS.PRIMARY};
        }}
        
        /* Etiketler */
        QLabel {{
            color: {COLORS.TEXT_PRIMARY};
            background-color: transparent;
        }}
        
        /* Scroll bar */
        QScrollBar:vertical {{
            background-color: {COLORS.BG_CARD};
            width: 10px;
            border-radius: 5px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {COLORS.BORDER};
            border-radius: 5px;
            min-height: 40px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS.BORDER_LIGHT};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        /* Grup kutuları */
        QGroupBox {{
            background-color: {COLORS.BG_CARD};
            border: 1px solid {COLORS.BORDER};
            border-radius: 12px;
            margin-top: 24px;
            padding: 20px;
            padding-top: 32px;
            font-weight: 600;
        }}
        
        QGroupBox::title {{
            color: {COLORS.TEXT_PRIMARY};
            subcontrol-origin: margin;
            left: 20px;
            top: 8px;
            padding: 0 8px;
            font-size: 14px;
        }}
        
        /* Dialog */
        QDialog {{
            background-color: {COLORS.BG_DARK};
        }}
        
        /* Message Box */
        QMessageBox {{
            background-color: {COLORS.BG_CARD};
        }}
        
        QMessageBox QLabel {{
            color: {COLORS.TEXT_PRIMARY};
            font-size: 14px;
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
        }}
        
        /* Frame */
        QFrame {{
            border: none;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {COLORS.BG_CARD};
            color: {COLORS.TEXT_SECONDARY};
            border-top: 1px solid {COLORS.BORDER};
            padding: 8px 16px;
            font-size: 12px;
        }}
    """
