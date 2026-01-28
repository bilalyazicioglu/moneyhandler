"""
Planlanan İşlemler View Modülü

Beklenen/Planlanan işlemler listesi ekranı widget'ı.
Planlanan işlem listesi, ekleme, düzenleme, silme ve gerçekleştirme işlemleri.
"""

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QSplitter,
    QFrame,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QDateEdit
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QDate

from config import COLORS, CURRENCIES
from models.planned_item import PlannedItem
from views.forms import PlannedItemDialog

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class PlannedItemsView(QWidget):
    """
    Planlanan işlem yönetimi ekranı widget'ı.
    
    Signals:
        planned_item_changed: Planlanan işlem değiştiğinde
        item_realized: Planlanan işlem gerçekleştirildiğinde
    """
    
    planned_item_changed = pyqtSignal()
    item_realized = pyqtSignal()
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        """
        PlannedItemsView başlatıcısı.
        
        Args:
            controller: Ana controller referansı
            parent: Üst widget
        """
        super().__init__(parent)
        self.controller = controller
        self._selected_item = None
        self._accounts = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("Planlanan İşlemler")
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Beklenen gelir ve giderlerinizi yönetin")
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        self.add_btn = QPushButton("Yeni Planlanan İşlem")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                padding: 12px 28px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_LIGHT};
            }}
        """)
        self.add_btn.clicked.connect(self._on_add_planned_item)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        info_card = QLabel(
            "Gerçekleştir butonuna tıklayarak planlanan işlemi gerçek bir işleme dönüştürebilirsiniz."
        )
        info_card.setStyleSheet(f"""
            color: {COLORS.TEXT_SECONDARY};
            padding: 16px 20px;
            background-color: {COLORS.BG_CARD};
            border: 1px solid {COLORS.BORDER};
            border-left: 4px solid {COLORS.INFO};
            border-radius: 8px;
            font-size: 13px;
        """)
        layout.addWidget(info_card)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Hesap", "Tip", "Kategori", "Açıklama", "Tutar"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(6, 140)
        
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        splitter.addWidget(self.table)
        
        self.detail_panel = self._create_detail_panel()
        splitter.addWidget(self.detail_panel)
        
        splitter.setSizes([550, 350])
        layout.addWidget(splitter)
    
    def _create_detail_panel(self) -> QFrame:
        """Detay panelini oluşturur."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.BG_CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.detail_title = QLabel("Planlanan İşlem Detayları")
        self.detail_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS.TEXT_PRIMARY};
            border: none;
        """)
        layout.addWidget(self.detail_title)
        
        date_label = QLabel("Planlanan Tarih")
        date_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(date_label)
        
        self.detail_date = QDateEdit()
        self.detail_date.setCalendarPopup(True)
        self.detail_date.setDate(QDate.currentDate())
        layout.addWidget(self.detail_date)
        
        account_label = QLabel("Hesap")
        account_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(account_label)
        
        self.detail_account = QComboBox()
        layout.addWidget(self.detail_account)
        
        type_label = QLabel("İşlem Tipi")
        type_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(type_label)
        
        self.detail_type = QComboBox()
        self.detail_type.addItem("Gelir", "income")
        self.detail_type.addItem("Gider", "expense")
        layout.addWidget(self.detail_type)
        
        category_label = QLabel("Kategori")
        category_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(category_label)
        
        self.detail_category = QLineEdit()
        self.detail_category.setPlaceholderText("Kategori girin...")
        layout.addWidget(self.detail_category)
        
        amount_label = QLabel("Tutar")
        amount_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(amount_label)
        
        self.detail_amount = QDoubleSpinBox()
        self.detail_amount.setRange(0, 999999999)
        self.detail_amount.setDecimals(2)
        self.detail_amount.setPrefix("₺ ")
        layout.addWidget(self.detail_amount)
        
        desc_label = QLabel("Açıklama")
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(desc_label)
        
        self.detail_description = QLineEdit()
        self.detail_description.setPlaceholderText("Açıklama girin...")
        layout.addWidget(self.detail_description)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        self.realize_detail_btn = QPushButton("Gerçekleştir")
        self.realize_detail_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        self.realize_detail_btn.clicked.connect(self._on_realize_selected)
        btn_layout.addWidget(self.realize_detail_btn)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_LIGHT};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save_detail)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("Sil")
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.DANGER};
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.DANGER_LIGHT};
            }}
        """)
        self.delete_btn.clicked.connect(self._on_delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        layout.addLayout(btn_layout)
        
        self._set_detail_enabled(False)
        
        return panel
    
    def _set_detail_enabled(self, enabled: bool) -> None:
        """Detay panelini etkinleştirir/devre dışı bırakır."""
        self.detail_date.setEnabled(enabled)
        self.detail_account.setEnabled(enabled)
        self.detail_type.setEnabled(enabled)
        self.detail_category.setEnabled(enabled)
        self.detail_amount.setEnabled(enabled)
        self.detail_description.setEnabled(enabled)
        self.realize_detail_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        
        if not enabled:
            self.detail_category.clear()
            self.detail_description.clear()
            self.detail_amount.setValue(0)
            self.detail_title.setText("Planlanan İşlem Detayları")
    
    def _on_selection_changed(self) -> None:
        """Tablo seçimi değiştiğinde çağrılır."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_item = None
            self._set_detail_enabled(False)
            return
        
        row = selected_rows[0].row()
        item_id = int(self.table.item(row, 0).text())
        
        all_items = self.controller.get_all_planned_items()
        self._selected_item = next((i for i in all_items if i.id == item_id), None)
        
        if self._selected_item:
            self._load_detail(self._selected_item)
            self._set_detail_enabled(True)
    
    def _load_detail(self, item: PlannedItem) -> None:
        """Planlanan işlem detaylarını panele yükler."""
        self.detail_title.setText(f"{item.category or 'Planlanan'}")
        
        self.detail_date.setDate(QDate(item.planned_date.year, item.planned_date.month, item.planned_date.day))
        
        self.detail_account.clear()
        self._accounts = self.controller.get_all_accounts()
        for acc in self._accounts:
            self.detail_account.addItem(acc.name, acc.id)
        
        acc_index = self.detail_account.findData(item.account_id)
        if acc_index >= 0:
            self.detail_account.setCurrentIndex(acc_index)
        
        type_index = self.detail_type.findData(item.transaction_type)
        if type_index >= 0:
            self.detail_type.setCurrentIndex(type_index)
        
        self.detail_category.setText(item.category or "")
        self.detail_amount.setValue(item.amount)
        self.detail_description.setText(item.description or "")
    
    def _on_save_detail(self) -> None:
        """Detay panelinden planlanan işlemi kaydeder."""
        if not self._selected_item:
            return
        
        qdate = self.detail_date.date()
        from datetime import date as dt_date
        
        self._selected_item.planned_date = dt_date(qdate.year(), qdate.month(), qdate.day())
        self._selected_item.account_id = self.detail_account.currentData()
        self._selected_item.transaction_type = self.detail_type.currentData()
        self._selected_item.category = self.detail_category.text().strip()
        self._selected_item.amount = self.detail_amount.value()
        self._selected_item.description = self.detail_description.text().strip()
        
        self.controller.update_planned_item(self._selected_item)
        self.refresh()
        self.planned_item_changed.emit()
    
    def _on_delete_selected(self) -> None:
        """Seçili planlanan işlemi siler."""
        if self._selected_item:
            self._on_delete_planned_item(self._selected_item)
    
    def _on_realize_selected(self) -> None:
        """Seçili planlanan işlemi gerçekleştirir."""
        if self._selected_item:
            self._on_realize_item(self._selected_item)
    
    def refresh(self) -> None:
        """Planlanan işlem listesini yeniler."""
        planned_items = self.controller.get_all_planned_items()
        accounts = {a.id: a for a in self.controller.get_all_accounts()}
        
        self.table.setRowCount(len(planned_items))
        
        for row, item in enumerate(planned_items):
            id_item = QTableWidgetItem(str(item.id))
            self.table.setItem(row, 0, id_item)
            
            date_str = item.planned_date.strftime("%d.%m.%Y")
            date_item = QTableWidgetItem(date_str)
            
            if item.is_overdue:
                date_item.setForeground(QColor(COLORS.DANGER))
                date_item.setToolTip("Vadesi geçmiş!")
            elif item.days_until <= 7:
                date_item.setForeground(QColor(COLORS.WARNING))
                date_item.setToolTip(f"{item.days_until} gün kaldı")
            
            self.table.setItem(row, 1, date_item)
            
            account = accounts.get(item.account_id)
            account_name = account.name if account else "-"
            self.table.setItem(row, 2, QTableWidgetItem(account_name))
            
            if item.is_income:
                type_text = "Gelir"
                color = COLORS.SUCCESS
            else:
                type_text = "Gider"
                color = COLORS.DANGER
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor(color))
            self.table.setItem(row, 3, type_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(item.category or "-"))
            
            self.table.setItem(row, 5, QTableWidgetItem(item.description or "-"))
            
            symbol = CURRENCIES[item.currency].symbol
            amount_text = f"{symbol}{item.amount:,.2f}"
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setForeground(QColor(color))
            self.table.setItem(row, 6, amount_item)
    
    def _on_add_planned_item(self) -> None:
        """Yeni planlanan işlem ekleme."""
        accounts = self.controller.get_all_accounts()
        if not accounts:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Planlanan işlem eklemek için önce bir hesap oluşturmalısınız!"
            )
            return
        
        dialog = PlannedItemDialog(self, accounts=accounts)
        if dialog.exec():
            planned_item = dialog.get_data()
            self.controller.create_planned_item(planned_item)
            self.refresh()
            self.planned_item_changed.emit()
    
    def _on_edit_planned_item(self, item: PlannedItem) -> None:
        """
        Planlanan işlem düzenleme.
        
        Args:
            item: Düzenlenecek planlanan işlem
        """
        accounts = self.controller.get_all_accounts()
        dialog = PlannedItemDialog(self, item, accounts)
        if dialog.exec():
            updated_item = dialog.get_data()
            self.controller.update_planned_item(updated_item)
            self.refresh()
            self.planned_item_changed.emit()
    
    def _on_delete_planned_item(self, item: PlannedItem) -> None:
        """
        Planlanan işlem silme.
        
        Args:
            item: Silinecek planlanan işlem
        """
        reply = QMessageBox.question(
            self,
            "Planlanan İşlem Sil",
            "Bu planlanan işlemi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_planned_item(item.id)
            self.refresh()
            self.planned_item_changed.emit()
    
    def _on_realize_item(self, item: PlannedItem) -> None:
        """
        Planlanan işlemi gerçek işleme dönüştürür.
        
        Args:
            item: Gerçekleştirilecek planlanan işlem
        """
        reply = QMessageBox.question(
            self,
            "İşlemi Gerçekleştir",
            f"Bu planlanan işlemi gerçek bir işleme dönüştürmek istediğinize emin misiniz?\n\n"
            f"Tutar: {CURRENCIES[item.currency].symbol}{item.amount:,.2f}\n"
            f"Tip: {'Gelir' if item.is_income else 'Gider'}\n\n"
            f"Bu işlem hesap bakiyesini güncelleyecek ve planlanan işlemi silecektir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.controller.realize_planned_item(item)
            if success:
                QMessageBox.information(
                    self,
                    "Başarılı",
                    "Planlanan işlem başarıyla gerçekleştirildi!"
                )
                self.refresh()
                self.item_realized.emit()
            else:
                QMessageBox.warning(
                    self,
                    "Hata",
                    "İşlem gerçekleştirilirken bir hata oluştu."
                )
