"""
Hesaplar View Modülü

Hesap/Cüzdan yönetimi ekranı widget'ı.
Hesap listesi, ekleme, düzenleme ve silme işlemleri.
"""

from typing import TYPE_CHECKING, Optional

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
    QMessageBox
)
from PyQt6.QtGui import QColor

from config import COLORS, CURRENCIES
from models.account import Account
from views.forms import AccountDialog

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class AccountsView(QWidget):
    """
    Hesap yönetimi ekranı widget'ı.
    
    Signals:
        account_changed: Hesap eklendiğinde/güncellendiğinde/silindiğinde
    """
    
    account_changed = pyqtSignal()
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        """
        AccountsView başlatıcısı.
        
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
        
        title = QLabel("Hesaplar")
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Nakit ve banka hesaplarınızı yönetin")
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Yeni hesap butonu
        self.add_btn = QPushButton("Yeni Hesap")
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
        self.add_btn.clicked.connect(self._on_add_account)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Hesap tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Hesap Adı", "Tip", "Para Birimi", "Bakiye", "İşlemler"
        ])
        
        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 160)
        
        # ID sütununu gizle
        self.table.setColumnHidden(0, True)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        layout.addWidget(self.table)
    
    def refresh(self) -> None:
        """Hesap listesini yeniler."""
        accounts = self.controller.get_all_accounts()
        
        self.table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            # ID (gizli)
            id_item = QTableWidgetItem(str(account.id))
            self.table.setItem(row, 0, id_item)
            
            # Hesap Adı
            self.table.setItem(row, 1, QTableWidgetItem(account.name))
            
            # Tip
            type_text = "Nakit" if account.account_type == "cash" else "Banka"
            self.table.setItem(row, 2, QTableWidgetItem(type_text))
            
            # Para Birimi
            currency = CURRENCIES.get(account.currency)
            currency_text = f"{currency.symbol} {currency.code}" if currency else account.currency
            self.table.setItem(row, 3, QTableWidgetItem(currency_text))
            
            # Bakiye
            symbol = currency.symbol if currency else ""
            balance_text = f"{symbol}{account.balance:,.2f}"
            balance_item = QTableWidgetItem(balance_text)
            if account.balance >= 0:
                balance_item.setForeground(QColor(COLORS.SUCCESS))
            else:
                balance_item.setForeground(QColor(COLORS.DANGER))
            self.table.setItem(row, 4, balance_item)
            
            # İşlem butonları
            self._add_action_buttons(row, account)
    
    def _add_action_buttons(self, row: int, account: Account) -> None:
        """
        Satıra işlem butonlarını ekler.
        
        Args:
            row: Satır indeksi
            account: Hesap nesnesi
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
        edit_btn.clicked.connect(lambda: self._on_edit_account(account))
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
        delete_btn.clicked.connect(lambda: self._on_delete_account(account))
        button_layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row, 5, button_widget)
    
    def _on_add_account(self) -> None:
        """Yeni hesap ekleme."""
        dialog = AccountDialog(self)
        if dialog.exec():
            account = dialog.get_data()
            self.controller.create_account(account)
            self.refresh()
            self.account_changed.emit()
    
    def _on_edit_account(self, account: Account) -> None:
        """
        Hesap düzenleme.
        
        Args:
            account: Düzenlenecek hesap
        """
        dialog = AccountDialog(self, account)
        if dialog.exec():
            updated_account = dialog.get_data()
            self.controller.update_account(updated_account)
            self.refresh()
            self.account_changed.emit()
    
    def _on_delete_account(self, account: Account) -> None:
        """
        Hesap silme.
        
        Args:
            account: Silinecek hesap
        """
        reply = QMessageBox.question(
            self,
            "Hesap Sil",
            f"'{account.name}' hesabını silmek istediğinize emin misiniz?\n\n"
            "Bu işlem geri alınamaz ve hesaba bağlı tüm işlemler de silinecektir!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_account(account.id)
            self.refresh()
            self.account_changed.emit()
