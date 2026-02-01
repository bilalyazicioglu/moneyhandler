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

from config import CURRENCIES, TransactionType, COLORS, convert_currency, t
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
        self.setWindowTitle(t("dialog_add_account") if self.account is None else t("dialog_edit_account"))
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel(t("dialog_add_account") if self.account is None else t("dialog_edit_account"))
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
        self.name_input.setPlaceholderText(t("placeholder_account_name"))
        form_layout.addRow(t("account_name"), self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(t("account_type_cash"), "cash")
        self.type_combo.addItem(t("account_type_bank"), "bank")
        form_layout.addRow(t("account_type"), self.type_combo)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name}", code)
        form_layout.addRow(t("currency"), self.currency_combo)
        
        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(-999999999, 999999999)
        self.balance_input.setDecimals(2)
        self.balance_input.setSingleStep(100)
        if self.account is not None:
            self.balance_input.setEnabled(False)
        form_layout.addRow(t("balance"), self.balance_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText(t("placeholder_account_desc"))
        form_layout.addRow(t("description"), self.description_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(t("cancel"))
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
        
        self.save_btn = QPushButton(t("save"))
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
            QMessageBox.warning(self, t("warning"), t("msg_account_empty"))
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
        self.setWindowTitle(t("dialog_add_transaction") if self.transaction is None else t("dialog_edit_transaction"))
        self.setMinimumWidth(480)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel(t("dialog_add_transaction") if self.transaction is None else t("dialog_edit_transaction"))
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
        form_layout.addRow(t("account"), self.account_combo)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(t("income"), TransactionType.INCOME)
        self.type_combo.addItem(t("expense"), TransactionType.EXPENSE)
        form_layout.addRow(t("transaction_type"), self.type_combo)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(100)
        form_layout.addRow(t("amount"), self.amount_input)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name}", code)
        form_layout.addRow(t("currency"), self.currency_combo)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow(t("date"), self.date_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.category_input.addItems(self.categories)
        self.category_input.setCurrentText("")
        self.category_input.lineEdit().setPlaceholderText(t("placeholder_category"))
        form_layout.addRow(t("category"), self.category_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText(t("placeholder_description"))
        form_layout.addRow(t("description"), self.description_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(t("cancel"))
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
        
        self.save_btn = QPushButton(t("save"))
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
            QMessageBox.warning(self, t("warning"), t("msg_create_account_first"))
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, t("warning"), t("msg_amount_positive"))
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
            t("dialog_add_planned") if self.planned_item is None 
            else t("dialog_edit_planned")
        )
        self.setMinimumWidth(480)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Başlık
        title = QLabel(
            t("dialog_add_planned") if self.planned_item is None 
            else t("dialog_edit_planned")
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
        form_layout.addRow(t("account"), self.account_combo)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(t("expected_income"), TransactionType.INCOME)
        self.type_combo.addItem(t("expected_expense"), TransactionType.EXPENSE)
        form_layout.addRow(t("transaction_type"), self.type_combo)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(100)
        form_layout.addRow(t("amount"), self.amount_input)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name}", code)
        form_layout.addRow(t("currency"), self.currency_combo)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow(t("planned_date"), self.date_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.category_input.addItems(self.categories)
        self.category_input.setCurrentText("")
        self.category_input.lineEdit().setPlaceholderText(t("placeholder_planned_category"))
        form_layout.addRow(t("category"), self.category_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText(f"{t('description')} ({t('optional')})")
        form_layout.addRow(t("description"), self.description_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(t("cancel"))
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
        
        self.save_btn = QPushButton(t("save"))
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
            QMessageBox.warning(self, t("warning"), t("msg_create_account_first"))
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, t("warning"), t("msg_amount_positive"))
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


class RegularIncomeDialog(QDialog):
    """
    Düzenli gelir ekleme/düzenleme formu.
    
    Attributes:
        regular_income: Düzenlenecek düzenli gelir (None ise yeni)
        accounts: Hesap listesi
    """
    
    def __init__(
        self,
        parent=None,
        regular_income=None,
        accounts: List[Account] = None
    ) -> None:
        """
        Dialog başlatıcısı.
        
        Args:
            parent: Üst widget
            regular_income: Düzenlenecek düzenli gelir (opsiyonel)
            accounts: Hesap listesi
        """
        super().__init__(parent)
        self.regular_income = regular_income
        self.accounts = accounts or []
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle(
            t("dialog_add_regular_income") if self.regular_income is None 
            else t("dialog_edit_regular_income")
        )
        self.setMinimumWidth(480)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel(
            t("dialog_add_regular_income") if self.regular_income is None 
            else t("dialog_edit_regular_income")
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
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t("placeholder_income_name"))
        form_layout.addRow(t("income_name"), self.name_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem(t("category_salary"), "salary")
        self.category_combo.addItem(t("category_scholarship"), "scholarship")
        self.category_combo.addItem(t("category_allowance"), "allowance")
        self.category_combo.addItem(t("category_rental"), "rental")
        self.category_combo.addItem(t("category_other_income"), "other")
        form_layout.addRow(t("category"), self.category_combo)
        
        self.account_combo = QComboBox()
        for account in self.accounts:
            symbol = CURRENCIES[account.currency].symbol
            self.account_combo.addItem(
                f"{account.name} ({symbol})",
                account.id
            )
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        form_layout.addRow(t("account"), self.account_combo)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(100)
        form_layout.addRow(t("amount"), self.amount_input)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name}", code)
        form_layout.addRow(t("currency"), self.currency_combo)
        
        from PyQt6.QtWidgets import QSpinBox
        self.day_input = QSpinBox()
        self.day_input.setRange(1, 31)
        self.day_input.setValue(1)
        form_layout.addRow(t("day_of_month"), self.day_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText(f"{t('description')} ({t('optional')})")
        form_layout.addRow(t("description"), self.description_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(t("cancel"))
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
        
        self.save_btn = QPushButton(t("save"))
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
        
        if self.regular_income is None and len(self.accounts) > 0:
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
        """Mevcut düzenli gelir verilerini forma yükler."""
        if self.regular_income is None:
            return
        
        self.name_input.setText(self.regular_income.name)
        
        index = self.category_combo.findData(self.regular_income.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        
        index = self.account_combo.findData(self.regular_income.account_id)
        if index >= 0:
            self.account_combo.setCurrentIndex(index)
        
        self.amount_input.setValue(self.regular_income.amount)
        
        index = self.currency_combo.findData(self.regular_income.currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        
        self.day_input.setValue(self.regular_income.expected_day)
        self.description_input.setPlainText(self.regular_income.description)
    
    def _on_save(self) -> None:
        """Kaydet butonuna tıklandığında."""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, t("warning"), t("msg_account_empty"))
            return
        
        if self.account_combo.count() == 0:
            QMessageBox.warning(self, t("warning"), t("msg_create_account_first"))
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, t("warning"), t("msg_amount_positive"))
            return
        
        self.accept()
    
    def get_data(self):
        """
        Form verilerinden RegularIncome nesnesi oluşturur.
        
        Returns:
            RegularIncome nesnesi
        """
        from models.regular_income import RegularIncome
        
        return RegularIncome(
            id=self.regular_income.id if self.regular_income else None,
            account_id=self.account_combo.currentData(),
            name=self.name_input.text().strip(),
            category=self.category_combo.currentData(),
            amount=self.amount_input.value(),
            currency=self.currency_combo.currentData(),
            expected_day=self.day_input.value(),
            description=self.description_input.toPlainText().strip()
        )


class RecordPaymentDialog(QDialog):
    """
    Ödeme kaydetme formu.
    
    Attributes:
        regular_income: İlişkili düzenli gelir
    """
    
    def __init__(
        self,
        parent=None,
        regular_income=None
    ) -> None:
        """
        Dialog başlatıcısı.
        
        Args:
            parent: Üst widget
            regular_income: İlişkili düzenli gelir
        """
        super().__init__(parent)
        self.regular_income = regular_income
        self._setup_ui()
        self._load_defaults()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle(t("dialog_record_payment"))
        self.setMinimumWidth(420)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel(t("dialog_record_payment"))
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        if self.regular_income:
            info_label = QLabel(f"{self.regular_income.name}")
            info_label.setStyleSheet(f"""
                color: {COLORS.TEXT_SECONDARY};
                font-size: 14px;
            """)
            layout.addWidget(info_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS.BORDER};")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.expected_date_input = QDateEdit()
        self.expected_date_input.setCalendarPopup(True)
        self.expected_date_input.setDate(QDate.currentDate())
        form_layout.addRow(t("expected_day"), self.expected_date_input)
        
        self.actual_date_input = QDateEdit()
        self.actual_date_input.setCalendarPopup(True)
        self.actual_date_input.setDate(QDate.currentDate())
        form_layout.addRow(t("actual_date"), self.actual_date_input)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(100)
        form_layout.addRow(t("amount"), self.amount_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText(f"{t('description')} ({t('optional')})")
        form_layout.addRow(t("description"), self.notes_input)
        
        layout.addLayout(form_layout)
        
        self.delay_label = QLabel()
        self.delay_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(self.delay_label)
        
        self.expected_date_input.dateChanged.connect(self._update_delay_display)
        self.actual_date_input.dateChanged.connect(self._update_delay_display)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(t("cancel"))
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
        
        self.save_btn = QPushButton(t("record_payment"))
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_LIGHT};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_defaults(self) -> None:
        """Varsayılan değerleri yükler."""
        if self.regular_income is None:
            return
        
        today = date.today()
        expected = self.regular_income.get_expected_date_for_month(today.year, today.month)
        
        self.expected_date_input.setDate(QDate(expected.year, expected.month, expected.day))
        self.actual_date_input.setDate(QDate.currentDate())
        self.amount_input.setValue(self.regular_income.amount)
        
        self._update_delay_display()
    
    def _update_delay_display(self) -> None:
        """Gecikme göstergesini günceller."""
        expected = self.expected_date_input.date()
        actual = self.actual_date_input.date()
        
        expected_date = date(expected.year(), expected.month(), expected.day())
        actual_date = date(actual.year(), actual.month(), actual.day())
        
        delay = (actual_date - expected_date).days
        
        if delay < 0:
            text = f"{abs(delay)} {t('days_early')}"
            color = COLORS.SUCCESS
        elif delay == 0:
            text = t('on_time')
            color = COLORS.INFO
        elif delay <= 3:
            text = f"{delay} {t('days_late')}"
            color = COLORS.WARNING
        else:
            text = f"{delay} {t('days_late')}"
            color = COLORS.DANGER
        
        self.delay_label.setText(text)
        self.delay_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
    
    def _on_save(self) -> None:
        """Kaydet butonuna tıklandığında."""
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, t("warning"), t("msg_amount_positive"))
            return
        
        self.accept()
    
    def get_data(self):
        """
        Form verilerinden IncomePayment nesnesi oluşturur.
        
        Returns:
            IncomePayment nesnesi
        """
        from models.regular_income import IncomePayment
        
        expected = self.expected_date_input.date()
        actual = self.actual_date_input.date()
        
        expected_date = date(expected.year(), expected.month(), expected.day())
        actual_date = date(actual.year(), actual.month(), actual.day())
        
        return IncomePayment(
            regular_income_id=self.regular_income.id if self.regular_income else None,
            expected_date=expected_date,
            actual_date=actual_date,
            amount=self.amount_input.value(),
            currency=self.regular_income.currency if self.regular_income else "TRY",
            notes=self.notes_input.toPlainText().strip()
        )

