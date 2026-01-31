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

from config import COLORS, CURRENCIES, t
from models.planned_item import PlannedItem, PlannedItemRepository
from models.transaction import TransactionRepository
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
    
    SORT_NONE = 0
    SORT_ASC = 1
    SORT_DESC = 2
    
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
        self._sort_column = None
        self._sort_order = self.SORT_NONE
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel(t("planned_title"))
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel(t("planned_subtitle"))
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        self.add_btn = QPushButton(t("new_planned"))
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
        
        info_card = QLabel(t("realize_info"))
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
            "ID", t("date"), t("account"), t("type"), t("category"), t("description"), t("amount")
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
        self.table.setSortingEnabled(False)
        
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self._on_header_clicked)
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
        
        self.detail_title = QLabel(t("planned_details"))
        self.detail_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS.TEXT_PRIMARY};
            border: none;
        """)
        layout.addWidget(self.detail_title)
        
        date_label = QLabel(t("planned_date"))
        date_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(date_label)
        
        self.detail_date = QDateEdit()
        self.detail_date.setCalendarPopup(True)
        self.detail_date.setDate(QDate.currentDate())
        layout.addWidget(self.detail_date)
        
        account_label = QLabel(t("account"))
        account_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(account_label)
        
        self.detail_account = QComboBox()
        layout.addWidget(self.detail_account)
        
        type_label = QLabel(t("transaction_type"))
        type_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(type_label)
        
        self.detail_type = QComboBox()
        self.detail_type.addItem(t("income"), "income")
        self.detail_type.addItem(t("expense"), "expense")
        layout.addWidget(self.detail_type)
        
        category_label = QLabel(t("category"))
        category_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(category_label)
        
        self.detail_category = QLineEdit()
        self.detail_category.setPlaceholderText(t("enter_category"))
        layout.addWidget(self.detail_category)
        
        amount_label = QLabel(t("amount"))
        amount_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(amount_label)
        
        self.detail_amount = QDoubleSpinBox()
        self.detail_amount.setRange(0, 999999999)
        self.detail_amount.setDecimals(2)
        self.detail_amount.setPrefix("₺ ")
        layout.addWidget(self.detail_amount)
        
        desc_label = QLabel(t("description"))
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(desc_label)
        
        self.detail_description = QLineEdit()
        self.detail_description.setPlaceholderText(t("enter_description"))
        layout.addWidget(self.detail_description)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        self.realize_detail_btn = QPushButton(t("realize"))
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
        
        self.save_btn = QPushButton(t("save"))
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
        
        self.delete_btn = QPushButton(t("delete"))
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
            self.detail_title.setText(t("planned_details"))
    
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
    
    def _on_header_clicked(self, logical_index: int) -> None:
        """
        Sütun başlığına tıklandığında sıralama yapar.
        
        Args:
            logical_index: Tıklanan sütun indeksi
        """
        if logical_index == 0:
            return
        
        if self._sort_column == logical_index:
            if self._sort_order == self.SORT_NONE:
                self._sort_order = self.SORT_ASC
            elif self._sort_order == self.SORT_ASC:
                self._sort_order = self.SORT_DESC
            else:
                self._sort_order = self.SORT_NONE
        else:
            self._sort_column = logical_index
            self._sort_order = self.SORT_ASC
        
        self._update_header_indicators()
        self.refresh()
    
    def _update_header_indicators(self) -> None:
        """Sütun başlıklarındaki sıralama göstergelerini günceller."""
        column_names = ["ID", t("date"), t("account"), t("type"), t("category"), t("description"), t("amount")]
        
        for i, name in enumerate(column_names):
            if i == self._sort_column:
                if self._sort_order == self.SORT_ASC:
                    self.table.horizontalHeaderItem(i).setText(f"{name} ▲")
                elif self._sort_order == self.SORT_DESC:
                    self.table.horizontalHeaderItem(i).setText(f"{name} ▼")
                else:
                    self.table.horizontalHeaderItem(i).setText(name)
            else:
                self.table.horizontalHeaderItem(i).setText(name)
    
    def _sort_planned_items(self, items: list) -> list:
        """
        Planlanan işlemleri mevcut sıralama durumuna göre sıralar.
        
        Args:
            items: Sıralanacak planlanan işlemler listesi
            
        Returns:
            Sıralanmış planlanan işlemler listesi
        """
        if self._sort_order == self.SORT_NONE or self._sort_column is None:
            return items
        
        accounts = {a.id: a for a in self.controller.get_all_accounts()}
        reverse = self._sort_order == self.SORT_DESC
        
        def get_sort_key(item):
            if self._sort_column == 1:
                return item.planned_date
            elif self._sort_column == 2:
                account = accounts.get(item.account_id)
                return (account.name if account else "").lower()
            elif self._sort_column == 3:
                return 0 if item.is_income else 1
            elif self._sort_column == 4:
                return (item.category or "").lower()
            elif self._sort_column == 5:
                return (item.description or "").lower()
            elif self._sort_column == 6:
                return item.amount if item.is_income else -item.amount
            return 0
        
        return sorted(items, key=get_sort_key, reverse=reverse)
    
    def refresh(self) -> None:
        """Planlanan işlem listesini yeniler."""
        planned_items = self.controller.get_all_planned_items()
        planned_items = self._sort_planned_items(list(planned_items))
        accounts = {a.id: a for a in self.controller.get_all_accounts()}
        
        self.table.setRowCount(len(planned_items))
        
        for row, item in enumerate(planned_items):
            id_item = QTableWidgetItem(str(item.id))
            self.table.setItem(row, 0, id_item)
            
            date_str = item.planned_date.strftime("%d.%m.%Y")
            date_item = QTableWidgetItem(date_str)
            
            if item.is_overdue:
                date_item.setForeground(QColor(COLORS.DANGER))
                date_item.setToolTip(t("overdue"))
            elif item.days_until <= 7:
                date_item.setForeground(QColor(COLORS.WARNING))
                date_item.setToolTip(f"{item.days_until} {t('days_left')}")
            
            self.table.setItem(row, 1, date_item)
            
            account = accounts.get(item.account_id)
            account_name = account.name if account else "-"
            self.table.setItem(row, 2, QTableWidgetItem(account_name))
            
            if item.is_income:
                type_text = t("income")
                color = COLORS.SUCCESS
            else:
                type_text = t("expense")
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
                t("warning"),
                t("msg_create_account_first")
            )
            return
        
        trans_categories = TransactionRepository().get_distinct_categories()
        planned_categories = PlannedItemRepository().get_distinct_categories()
        all_categories = sorted(set(trans_categories + planned_categories))
        
        dialog = PlannedItemDialog(self, accounts=accounts, categories=all_categories)
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
        trans_categories = TransactionRepository().get_distinct_categories()
        planned_categories = PlannedItemRepository().get_distinct_categories()
        all_categories = sorted(set(trans_categories + planned_categories))
        
        dialog = PlannedItemDialog(self, item, accounts, all_categories)
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
            t("dialog_delete_planned"),
            t("msg_delete_planned"),
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
            t("dialog_realize"),
            f"{t('msg_realize_confirm')}\n\n"
            f"{t('amount')}: {CURRENCIES[item.currency].symbol}{item.amount:,.2f}\n"
            f"{t('type')}: {t('income') if item.is_income else t('expense')}\n\n"
            f"{t('msg_realize_info')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.controller.realize_planned_item(item)
            if success:
                QMessageBox.information(
                    self,
                    t("success"),
                    t("msg_realize_success")
                )
                self.refresh()
                self.item_realized.emit()
            else:
                QMessageBox.warning(
                    self,
                    t("error"),
                    t("msg_realize_error")
                )
