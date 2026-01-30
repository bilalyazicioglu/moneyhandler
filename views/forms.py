"""
Form Dialog Modülü

Veri giriş formları için PyQt6 dialog sınıfları.
Hesap, İşlem ve Planlanan İşlem ekleme/düzenleme formları.
"""

from datetime import date
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QDoubleSpinBox,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QMessageBox,
    QFrame
)
from PyQt6.QtCore import QDate

from config import CURRENCIES, TransactionType, COLORS, convert_currency
from models.account import Account
from models.transaction import Transaction
from models.planned_item import PlannedItem


class AccountDialog(QDialog):
    """
    Hesap ekleme/düzenleme formu.
    
    Attributes:
        account: Düzenlenecek hesap (None ise yeni hesap)
    """
    
    def __init__(
        self,
        parent=None,
        account: Optional[Account] = None
    ) -> None:
        """
        Dialog başlatıcısı.
        
        Args:
            parent: Üst widget
            account: Düzenlenecek hesap (opsiyonel)
        """
        super().__init__(parent)
        self.account = account
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle("Hesap Ekle" if self.account is None else "Hesap Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Hesap Ekle" if self.account is None else "Hesap Düzenle")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS.BORDER};")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Nakit Cüzdan, Ziraat Bankası")
        form_layout.addRow("Hesap Adı", self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("Nakit", "cash")
        self.type_combo.addItem("Banka", "bank")
        form_layout.addRow("Hesap Tipi", self.type_combo)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name}", code)
        form_layout.addRow("Para Birimi", self.currency_combo)
        
        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(-999999999, 999999999)
        self.balance_input.setDecimals(2)
        self.balance_input.setSingleStep(100)
        if self.account is not None:
            self.balance_input.setEnabled(False)
        form_layout.addRow("Bakiye", self.balance_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Hesap açıklaması (opsiyonel)")
        form_layout.addRow("Açıklama", self.description_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_data(self) -> None:
        """Mevcut hesap verilerini forma yükler."""
        if self.account is None:
            return
        
        self.name_input.setText(self.account.name)
        
        index = self.type_combo.findData(self.account.account_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        index = self.currency_combo.findData(self.account.currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        
        self.balance_input.setValue(self.account.balance)
        self.description_input.setPlainText(self.account.description)
    
    def _on_save(self) -> None:
        """Kaydet butonuna tıklandığında."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Hesap adı boş olamaz!")
            return
        
        self.accept()
    
    def get_data(self) -> Account:
        """
        Form verilerinden Account nesnesi oluşturur.
        
        Returns:
            Account nesnesi
        """
        return Account(
            id=self.account.id if self.account else None,
            name=self.name_input.text().strip(),
            account_type=self.type_combo.currentData(),
            currency=self.currency_combo.currentData(),
            balance=self.balance_input.value(),
            description=self.description_input.toPlainText().strip()
        )


class TransactionDialog(QDialog):
    """
    İşlem ekleme/düzenleme formu.
    
    Attributes:
        transaction: Düzenlenecek işlem (None ise yeni işlem)
        accounts: Hesap listesi
    """
    
    def __init__(
        self,
        parent=None,
        transaction: Optional[Transaction] = None,
        accounts: List[Account] = None,
        categories: List[str] = None
    ) -> None:
        """
        Dialog başlatıcısı.
        
        Args:
            parent: Üst widget
            transaction: Düzenlenecek işlem (opsiyonel)
            accounts: Hesap listesi
            categories: Mevcut kategori listesi
        """
        super().__init__(parent)
        self.transaction = transaction
        self.accounts = accounts or []
        self.categories = categories or []
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle("İşlem Ekle" if self.transaction is None else "İşlem Düzenle")
        self.setMinimumWidth(480)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("İşlem Ekle" if self.transaction is None else "İşlem Düzenle")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS.BORDER};")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.account_combo = QComboBox()
        for account in self.accounts:
            symbol = CURRENCIES[account.currency].symbol
            self.account_combo.addItem(
                f"{account.name} ({symbol})",
                account.id
            )
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        form_layout.addRow("Hesap", self.account_combo)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("Gelir", TransactionType.INCOME)
        self.type_combo.addItem("Gider", TransactionType.EXPENSE)
        form_layout.addRow("İşlem Tipi", self.type_combo)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(100)
        form_layout.addRow("Tutar", self.amount_input)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name}", code)
        form_layout.addRow("Para Birimi", self.currency_combo)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow("Tarih", self.date_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.category_input.addItems(self.categories)
        self.category_input.setCurrentText("")
        self.category_input.lineEdit().setPlaceholderText("Örn: Maaş, Kira, Market")
        form_layout.addRow("Kategori", self.category_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("İşlem açıklaması (opsiyonel)")
        form_layout.addRow("Açıklama", self.description_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        if self.transaction is None and len(self.accounts) > 0:
            self._on_account_changed(0)
    
    def _on_account_changed(self, index: int) -> None:
        """Hesap değiştiğinde para birimini günceller."""
        if index < 0 or index >= len(self.accounts):
            return
        account = self.accounts[index]
        currency_index = self.currency_combo.findData(account.currency)
        if currency_index >= 0:
            self.currency_combo.setCurrentIndex(currency_index)
    
    def _load_data(self) -> None:
        """Mevcut işlem verilerini forma yükler."""
        if self.transaction is None:
            return
        
        index = self.account_combo.findData(self.transaction.account_id)
        if index >= 0:
            self.account_combo.setCurrentIndex(index)
        
        index = self.type_combo.findData(self.transaction.transaction_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        self.amount_input.setValue(self.transaction.amount)
        
        index = self.currency_combo.findData(self.transaction.currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        
        self.date_input.setDate(QDate(
            self.transaction.transaction_date.year,
            self.transaction.transaction_date.month,
            self.transaction.transaction_date.day
        ))
        
        self.category_input.setCurrentText(self.transaction.category)
        self.description_input.setPlainText(self.transaction.description)
    
    def _on_save(self) -> None:
        """Kaydet butonuna tıklandığında."""
        if self.account_combo.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Önce bir hesap oluşturmalısınız!")
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Uyarı", "Tutar 0'dan büyük olmalıdır!")
            return
        
        self.accept()
    
    def get_data(self) -> Transaction:
        """
        Form verilerinden Transaction nesnesi oluşturur.
        
        Para birimi hesabın para biriminden farklıysa, tutar
        hesabın para birimine dönüştürülür.
        
        Returns:
            Transaction nesnesi
        """
        qdate = self.date_input.date()
        trans_date = date(qdate.year(), qdate.month(), qdate.day())
        
        amount = self.amount_input.value()
        selected_currency = self.currency_combo.currentData()
        account_id = self.account_combo.currentData()
        
        account_currency = selected_currency
        for acc in self.accounts:
            if acc.id == account_id:
                account_currency = acc.currency
                break
        
        if selected_currency != account_currency:
            amount = convert_currency(amount, selected_currency, account_currency)
        
        return Transaction(
            id=self.transaction.id if self.transaction else None,
            account_id=account_id,
            transaction_type=self.type_combo.currentData(),
            amount=amount,
            currency=account_currency,
            category=self.category_input.currentText().strip(),
            description=self.description_input.toPlainText().strip(),
            transaction_date=trans_date
        )


class PlannedItemDialog(QDialog):
    """
    Planlanan işlem ekleme/düzenleme formu.
    
    Attributes:
        planned_item: Düzenlenecek planlanan işlem (None ise yeni)
        accounts: Hesap listesi
    """
    
    def __init__(
        self,
        parent=None,
        planned_item: Optional[PlannedItem] = None,
        accounts: List[Account] = None,
        categories: List[str] = None
    ) -> None:
        """
        Dialog başlatıcısı.
        
        Args:
            parent: Üst widget
            planned_item: Düzenlenecek planlanan işlem (opsiyonel)
            accounts: Hesap listesi
            categories: Mevcut kategori listesi
        """
        super().__init__(parent)
        self.planned_item = planned_item
        self.accounts = accounts or []
        self.categories = categories or []
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle(
            "Planlanan İşlem Ekle" if self.planned_item is None 
            else "Planlanan İşlem Düzenle"
        )
        self.setMinimumWidth(480)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Başlık
        title = QLabel(
            "Planlanan İşlem Ekle" if self.planned_item is None 
            else "Planlanan İşlem Düzenle"
        )
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS.BORDER};")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.account_combo = QComboBox()
        for account in self.accounts:
            symbol = CURRENCIES[account.currency].symbol
            self.account_combo.addItem(
                f"{account.name} ({symbol})",
                account.id
            )
        form_layout.addRow("Hesap", self.account_combo)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("Beklenen Gelir", TransactionType.INCOME)
        self.type_combo.addItem("Beklenen Gider", TransactionType.EXPENSE)
        form_layout.addRow("İşlem Tipi", self.type_combo)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(100)
        form_layout.addRow("Tutar", self.amount_input)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name}", code)
        form_layout.addRow("Para Birimi", self.currency_combo)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow("Planlanan Tarih", self.date_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.category_input.addItems(self.categories)
        self.category_input.setCurrentText("")
        self.category_input.lineEdit().setPlaceholderText("Örn: Maaş, Kira, Fatura")
        form_layout.addRow("Kategori", self.category_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Açıklama (opsiyonel)")
        form_layout.addRow("Açıklama", self.description_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_data(self) -> None:
        """Mevcut planlanan işlem verilerini forma yükler."""
        if self.planned_item is None:
            return
        
        index = self.account_combo.findData(self.planned_item.account_id)
        if index >= 0:
            self.account_combo.setCurrentIndex(index)
        
        index = self.type_combo.findData(self.planned_item.transaction_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        self.amount_input.setValue(self.planned_item.amount)
        
        index = self.currency_combo.findData(self.planned_item.currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        
        self.date_input.setDate(QDate(
            self.planned_item.planned_date.year,
            self.planned_item.planned_date.month,
            self.planned_item.planned_date.day
        ))
        
        self.category_input.setCurrentText(self.planned_item.category)
        self.description_input.setPlainText(self.planned_item.description)
    
    def _on_save(self) -> None:
        """Kaydet butonuna tıklandığında."""
        if self.account_combo.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Önce bir hesap oluşturmalısınız!")
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Uyarı", "Tutar 0'dan büyük olmalıdır!")
            return
        
        self.accept()
    
    def get_data(self) -> PlannedItem:
        """
        Form verilerinden PlannedItem nesnesi oluşturur.
        
        Returns:
            PlannedItem nesnesi
        """
        qdate = self.date_input.date()
        plan_date = date(qdate.year(), qdate.month(), qdate.day())
        
        return PlannedItem(
            id=self.planned_item.id if self.planned_item else None,
            account_id=self.account_combo.currentData(),
            transaction_type=self.type_combo.currentData(),
            amount=self.amount_input.value(),
            currency=self.currency_combo.currentData(),
            category=self.category_input.currentText().strip(),
            description=self.description_input.toPlainText().strip(),
            planned_date=plan_date
        )
