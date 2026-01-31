"""
Dashboard View Modülü

Ana sayfa/özet ekranı widget'ı.
Toplam varlık, yaklaşan ödemeler ve son işlemleri görüntüler.
"""

from datetime import date
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QComboBox
)
from PyQt6.QtGui import QColor

from config import (
    COLORS,
    CURRENCIES,
    EXCHANGE_RATES,
    BASE_CURRENCY,
    convert_to_base_currency,
    convert_currency,
    UPCOMING_DAYS_THRESHOLD,
    TransactionType,
    t
)

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class DashboardView(QWidget):
    """
    Dashboard/Özet ekranı widget'ı.
    
    Toplam varlıkları, yaklaşan ödemeleri ve son işlemleri görüntüler.
    Tüm para birimleri ana para birimine (TRY) çevrilir.
    
    Signals:
        refresh_requested: Yenileme istendiğinde
    """
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        """
        Dashboard başlatıcısı.
        
        Args:
            controller: Ana controller referansı
            parent: Üst widget
        """
        super().__init__(parent)
        self.controller = controller
        self.display_currency = BASE_CURRENCY
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        title = QLabel(t("dashboard_title"))
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel(t("dashboard_subtitle"))
        subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS.TEXT_SECONDARY};
        """)
        header_layout.addWidget(subtitle)
        
        title_row = QHBoxLayout()
        title_row.addLayout(header_layout)
        title_row.addStretch()
        
        currency_layout = QHBoxLayout()
        currency_layout.setSpacing(8)
        
        currency_label = QLabel(f"{t('currency')}:")
        currency_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS.TEXT_SECONDARY};
        """)
        currency_layout.addWidget(currency_label)
        
        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {code}", code)
        self.currency_combo.setCurrentText(f"{CURRENCIES[BASE_CURRENCY].symbol} {BASE_CURRENCY}")
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self.currency_combo.setMinimumWidth(120)
        currency_layout.addWidget(self.currency_combo)
        
        title_row.addLayout(currency_layout)
        layout.addLayout(title_row)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        self.total_card = self._create_summary_card(
            t("total_assets"),
            "₺0.00",
            COLORS.PRIMARY,
            t("total_assets_desc")
        )
        cards_layout.addWidget(self.total_card)
        
        self.income_card = self._create_summary_card(
            t("total_income"),
            "₺0.00",
            COLORS.SUCCESS,
            t("total_income_desc")
        )
        cards_layout.addWidget(self.income_card)
        
        self.expense_card = self._create_summary_card(
            t("total_expense"),
            "₺0.00",
            COLORS.DANGER,
            t("total_expense_desc")
        )
        cards_layout.addWidget(self.expense_card)
        
        layout.addLayout(cards_layout)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        self.upcoming_group = self._create_upcoming_section()
        bottom_layout.addWidget(self.upcoming_group, 1)
        
        self.recent_group = self._create_recent_section()
        bottom_layout.addWidget(self.recent_group, 2)
        
        layout.addLayout(bottom_layout)
        layout.addStretch()
    
    def _create_summary_card(
        self,
        title: str,
        value: str,
        accent_color: str,
        subtitle: str = ""
    ) -> QFrame:
        """
        Özet kartı oluşturur.
        
        Args:
            title: Kart başlığı
            value: Gösterilecek değer
            accent_color: Vurgu rengi
            subtitle: Alt başlık
            
        Returns:
            Kart widget'ı
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.BG_CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 16px;
                border-left: 4px solid {accent_color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS.TEXT_SECONDARY};
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            color: {COLORS.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        """)
        layout.addWidget(value_label)
        
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"""
                color: {COLORS.TEXT_MUTED};
                font-size: 12px;
            """)
            layout.addWidget(subtitle_label)
        
        return card
    
    def _create_upcoming_section(self) -> QGroupBox:
        """
        Yaklaşan ödemeler bölümünü oluşturur.
        
        Returns:
            GroupBox widget'ı
        """
        group = QGroupBox(f"{t('upcoming_payments')} ({UPCOMING_DAYS_THRESHOLD} {t('upcoming_days')})")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.upcoming_table = QTableWidget()
        self.upcoming_table.setColumnCount(4)
        self.upcoming_table.setHorizontalHeaderLabels([
            t("date"), t("description"), t("amount"), t("type")
        ])
        self.upcoming_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.upcoming_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.upcoming_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.upcoming_table.verticalHeader().setVisible(False)
        self.upcoming_table.setShowGrid(False)
        
        layout.addWidget(self.upcoming_table)
        return group
    
    def _create_recent_section(self) -> QGroupBox:
        """
        Son işlemler bölümünü oluşturur.
        
        Returns:
            GroupBox widget'ı
        """
        group = QGroupBox(t("recent_transactions"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels([
            t("date"), t("account"), t("category"), t("description"), t("amount")
        ])
        self.recent_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.recent_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.recent_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setShowGrid(False)
        
        layout.addWidget(self.recent_table)
        return group
    
    def refresh(self) -> None:
        """Dashboard verilerini yeniler."""
        self._update_summary_cards()
        self._update_upcoming_table()
        self._update_recent_table()
    
    def _on_currency_changed(self) -> None:
        """Para birimi değiştiğinde çağrılır."""
        self.display_currency = self.currency_combo.currentData()
        self.refresh()
    
    def _update_summary_cards(self) -> None:
        """Özet kartlarını günceller."""
        total_in_try = self.controller.get_total_assets_in_base_currency()
        total_in_display = convert_currency(total_in_try, BASE_CURRENCY, self.display_currency)
        symbol = CURRENCIES[self.display_currency].symbol
        
        value_label = self.total_card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(f"{symbol}{total_in_display:,.2f}")
        
        summary = self.controller.get_transaction_summary()
        income_in_display = convert_currency(summary['income'], BASE_CURRENCY, self.display_currency)
        expense_in_display = convert_currency(summary['expense'], BASE_CURRENCY, self.display_currency)
        
        income_label = self.income_card.findChild(QLabel, "value")
        if income_label:
            income_label.setText(f"{symbol}{income_in_display:,.2f}")
        
        expense_label = self.expense_card.findChild(QLabel, "value")
        if expense_label:
            expense_label.setText(f"{symbol}{expense_in_display:,.2f}")
    
    def _update_upcoming_table(self) -> None:
        """Yaklaşan ödemeler tablosunu günceller."""
        upcoming = self.controller.get_upcoming_payments()
        
        self.upcoming_table.setRowCount(len(upcoming))
        
        for row, item in enumerate(upcoming):
            date_item = QTableWidgetItem(item.planned_date.strftime("%d.%m.%Y"))
            if item.is_overdue:
                date_item.setForeground(QColor(COLORS.DANGER))
            self.upcoming_table.setItem(row, 0, date_item)
            
            desc = item.description or item.category or "-"
            self.upcoming_table.setItem(row, 1, QTableWidgetItem(desc))
            
            symbol = CURRENCIES[self.display_currency].symbol
            amount_in_display = convert_currency(item.amount, item.currency, self.display_currency)
            amount_text = f"{symbol}{amount_in_display:,.2f}"
            amount_item = QTableWidgetItem(amount_text)
            if item.is_expense:
                amount_item.setForeground(QColor(COLORS.DANGER))
            else:
                amount_item.setForeground(QColor(COLORS.SUCCESS))
            self.upcoming_table.setItem(row, 2, amount_item)
            
            type_text = t("expense") if item.is_expense else t("income")
            self.upcoming_table.setItem(row, 3, QTableWidgetItem(type_text))
    
    def _update_recent_table(self) -> None:
        """Son işlemler tablosunu günceller."""
        transactions = self.controller.get_recent_transactions(10)
        accounts = {a.id: a for a in self.controller.get_all_accounts()}
        
        self.recent_table.setRowCount(len(transactions))
        
        for row, trans in enumerate(transactions):
            date_str = trans.transaction_date.strftime("%d.%m.%Y")
            self.recent_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            account = accounts.get(trans.account_id)
            account_name = account.name if account else "-"
            self.recent_table.setItem(row, 1, QTableWidgetItem(account_name))
            
            self.recent_table.setItem(row, 2, QTableWidgetItem(trans.category or "-"))
            
            self.recent_table.setItem(row, 3, QTableWidgetItem(trans.description or "-"))
            
            symbol = CURRENCIES[self.display_currency].symbol
            amount_in_display = convert_currency(trans.amount, trans.currency, self.display_currency)
            if trans.is_income:
                amount_text = f"+{symbol}{amount_in_display:,.2f}"
                color = COLORS.SUCCESS
            else:
                amount_text = f"-{symbol}{amount_in_display:,.2f}"
                color = COLORS.DANGER
            
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setForeground(QColor(color))
            self.recent_table.setItem(row, 4, amount_item)
