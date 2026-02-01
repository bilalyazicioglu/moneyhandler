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


# Dil Ayarları / Language Settings
def _load_language_setting() -> str:
    """Kaydedilmiş dil ayarını yükler."""
    import json
    settings_path = get_database_path().parent / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get("language", "tr")
        except:
            pass
    return "tr"

CURRENT_LANGUAGE: str = _load_language_setting()

TRANSLATIONS = {
    "tr": {
        # Main Window
        "app_title": "MoneyHandler - Kişisel Finans Yönetimi",
        "tab_dashboard": "Dashboard",
        "tab_accounts": "Hesaplar",
        "tab_transactions": "İşlemler",
        "tab_planned": "Planlanan",
        "tab_weekly": "Haftalık",
        "tab_settings": "Ayarlar",
        "status_accounts": "Hesap",
        "status_transactions": "İşlem",
        "status_planned": "Planlanan",
        
        # Dashboard
        "dashboard_title": "Dashboard",
        "dashboard_subtitle": "Finansal durumunuzun özeti",
        "total_assets": "Toplam Varlık",
        "total_assets_desc": "Tüm hesaplarınızın toplam değeri",
        "total_income": "Toplam Gelir",
        "total_income_desc": "Kayıtlı tüm gelirleriniz",
        "total_expense": "Toplam Gider",
        "total_expense_desc": "Kayıtlı tüm giderleriniz",
        "upcoming_payments": "Yaklaşan",
        "upcoming_days": "gün",
        "recent_transactions": "Son İşlemler",
        
        # Accounts
        "accounts_title": "Hesaplar",
        "accounts_subtitle": "Nakit ve banka hesaplarınızı yönetin",
        "new_account": "Yeni Hesap",
        "account_details": "Hesap Detayları",
        "account_name": "Hesap Adı",
        "account_type": "Hesap Tipi",
        "account_type_cash": "Nakit",
        "account_type_bank": "Banka",
        "balance": "Bakiye",
        "detail": "Detay",
        "description": "Açıklama",
        "transaction_history": "İşlem Geçmişi",
        "transactions_count": "işlem",
        
        # Transactions
        "transactions_title": "İşlemler",
        "transactions_subtitle": "Gelir ve gider işlemlerinizi takip edin",
        "new_transaction": "Yeni İşlem",
        "transaction_details": "İşlem Detayları",
        "filter": "Filtre",
        "all": "Tümü",
        "incomes": "Gelirler",
        "expenses": "Giderler",
        "category": "Kategori",
        "category_search": "Kategori ara...",
        "date": "Tarih",
        "account": "Hesap",
        "transaction_type": "İşlem Tipi",
        "income": "Gelir",
        "expense": "Gider",
        "amount": "Tutar",
        "type": "Tip",
        
        # Planned Items
        "planned_title": "Planlanan İşlemler",
        "planned_subtitle": "Beklenen gelir ve giderlerinizi yönetin",
        "new_planned": "Yeni Planlanan İşlem",
        "planned_details": "Planlanan İşlem Detayları",
        "planned_date": "Planlanan Tarih",
        "expected_income": "Beklenen Gelir",
        "expected_expense": "Beklenen Gider",
        "realize": "Gerçekleştir",
        "realize_info": "Gerçekleştir butonuna tıklayarak planlanan işlemi gerçek bir işleme dönüştürebilirsiniz.",
        "days_left": "gün kaldı",
        "overdue": "Vadesi geçmiş!",
        
        # Weekly View
        "weekly_title": "Haftalık Görünüm",
        "this_week": "Bu hafta",
        "today": "Bugün",
        "daily_avg_expense": "Günlük Ort. Harcama",
        "daily_avg_income": "Günlük Ort. Gelir",
        "weekly_expense": "Haftalık Harcama",
        "weekly_income": "Haftalık Gelir",
        "category_filter": "Kategori Filtresi (Ortalama Hesaplama İçin)",
        "general": "Genel",
        
        # Day names
        "day_monday": "Pazartesi",
        "day_tuesday": "Salı",
        "day_wednesday": "Çarşamba",
        "day_thursday": "Perşembe",
        "day_friday": "Cuma",
        "day_saturday": "Cumartesi",
        "day_sunday": "Pazar",
        "day_mon": "Pzt",
        "day_tue": "Sal",
        "day_wed": "Çar",
        "day_thu": "Per",
        "day_fri": "Cum",
        "day_sat": "Cmt",
        "day_sun": "Paz",
        
        # Common
        "currency": "Para Birimi",
        "save": "Kaydet",
        "cancel": "İptal",
        "delete": "Sil",
        "close": "Kapat",
        "warning": "Uyarı",
        "error": "Hata",
        "success": "Başarılı",
        "confirm": "Onayla",
        "enter_category": "Kategori girin...",
        "enter_description": "Açıklama girin...",
        "optional": "opsiyonel",
        
        # Messages
        "msg_account_empty": "Hesap adı boş olamaz!",
        "msg_create_account_first": "İşlem eklemek için önce bir hesap oluşturmalısınız!",
        "msg_amount_positive": "Tutar 0'dan büyük olmalıdır!",
        "msg_delete_account": "hesabını silmek istediğinize emin misiniz?",
        "msg_delete_account_warning": "Bu işlem geri alınamaz ve hesaba bağlı tüm işlemler de silinecektir!",
        "msg_delete_transaction": "Bu işlemi silmek istediğinize emin misiniz?",
        "msg_delete_transaction_warning": "Bu işlem geri alınamaz ve hesap bakiyesi güncellenecektir!",
        "msg_delete_planned": "Bu planlanan işlemi silmek istediğinize emin misiniz?",
        "msg_realize_confirm": "Bu planlanan işlemi gerçek bir işleme dönüştürmek istediğinize emin misiniz?",
        "msg_realize_info": "Bu işlem hesap bakiyesini güncelleyecek ve planlanan işlemi silecektir.",
        "msg_realize_success": "Planlanan işlem başarıyla gerçekleştirildi!",
        "msg_realize_error": "İşlem gerçekleştirilirken bir hata oluştu.",
        "msg_description_saved": "Açıklama kaydedildi!",
        "msg_save_failed": "Değişiklik kaydedilemedi.",
        
        # Dialog titles
        "dialog_add_account": "Hesap Ekle",
        "dialog_edit_account": "Hesap Düzenle",
        "dialog_add_transaction": "İşlem Ekle",
        "dialog_edit_transaction": "İşlem Düzenle",
        "dialog_add_planned": "Planlanan İşlem Ekle",
        "dialog_edit_planned": "Planlanan İşlem Düzenle",
        "dialog_delete_account": "Hesap Sil",
        "dialog_delete_transaction": "İşlem Sil",
        "dialog_delete_planned": "Planlanan İşlem Sil",
        "dialog_realize": "İşlemi Gerçekleştir",
        
        # Form placeholders
        "placeholder_account_name": "Örn: Nakit Cüzdan, Ziraat Bankası",
        "placeholder_category": "Örn: Maaş, Kira, Market",
        "placeholder_planned_category": "Örn: Maaş, Kira, Fatura",
        "placeholder_description": "İşlem açıklaması (opsiyonel)",
        "placeholder_account_desc": "Hesap açıklaması (opsiyonel)",
        
        # Regular Income
        "regular_income_tab": "Düzenli Gelirler",
        "planned_items_tab": "Planlanan İşlemler",
        "category_salary": "Maaş",
        "category_scholarship": "Burs",
        "category_allowance": "Harçlık",
        "category_rental": "Kira Geliri",
        "category_other_income": "Diğer",
        "expected_day": "Beklenen Gün",
        "avg_delay": "Ort. Gecikme",
        "record_payment": "Ödeme Kaydet",
        "payment_history": "Ödeme Geçmişi",
        "actual_date": "Gerçekleşen Tarih",
        "delay_status": "Gecikme Durumu",
        "days_early": "gün erken",
        "days_late": "gün geç",
        "on_time": "Zamanında",
        "new_regular_income": "Yeni Düzenli Gelir",
        "income_name": "Gelir Adı",
        "day_of_month": "Ayın Günü",
        "this_month_expected": "Bu Ay Beklenen",
        "pending_incomes": "Bekleyen Gelirler",
        "no_pending": "Bekleyen gelir yok",
        "dialog_add_regular_income": "Düzenli Gelir Ekle",
        "dialog_edit_regular_income": "Düzenli Gelir Düzenle",
        "dialog_record_payment": "Ödeme Kaydet",
        "msg_delete_regular_income": "Bu düzenli geliri silmek istediğinize emin misiniz?",
        "payment_recorded": "Ödeme kaydedildi!",
        "regular_income_details": "Düzenli Gelir Detayları",
        "placeholder_income_name": "Örn: İş Maaşı, YKS Bursu",
        "no_payments_yet": "Henüz ödeme kaydı yok",
        
        # Settings
        "settings_title": "Ayarlar",
        "settings_subtitle": "Uygulama tercihlerinizi yönetin",
        "language_settings": "Dil Ayarları",
        "select_language": "Dil Seçin:",
        "language_restart_note": "! Dil değişikliğinin tam olarak uygulanması için uygulamayı yeniden başlatmanız gerekebilir.",
        "about_app": "Uygulama Hakkında",
        "version": "Sürüm",
        "app_description": "MoneyHandler, kişisel finans yönetiminizi kolaylaştıran modern bir masaüstü uygulamasıdır.",
        "language_changed_title": "Dil Değiştirildi",
        "language_changed_message": "Dil ayarı kaydedildi. Değişikliklerin tam olarak uygulanması için uygulamayı yeniden başlatın.",
    },
    "en": {
        # Main Window
        "app_title": "MoneyHandler - Personal Finance Management",
        "tab_dashboard": "Dashboard",
        "tab_accounts": "Accounts",
        "tab_transactions": "Transactions",
        "tab_planned": "Planned",
        "tab_weekly": "Weekly",
        "tab_settings": "Settings",
        "status_accounts": "Account",
        "status_transactions": "Transaction",
        "status_planned": "Planned",
        
        # Dashboard
        "dashboard_title": "Dashboard",
        "dashboard_subtitle": "Summary of your financial status",
        "total_assets": "Total Assets",
        "total_assets_desc": "Total value of all your accounts",
        "total_income": "Total Income",
        "total_income_desc": "All your recorded income",
        "total_expense": "Total Expense",
        "total_expense_desc": "All your recorded expenses",
        "upcoming_payments": "Upcoming",
        "upcoming_days": "days",
        "recent_transactions": "Recent Transactions",
        
        # Accounts
        "accounts_title": "Accounts",
        "accounts_subtitle": "Manage your cash and bank accounts",
        "new_account": "New Account",
        "account_details": "Account Details",
        "account_name": "Account Name",
        "account_type": "Account Type",
        "account_type_cash": "Cash",
        "account_type_bank": "Bank",
        "balance": "Balance",
        "detail": "Detail",
        "description": "Description",
        "transaction_history": "Transaction History",
        "transactions_count": "transactions",
        
        # Transactions
        "transactions_title": "Transactions",
        "transactions_subtitle": "Track your income and expenses",
        "new_transaction": "New Transaction",
        "transaction_details": "Transaction Details",
        "filter": "Filter",
        "all": "All",
        "incomes": "Incomes",
        "expenses": "Expenses",
        "category": "Category",
        "category_search": "Search category...",
        "date": "Date",
        "account": "Account",
        "transaction_type": "Transaction Type",
        "income": "Income",
        "expense": "Expense",
        "amount": "Amount",
        "type": "Type",
        
        # Planned Items
        "planned_title": "Planned Transactions",
        "planned_subtitle": "Manage your expected income and expenses",
        "new_planned": "New Planned Transaction",
        "planned_details": "Planned Transaction Details",
        "planned_date": "Planned Date",
        "expected_income": "Expected Income",
        "expected_expense": "Expected Expense",
        "realize": "Realize",
        "realize_info": "Click the Realize button to convert a planned transaction into an actual transaction.",
        "days_left": "days left",
        "overdue": "Overdue!",
        
        # Weekly View
        "weekly_title": "Weekly View",
        "this_week": "This week",
        "today": "Today",
        "daily_avg_expense": "Daily Avg. Expense",
        "daily_avg_income": "Daily Avg. Income",
        "weekly_expense": "Weekly Expense",
        "weekly_income": "Weekly Income",
        "category_filter": "Category Filter (For Average Calculation)",
        "general": "General",
        
        # Day names
        "day_monday": "Monday",
        "day_tuesday": "Tuesday",
        "day_wednesday": "Wednesday",
        "day_thursday": "Thursday",
        "day_friday": "Friday",
        "day_saturday": "Saturday",
        "day_sunday": "Sunday",
        "day_mon": "Mon",
        "day_tue": "Tue",
        "day_wed": "Wed",
        "day_thu": "Thu",
        "day_fri": "Fri",
        "day_sat": "Sat",
        "day_sun": "Sun",
        
        # Common
        "currency": "Currency",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "close": "Close",
        "warning": "Warning",
        "error": "Error",
        "success": "Success",
        "confirm": "Confirm",
        "enter_category": "Enter category...",
        "enter_description": "Enter description...",
        "optional": "optional",
        
        # Messages
        "msg_account_empty": "Account name cannot be empty!",
        "msg_create_account_first": "You must create an account first to add a transaction!",
        "msg_amount_positive": "Amount must be greater than 0!",
        "msg_delete_account": "Are you sure you want to delete this account?",
        "msg_delete_account_warning": "This action cannot be undone and all transactions linked to this account will be deleted!",
        "msg_delete_transaction": "Are you sure you want to delete this transaction?",
        "msg_delete_transaction_warning": "This action cannot be undone and the account balance will be updated!",
        "msg_delete_planned": "Are you sure you want to delete this planned transaction?",
        "msg_realize_confirm": "Are you sure you want to convert this planned transaction into an actual transaction?",
        "msg_realize_info": "This will update the account balance and delete the planned transaction.",
        "msg_realize_success": "Planned transaction has been successfully realized!",
        "msg_realize_error": "An error occurred while realizing the transaction.",
        "msg_description_saved": "Description saved!",
        "msg_save_failed": "Failed to save changes.",
        
        # Dialog titles
        "dialog_add_account": "Add Account",
        "dialog_edit_account": "Edit Account",
        "dialog_add_transaction": "Add Transaction",
        "dialog_edit_transaction": "Edit Transaction",
        "dialog_add_planned": "Add Planned Transaction",
        "dialog_edit_planned": "Edit Planned Transaction",
        "dialog_delete_account": "Delete Account",
        "dialog_delete_transaction": "Delete Transaction",
        "dialog_delete_planned": "Delete Planned Transaction",
        "dialog_realize": "Realize Transaction",
        
        # Form placeholders
        "placeholder_account_name": "E.g.: Cash Wallet, Bank Account",
        "placeholder_category": "E.g.: Salary, Rent, Groceries",
        "placeholder_planned_category": "E.g.: Salary, Rent, Bills",
        "placeholder_description": "Transaction description (optional)",
        "placeholder_account_desc": "Account description (optional)",
        
        # Regular Income
        "regular_income_tab": "Regular Income",
        "planned_items_tab": "Planned Items",
        "category_salary": "Salary",
        "category_scholarship": "Scholarship",
        "category_allowance": "Allowance",
        "category_rental": "Rental Income",
        "category_other_income": "Other",
        "expected_day": "Expected Day",
        "avg_delay": "Avg. Delay",
        "record_payment": "Record Payment",
        "payment_history": "Payment History",
        "actual_date": "Actual Date",
        "delay_status": "Delay Status",
        "days_early": "days early",
        "days_late": "days late",
        "on_time": "On Time",
        "new_regular_income": "New Regular Income",
        "income_name": "Income Name",
        "day_of_month": "Day of Month",
        "this_month_expected": "Expected This Month",
        "pending_incomes": "Pending Incomes",
        "no_pending": "No pending income",
        "dialog_add_regular_income": "Add Regular Income",
        "dialog_edit_regular_income": "Edit Regular Income",
        "dialog_record_payment": "Record Payment",
        "msg_delete_regular_income": "Are you sure you want to delete this regular income?",
        "payment_recorded": "Payment recorded!",
        "regular_income_details": "Regular Income Details",
        "placeholder_income_name": "E.g.: Work Salary, Scholarship",
        "no_payments_yet": "No payment records yet",
        
        # Settings
        "settings_title": "Settings",
        "settings_subtitle": "Manage your application preferences",
        "language_settings": "Language Settings",
        "select_language": "Select Language:",
        "language_restart_note": "! You may need to restart the application for language changes to take full effect.",
        "about_app": "About Application",
        "version": "Version",
        "app_description": "MoneyHandler is a modern desktop application that simplifies your personal finance management.",
        "language_changed_title": "Language Changed",
        "language_changed_message": "Language setting saved. Restart the application for changes to take full effect.",
    }
}


def t(key: str) -> str:
    """
    Get translated string for the given key.
    
    Args:
        key: Translation key
        
    Returns:
        Translated string or key if not found
    """
    lang = TRANSLATIONS.get(CURRENT_LANGUAGE, TRANSLATIONS["tr"])
    return lang.get(key, key)


def get_day_names() -> list:
    """Get translated day names (full)."""
    return [
        t("day_monday"), t("day_tuesday"), t("day_wednesday"),
        t("day_thursday"), t("day_friday"), t("day_saturday"), t("day_sunday")
    ]


def get_day_names_short() -> list:
    """Get translated day names (short)."""
    return [
        t("day_mon"), t("day_tue"), t("day_wed"),
        t("day_thu"), t("day_fri"), t("day_sat"), t("day_sun")
    ]
