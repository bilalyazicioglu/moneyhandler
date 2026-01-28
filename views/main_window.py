"""
Ana Pencere Modülü

Uygulamanın ana penceresi ve sekme yapısı.
Tüm view'ları bir arada tutar ve navigasyonu yönetir.
"""

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar
)

from config import (
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    get_stylesheet,
    COLORS
)
from views.dashboard_view import DashboardView
from views.accounts_view import AccountsView
from views.transactions_view import TransactionsView
from views.planned_items_view import PlannedItemsView

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
        self.setWindowTitle("Kişisel Finans Yönetimi")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1200, 800)
        
        # Stil uygula
        self.setStyleSheet(get_stylesheet())
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        # Merkezi widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sekme widget'ı
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # Dashboard sekmesi
        self.dashboard_view = DashboardView(self.controller)
        self.tab_widget.addTab(self.dashboard_view, "Dashboard")
        
        # Hesaplar sekmesi
        self.accounts_view = AccountsView(self.controller)
        self.tab_widget.addTab(self.accounts_view, "Hesaplar")
        
        # İşlemler sekmesi
        self.transactions_view = TransactionsView(self.controller)
        self.tab_widget.addTab(self.transactions_view, "İşlemler")
        
        # Planlanan İşlemler sekmesi
        self.planned_items_view = PlannedItemsView(self.controller)
        self.tab_widget.addTab(self.planned_items_view, "Planlanan")
        
        layout.addWidget(self.tab_widget)
        
        # Durum çubuğu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()
    
    def _connect_signals(self) -> None:
        """Signal/slot bağlantılarını kurar."""
        # Sekme değişikliği
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Hesap değişiklikleri
        self.accounts_view.account_changed.connect(self._on_data_changed)
        
        # İşlem değişiklikleri
        self.transactions_view.transaction_changed.connect(self._on_data_changed)
        
        # Planlanan işlem değişiklikleri
        self.planned_items_view.planned_item_changed.connect(self._on_data_changed)
        self.planned_items_view.item_realized.connect(self._on_data_changed)
    
    def _on_tab_changed(self, index: int) -> None:
        """
        Sekme değiştiğinde çağrılır.
        
        Args:
            index: Yeni sekme indeksi
        """
        # İlgili view'ı yenile
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
        self.planned_items_view.refresh()
    
    def _update_status_bar(self) -> None:
        """Durum çubuğunu günceller."""
        accounts_count = len(self.controller.get_all_accounts())
        transactions_count = len(self.controller.get_all_transactions())
        planned_count = len(self.controller.get_all_planned_items())
        
        self.status_bar.showMessage(
            f"{accounts_count} Hesap  |  "
            f"{transactions_count} İşlem  |  "
            f"{planned_count} Planlanan"
        )
