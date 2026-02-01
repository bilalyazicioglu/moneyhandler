"""
Ana Pencere Modülü

Uygulamanın ana penceresi ve sekme yapısı.
Tüm view'ları bir arada tutar ve navigasyonu yönetir.
"""

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar
)

from config import (
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    get_stylesheet,
    COLORS,
    t
)
from views.dashboard_view import DashboardView
from views.accounts_view import AccountsView
from views.transactions_view import TransactionsView
from views.planning_container_view import PlanningContainerView
from views.weekly_spending_view import WeeklySpendingView
from views.settings_view import SettingsView

import sys
import os

def resource_path(relative_path: str) -> str:
    """PyInstaller için kaynak dosya yolunu döndürür."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class MainWindow(QMainWindow):
    """
    Ana uygulama penceresi.
    
    Sekme yapısı ile Dashboard, Hesaplar, İşlemler ve 
    Planlanan İşlemler ekranlarını barındırır.
    """
    
    def __init__(self, controller: 'MainController') -> None:
        """
        MainWindow başlatıcısı.
        
        Args:
            controller: Ana controller referansı
        """
        super().__init__()
        self.controller = controller
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._refresh_all()
    
    def _setup_window(self) -> None:
        """Pencere ayarlarını yapılandırır."""
        self.setWindowTitle(t("app_title"))
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        screen = QApplication.primaryScreen()
        if screen:
            available_geometry = screen.availableGeometry()
            self.setGeometry(available_geometry)
        
        icon_path = resource_path("assets/icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet(get_stylesheet())
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS.BG_CARD}; border-bottom: 1px solid {COLORS.BORDER};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        logo_label = QLabel()
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        app_name = QLabel("MoneyHandler")
        app_name.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            margin-left: 12px;
        """)
        header_layout.addWidget(app_name)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        self.dashboard_view = DashboardView(self.controller)
        self.tab_widget.addTab(self.dashboard_view, t("tab_dashboard"))
        
        self.accounts_view = AccountsView(self.controller)
        self.tab_widget.addTab(self.accounts_view, t("tab_accounts"))
        
        self.transactions_view = TransactionsView(self.controller)
        self.tab_widget.addTab(self.transactions_view, t("tab_transactions"))
        
        self.planning_view = PlanningContainerView(self.controller)
        self.tab_widget.addTab(self.planning_view, t("tab_planned"))
        
        self.weekly_spending_view = WeeklySpendingView(self.controller)
        self.tab_widget.addTab(self.weekly_spending_view, t("tab_weekly"))
        
        self.settings_view = SettingsView(self.controller)
        self.tab_widget.addTab(self.settings_view, t("tab_settings"))
        
        layout.addWidget(self.tab_widget)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()
    
    def _connect_signals(self) -> None:
        """Signal/slot bağlantılarını kurar."""
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        self.accounts_view.account_changed.connect(self._on_data_changed)
        
        self.transactions_view.transaction_changed.connect(self._on_data_changed)
        
        self.planning_view.planned_item_changed.connect(self._on_data_changed)
        self.planning_view.item_realized.connect(self._on_data_changed)
        self.planning_view.data_changed.connect(self._on_data_changed)
    
    def _on_tab_changed(self, index: int) -> None:
        """
        Sekme değiştiğinde çağrılır.
        
        Args:
            index: Yeni sekme indeksi
        """
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
    
    def _on_data_changed(self) -> None:
        """Veri değiştiğinde çağrılır."""
        self._refresh_all()
        self._update_status_bar()
    
    def _refresh_all(self) -> None:
        """Tüm view'ları yeniler."""
        self.dashboard_view.refresh()
        self.accounts_view.refresh()
        self.transactions_view.refresh()
        self.planning_view.refresh()
        self.weekly_spending_view.refresh()
    
    def _update_status_bar(self) -> None:
        """Durum çubuğunu günceller."""
        accounts_count = len(self.controller.get_all_accounts())
        transactions_count = len(self.controller.get_all_transactions())
        planned_count = len(self.controller.get_all_planned_items())
        
        self.status_bar.showMessage(
            f"{accounts_count} {t('status_accounts')}  |  "
            f"{transactions_count} {t('status_transactions')}  |  "
            f"{planned_count} {t('status_planned')}"
        )
