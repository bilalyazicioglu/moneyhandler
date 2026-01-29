"""
İşlemler View Modülü

Gelir/Gider işlemleri listesi ekranı widget'ı.
İşlem listesi, ekleme, düzenleme ve silme işlemleri.
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
    QComboBox,
    QSplitter,
    QFrame,
    QLineEdit,
    QDoubleSpinBox,
    QDateEdit
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QDate

from config import COLORS, CURRENCIES, TransactionType
from models.transaction import Transaction
from views.forms import TransactionDialog

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class TransactionsView(QWidget):
    """
    İşlem yönetimi ekranı widget'ı.
    
    Signals:
        transaction_changed: İşlem eklendiğinde/güncellendiğinde/silindiğinde
    """
    
    transaction_changed = pyqtSignal()
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        """
        TransactionsView başlatıcısı.
        
        Args:
            controller: Ana controller referansı
            parent: Üst widget
        """
        super().__init__(parent)
        self.controller = controller
        self._selected_transaction = None
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
        
        title = QLabel("İşlemler")
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Gelir ve gider işlemlerinizi takip edin")
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        filter_label = QLabel("Filtre:")
        filter_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; margin-right: 8px;")
        header_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(140)
        self.filter_combo.addItem("Tümü", "all")
        self.filter_combo.addItem("Gelirler", TransactionType.INCOME)
        self.filter_combo.addItem("Giderler", TransactionType.EXPENSE)
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        header_layout.addWidget(self.filter_combo)
        
        header_layout.addSpacing(12)
        
        search_label = QLabel("Kategori:")
        search_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; margin-right: 8px;")
        header_layout.addWidget(search_label)
        
        self.category_search = QLineEdit()
        self.category_search.setMinimumWidth(160)
        self.category_search.setPlaceholderText("Kategori ara...")
        self.category_search.textChanged.connect(self.refresh)
        header_layout.addWidget(self.category_search)
        
        header_layout.addSpacing(16)
        
        self.add_btn = QPushButton("Yeni İşlem")
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
        self.add_btn.clicked.connect(self._on_add_transaction)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
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
        
        splitter.setSizes([600, 350])
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
        
        self.detail_title = QLabel("İşlem Detayları")
        self.detail_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS.TEXT_PRIMARY};
            border: none;
        """)
        layout.addWidget(self.detail_title)
        
        date_label = QLabel("Tarih")
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
        self.detail_type.addItem("Gelir", TransactionType.INCOME)
        self.detail_type.addItem("Gider", TransactionType.EXPENSE)
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
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save_detail)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("Sil")
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.DANGER};
                padding: 10px 20px;
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
        self.save_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        
        if not enabled:
            self.detail_category.clear()
            self.detail_description.clear()
            self.detail_amount.setValue(0)
            self.detail_title.setText("İşlem Detayları")
    
    def _on_selection_changed(self) -> None:
        """Tablo seçimi değiştiğinde çağrılır."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_transaction = None
            self._set_detail_enabled(False)
            return
        
        row = selected_rows[0].row()
        trans_id = int(self.table.item(row, 0).text())
        
        all_transactions = self.controller.get_all_transactions()
        self._selected_transaction = next((t for t in all_transactions if t.id == trans_id), None)
        
        if self._selected_transaction:
            self._load_detail(self._selected_transaction)
            self._set_detail_enabled(True)
    
    def _load_detail(self, trans: Transaction) -> None:
        """Transaction detaylarını panele yükler."""
        self.detail_title.setText(f"{trans.category or 'işlem'}")
        
        self.detail_date.setDate(QDate(trans.transaction_date.year, trans.transaction_date.month, trans.transaction_date.day))
        
        self.detail_account.clear()
        self._accounts = self.controller.get_all_accounts()
        for acc in self._accounts:
            self.detail_account.addItem(acc.name, acc.id)
        
        acc_index = self.detail_account.findData(trans.account_id)
        if acc_index >= 0:
            self.detail_account.setCurrentIndex(acc_index)
        
        type_index = self.detail_type.findData(trans.transaction_type)
        if type_index >= 0:
            self.detail_type.setCurrentIndex(type_index)
        
        self.detail_category.setText(trans.category or "")
        self.detail_amount.setValue(trans.amount)
        self.detail_description.setText(trans.description or "")
    
    def _on_save_detail(self) -> None:
        """Detay panelinden işlemi kaydeder."""
        if not self._selected_transaction:
            return
        
        old_trans = Transaction(
            id=self._selected_transaction.id,
            account_id=self._selected_transaction.account_id,
            transaction_type=self._selected_transaction.transaction_type,
            amount=self._selected_transaction.amount,
            currency=self._selected_transaction.currency,
            category=self._selected_transaction.category,
            description=self._selected_transaction.description,
            transaction_date=self._selected_transaction.transaction_date
        )
        
        qdate = self.detail_date.date()
        from datetime import date as dt_date
        
        new_trans = Transaction(
            id=self._selected_transaction.id,
            account_id=self.detail_account.currentData(),
            transaction_type=self.detail_type.currentData(),
            amount=self.detail_amount.value(),
            currency=self._selected_transaction.currency,
            category=self.detail_category.text().strip(),
            description=self.detail_description.text().strip(),
            transaction_date=dt_date(qdate.year(), qdate.month(), qdate.day())
        )
        
        self.controller.update_transaction(old_trans, new_trans)
        self.refresh()
        self.transaction_changed.emit()
    
    def _on_delete_selected(self) -> None:
        """Seçili işlemi siler."""
        if self._selected_transaction:
            self._on_delete_transaction(self._selected_transaction)
    
    def refresh(self) -> None:
        """İşlem listesini yeniler."""
        filter_type = self.filter_combo.currentData()
        
        if filter_type == "all":
            transactions = self.controller.get_all_transactions()
        else:
            transactions = self.controller.get_transactions_by_type(filter_type)
        
        category_filter = self.category_search.text().strip().lower()
        if category_filter:
            transactions = [
                t for t in transactions 
                if t.category and category_filter in t.category.lower()
            ]
        
        accounts = {a.id: a for a in self.controller.get_all_accounts()}
        
        self.table.setRowCount(len(transactions))
        
        for row, trans in enumerate(transactions):
            id_item = QTableWidgetItem(str(trans.id))
            self.table.setItem(row, 0, id_item)
            
            date_str = trans.transaction_date.strftime("%d.%m.%Y")
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            
            account = accounts.get(trans.account_id)
            account_name = account.name if account else "-"
            self.table.setItem(row, 2, QTableWidgetItem(account_name))
            
            if trans.is_income:
                type_text = "Gelir"
                color = COLORS.SUCCESS
            else:
                type_text = "Gider"
                color = COLORS.DANGER
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor(color))
            self.table.setItem(row, 3, type_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(trans.category or "-"))
            
            self.table.setItem(row, 5, QTableWidgetItem(trans.description or "-"))
            
            symbol = CURRENCIES[trans.currency].symbol
            if trans.is_income:
                amount_text = f"+{symbol}{trans.amount:,.2f}"
            else:
                amount_text = f"-{symbol}{trans.amount:,.2f}"
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setForeground(QColor(color))
            self.table.setItem(row, 6, amount_item)
    
    def _on_add_transaction(self) -> None:
        """Yeni işlem ekleme."""
        accounts = self.controller.get_all_accounts()
        if not accounts:
            QMessageBox.warning(
                self,
                "Uyarı",
                "İşlem eklemek için önce bir hesap oluşturmalısınız!"
            )
            return
        
        dialog = TransactionDialog(self, accounts=accounts)
        if dialog.exec():
            transaction = dialog.get_data()
            self.controller.create_transaction(transaction)
            self.refresh()
            self.transaction_changed.emit()
    
    def _on_edit_transaction(self, transaction: Transaction) -> None:
        """
        İşlem düzenleme.
        
        Args:
            transaction: Düzenlenecek işlem
        """
        accounts = self.controller.get_all_accounts()
        dialog = TransactionDialog(self, transaction, accounts)
        if dialog.exec():
            updated_transaction = dialog.get_data()
            self.controller.update_transaction(transaction, updated_transaction)
            self.refresh()
            self.transaction_changed.emit()
    
    def _on_delete_transaction(self, transaction: Transaction) -> None:
        """
        İşlem silme.
        
        Args:
            transaction: Silinecek işlem
        """
        reply = QMessageBox.question(
            self,
            "İşlem Sil",
            "Bu işlemi silmek istediğinize emin misiniz?\n\n"
            "Bu işlem geri alınamaz ve hesap bakiyesi güncellenecektir!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_transaction(transaction)
            self.refresh()
            self.transaction_changed.emit()
