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
    QComboBox
)
from PyQt6.QtGui import QColor

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
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Başlık ve butonlar
        header_layout = QHBoxLayout()
        
        # Sol taraf: Başlık
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
        
        # Filtre
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
        
        # Boşluk
        header_layout.addSpacing(16)
        
        # Yeni işlem butonu
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
        
        # İşlem tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Hesap", "Tip", "Kategori", "Açıklama", "Tutar", "İşlemler"
        ])
        
        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(6, 140)
        self.table.setColumnWidth(7, 160)
        
        # ID sütununu gizle
        self.table.setColumnHidden(0, True)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        layout.addWidget(self.table)
    
    def refresh(self) -> None:
        """İşlem listesini yeniler."""
        filter_type = self.filter_combo.currentData()
        
        if filter_type == "all":
            transactions = self.controller.get_all_transactions()
        else:
            transactions = self.controller.get_transactions_by_type(filter_type)
        
        accounts = {a.id: a for a in self.controller.get_all_accounts()}
        
        self.table.setRowCount(len(transactions))
        
        for row, trans in enumerate(transactions):
            # ID (gizli)
            id_item = QTableWidgetItem(str(trans.id))
            self.table.setItem(row, 0, id_item)
            
            # Tarih
            date_str = trans.transaction_date.strftime("%d.%m.%Y")
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Hesap
            account = accounts.get(trans.account_id)
            account_name = account.name if account else "-"
            self.table.setItem(row, 2, QTableWidgetItem(account_name))
            
            # Tip
            if trans.is_income:
                type_text = "Gelir"
                color = COLORS.SUCCESS
            else:
                type_text = "Gider"
                color = COLORS.DANGER
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor(color))
            self.table.setItem(row, 3, type_item)
            
            # Kategori
            self.table.setItem(row, 4, QTableWidgetItem(trans.category or "-"))
            
            # Açıklama
            self.table.setItem(row, 5, QTableWidgetItem(trans.description or "-"))
            
            # Tutar
            symbol = CURRENCIES[trans.currency].symbol
            if trans.is_income:
                amount_text = f"+{symbol}{trans.amount:,.2f}"
            else:
                amount_text = f"-{symbol}{trans.amount:,.2f}"
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setForeground(QColor(color))
            self.table.setItem(row, 6, amount_item)
            
            # İşlem butonları
            self._add_action_buttons(row, trans)
    
    def _add_action_buttons(self, row: int, transaction: Transaction) -> None:
        """
        Satıra işlem butonlarını ekler.
        
        Args:
            row: Satır indeksi
            transaction: İşlem nesnesi
        """
        button_widget = QWidget()
        button_widget.setStyleSheet("background-color: transparent;")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(8, 4, 8, 4)
        button_layout.setSpacing(8)
        
        # Düzenle butonu
        edit_btn = QPushButton("Düzenle")
        edit_btn.setFixedHeight(32)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
                border-color: {COLORS.BORDER_LIGHT};
            }}
        """)
        edit_btn.clicked.connect(lambda: self._on_edit_transaction(transaction))
        button_layout.addWidget(edit_btn)
        
        # Sil butonu
        delete_btn = QPushButton("Sil")
        delete_btn.setFixedHeight(32)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS.DANGER};
                color: {COLORS.DANGER};
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.DANGER};
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        delete_btn.clicked.connect(lambda: self._on_delete_transaction(transaction))
        button_layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row, 7, button_widget)
    
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
