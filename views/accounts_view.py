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
    QMessageBox,
    QSplitter,
    QFrame,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QDialog,
    QTextEdit
)
from PyQt6.QtGui import QColor

from config import COLORS, CURRENCIES
from models.account import Account
from views.forms import AccountDialog

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class AccountInfoDialog(QDialog):
    """
    Hesap bilgi ve işlem geçmişi popup dialog'u.
    """
    
    def __init__(self, parent, account: Account, transactions: list, controller=None) -> None:
        super().__init__(parent)
        self.account = account
        self.transactions = transactions
        self.controller = controller
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Dialog UI'ını oluşturur."""
        self.setWindowTitle(f"{self.account.name} - Hesap Detayları")
        self.setMinimumSize(600, 500)
        self.setStyleSheet(f"background-color: {COLORS.BG_DARK};")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Başlık
        title = QLabel(self.account.name)
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        # Açıklama bölümü
        desc_label = QLabel("Açıklama")
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; margin-top: 8px;")
        layout.addWidget(desc_label)
        
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(80)
        self.description_text.setText(self.account.description if self.account.description else "")
        self.description_text.setPlaceholderText("Hesap açıklaması girin...")
        self.description_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                border-radius: 8px;
                padding: 8px;
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.description_text)
        
        # İşlem geçmişi bölümü
        history_label = QLabel(f"İşlem Geçmişi ({len(self.transactions)} işlem)")
        history_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; margin-top: 8px;")
        layout.addWidget(history_label)
        
        history_table = QTableWidget()
        history_table.setColumnCount(5)
        history_table.setHorizontalHeaderLabels(["Tarih", "Tip", "Kategori", "Açıklama", "Tutar"])
        history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        history_table.verticalHeader().setVisible(False)
        history_table.setShowGrid(False)
        
        history_header = history_table.horizontalHeader()
        history_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        history_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        history_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        history_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        history_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        history_table.setColumnWidth(0, 90)
        history_table.setColumnWidth(1, 60)
        history_table.setColumnWidth(2, 100)
        history_table.setColumnWidth(4, 120)
        
        # İşlemleri tabloya ekle
        history_table.setRowCount(len(self.transactions))
        for row, trans in enumerate(self.transactions):
            date_item = QTableWidgetItem(trans.transaction_date.strftime("%d.%m.%Y"))
            history_table.setItem(row, 0, date_item)
            
            type_text = "Gelir" if trans.is_income else "Gider"
            type_item = QTableWidgetItem(type_text)
            if trans.is_income:
                type_item.setForeground(QColor(COLORS.SUCCESS))
            else:
                type_item.setForeground(QColor(COLORS.DANGER))
            history_table.setItem(row, 1, type_item)
            
            history_table.setItem(row, 2, QTableWidgetItem(trans.category or "-"))
            history_table.setItem(row, 3, QTableWidgetItem(trans.description or "-"))
            
            currency = CURRENCIES.get(trans.currency)
            symbol = currency.symbol if currency else ""
            amount_text = f"{symbol}{trans.amount:,.2f}"
            amount_item = QTableWidgetItem(amount_text)
            if trans.is_income:
                amount_item.setForeground(QColor(COLORS.SUCCESS))
            else:
                amount_item.setForeground(QColor(COLORS.DANGER))
            history_table.setItem(row, 4, amount_item)
        
        layout.addWidget(history_table)
        
        # Buton layout
        btn_layout = QHBoxLayout()
        
        # Kaydet butonu
        save_btn = QPushButton("Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                padding: 12px 24px;
                font-size: 14px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_LIGHT};
            }}
        """)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)
        
        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                padding: 12px 24px;
                font-size: 14px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_save(self) -> None:
        """Açıklamayı kaydeder."""
        new_description = self.description_text.toPlainText().strip()
        self.account.description = new_description
        
        if self.controller:
            self.controller.update_account(self.account)
            QMessageBox.information(self, "Başarılı", "Açıklama kaydedildi!")
        else:
            QMessageBox.warning(self, "Uyarı", "Değişiklik kaydedilemedi.")


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
        self._selected_account = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        header_layout = QHBoxLayout()
        
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
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Hesap Adı", "Tip", "Para Birimi", "Bakiye"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 160)
        
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        splitter.addWidget(self.table)
        
        self.detail_panel = self._create_detail_panel()
        splitter.addWidget(self.detail_panel)
        
        splitter.setSizes([600, 300])
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
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_layout = QHBoxLayout()
        self.detail_title = QLabel("Hesap Detayları")
        self.detail_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS.TEXT_PRIMARY};
            border: none;
        """)
        title_layout.addWidget(self.detail_title)
        title_layout.addStretch()
        
        self.info_btn = QPushButton("Detay")
        self.info_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        self.info_btn.clicked.connect(self._show_info_dialog)
        title_layout.addWidget(self.info_btn)
        layout.addLayout(title_layout)
        
        name_label = QLabel("Hesap Adı")
        name_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(name_label)
        
        self.detail_name = QLineEdit()
        self.detail_name.setPlaceholderText("Hesap adı girin...")
        layout.addWidget(self.detail_name)
        
        type_label = QLabel("Hesap Tipi")
        type_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(type_label)
        
        self.detail_type = QComboBox()
        self.detail_type.addItem("Nakit", "cash")
        self.detail_type.addItem("Banka", "bank")
        layout.addWidget(self.detail_type)
        
        currency_label = QLabel("Para Birimi")
        currency_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(currency_label)
        
        self.detail_currency = QComboBox()
        for code, currency in CURRENCIES.items():
            self.detail_currency.addItem(f"{currency.symbol} {currency.name}", code)
        layout.addWidget(self.detail_currency)
        
        balance_label = QLabel("Bakiye")
        balance_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px; border: none;")
        layout.addWidget(balance_label)
        
        self.detail_balance = QLabel("₺0.00")
        self.detail_balance.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {COLORS.SUCCESS};
            border: none;
        """)
        layout.addWidget(self.detail_balance)
        
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
    
    def _show_info_dialog(self) -> None:
        """Hesap bilgi dialog'unu gösterir."""
        if not self._selected_account:
            return
        
        transactions = self.controller.get_transactions_by_account(self._selected_account.id)
        dialog = AccountInfoDialog(self, self._selected_account, transactions, self.controller)
        dialog.exec()
        self.refresh()
    
    def _set_detail_enabled(self, enabled: bool) -> None:
        """Detay panelini etkinleştirir/devre dışı bırakır."""
        self.detail_name.setEnabled(enabled)
        self.detail_type.setEnabled(enabled)
        self.detail_currency.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.info_btn.setEnabled(enabled)
        
        if not enabled:
            self.detail_name.clear()
            self.detail_balance.setText("₺0.00")
            self.detail_title.setText("Hesap Detayları")
    
    def _on_selection_changed(self) -> None:
        """Tablo seçimi değiştiğinde çağrılır."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_account = None
            self._set_detail_enabled(False)
            return
        
        row = selected_rows[0].row()
        account_id = int(self.table.item(row, 0).text())
        self._selected_account = self.controller.get_account_by_id(account_id)
        
        if self._selected_account:
            self._load_detail(self._selected_account)
            self._set_detail_enabled(True)
    
    def _load_detail(self, account: Account) -> None:
        """Hesap detaylarını panele yükler."""
        self.detail_title.setText(f"{account.name}")
        self.detail_name.setText(account.name)
        
        type_index = self.detail_type.findData(account.account_type)
        if type_index >= 0:
            self.detail_type.setCurrentIndex(type_index)
        
        currency_index = self.detail_currency.findData(account.currency)
        if currency_index >= 0:
            self.detail_currency.setCurrentIndex(currency_index)
        
        currency = CURRENCIES.get(account.currency)
        symbol = currency.symbol if currency else ""
        self.detail_balance.setText(f"{symbol}{account.balance:,.2f}")
        
        if account.balance >= 0:
            self.detail_balance.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS.SUCCESS}; border: none;")
        else:
            self.detail_balance.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS.DANGER}; border: none;")
    
    def _on_save_detail(self) -> None:
        """Detay panelinden hesabı kaydeder."""
        if not self._selected_account:
            return
        
        name = self.detail_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Hesap adı boş olamaz!")
            return
        
        self._selected_account.name = name
        self._selected_account.account_type = self.detail_type.currentData()
        self._selected_account.currency = self.detail_currency.currentData()
        
        self.controller.update_account(self._selected_account)
        self.refresh()
        self.account_changed.emit()
    
    def _on_delete_selected(self) -> None:
        """Seçili hesabı siler."""
        if self._selected_account:
            self._on_delete_account(self._selected_account)
    
    def refresh(self) -> None:
        """Hesap listesini yeniler."""
        accounts = self.controller.get_all_accounts()
        
        self.table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            id_item = QTableWidgetItem(str(account.id))
            self.table.setItem(row, 0, id_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(account.name))
            
            type_text = "Nakit" if account.account_type == "cash" else "Banka"
            self.table.setItem(row, 2, QTableWidgetItem(type_text))
            
            currency = CURRENCIES.get(account.currency)
            currency_text = f"{currency.symbol} {currency.code}" if currency else account.currency
            self.table.setItem(row, 3, QTableWidgetItem(currency_text))
            
            symbol = currency.symbol if currency else ""
            balance_text = f"{symbol}{account.balance:,.2f}"
            balance_item = QTableWidgetItem(balance_text)
            if account.balance >= 0:
                balance_item.setForeground(QColor(COLORS.SUCCESS))
            else:
                balance_item.setForeground(QColor(COLORS.DANGER))
            self.table.setItem(row, 4, balance_item)
    
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
