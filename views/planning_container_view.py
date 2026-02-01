"""
Planlamalar Container View Modülü

Planlanan İşlemler ve Düzenli Gelirler sekmelerini içeren container widget.
"""

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget
)

from config import COLORS, t
from views.planned_items_view import PlannedItemsView
from views.regular_income_view import RegularIncomeView

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class PlanningContainerView(QWidget):
    """
    Planlama sekmelerini içeren container widget.
    
    Sekmeler:
    - Planlanan İşlemler (PlannedItemsView)
    - Düzenli Gelirler (RegularIncomeView)
    
    Signals:
        data_changed: Herhangi bir veri değiştiğinde
    """
    
    data_changed = pyqtSignal()
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        """
        PlanningContainerView başlatıcısı.
        
        Args:
            controller: Ana controller referansı
            parent: Üst widget
        """
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.inner_tabs = QTabWidget()
        self.inner_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {COLORS.BG_DARK};
            }}
            QTabBar {{
                background-color: {COLORS.BG_ELEVATED};
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {COLORS.TEXT_SECONDARY};
                padding: 12px 24px;
                margin: 0px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                color: {COLORS.TEXT_PRIMARY};
                border-bottom: 2px solid {COLORS.SUCCESS};
                background-color: transparent;
            }}
            QTabBar::tab:hover:!selected {{
                color: {COLORS.TEXT_PRIMARY};
                background-color: rgba(16, 185, 129, 0.1);
            }}
        """)
        
        self.planned_items_view = PlannedItemsView(self.controller)
        self.inner_tabs.addTab(self.planned_items_view, t("planned_items_tab"))
        
        self.regular_income_view = RegularIncomeView(self.controller)
        self.inner_tabs.addTab(self.regular_income_view, t("regular_income_tab"))
        
        layout.addWidget(self.inner_tabs)
    
    def _connect_signals(self) -> None:
        """Signal/slot bağlantılarını kurar."""
        self.planned_items_view.planned_item_changed.connect(self._on_data_changed)
        self.planned_items_view.item_realized.connect(self._on_data_changed)
        self.regular_income_view.income_changed.connect(self._on_data_changed)
        self.regular_income_view.payment_recorded.connect(self._on_data_changed)
    
    def _on_data_changed(self) -> None:
        """Veri değiştiğinde çağrılır."""
        self.data_changed.emit()
    
    def refresh(self) -> None:
        """İç sekmeleri yeniler."""
        self.planned_items_view.refresh()
        self.regular_income_view.refresh()
    
    @property
    def planned_item_changed(self):
        """PlannedItemsView'un planned_item_changed sinyaline erişim."""
        return self.planned_items_view.planned_item_changed
    
    @property
    def item_realized(self):
        """PlannedItemsView'un item_realized sinyaline erişim."""
        return self.planned_items_view.item_realized
