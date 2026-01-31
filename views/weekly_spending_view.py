"""
Haftalık Harcama View Modülü

Haftalık harcama ve gelir özeti - takvim görünümü.
Pazartesi-Pazar arası işlemleri gösterir.
"""

from datetime import date, timedelta
from typing import TYPE_CHECKING, List, Dict, Set

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QPushButton
)

from config import (
    COLORS, 
    CURRENCIES, 
    BASE_CURRENCY, 
    convert_to_base_currency,
    convert_currency,
    t,
    get_day_names_short
)

if TYPE_CHECKING:
    from controllers.main_controller import MainController





class DayColumnWidget(QFrame):
    """Tek bir gün için sütun widget'ı."""
    
    def __init__(
        self, 
        day_name: str,
        day_date: date,
        is_today: bool,
        transactions: List,
        display_currency: str,
        parent=None
    ):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.BG_ELEVATED if is_today else COLORS.BG_CARD};
                border: 1px solid {COLORS.PRIMARY if is_today else COLORS.BORDER};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        
        day_label = QLabel(day_name)
        day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {COLORS.PRIMARY if is_today else COLORS.TEXT_PRIMARY};
        """)
        header_layout.addWidget(day_label)
        
        date_label = QLabel(str(day_date.day))
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS.PRIMARY if is_today else COLORS.TEXT_PRIMARY};
        """)
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {COLORS.BORDER};")
        layout.addWidget(separator)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QWidget { background: transparent; }
        """)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 4, 0, 4)
        content_layout.setSpacing(4)
        
        symbol = CURRENCIES[display_currency].symbol
        
        if transactions:
            for trans in transactions:
                amount_in_display = convert_currency(
                    trans.amount, 
                    trans.currency, 
                    display_currency
                )
                
                trans_frame = QFrame()
                trans_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS.BG_INPUT};
                        border-radius: 4px;
                        padding: 2px;
                    }}
                """)
                
                trans_layout = QVBoxLayout(trans_frame)
                trans_layout.setContentsMargins(6, 4, 6, 4)
                trans_layout.setSpacing(2)
                
                category = trans.category or t("general")
                cat_label = QLabel(category)
                cat_label.setStyleSheet(f"""
                    font-size: 10px;
                    color: {COLORS.TEXT_SECONDARY};
                """)
                cat_label.setWordWrap(True)
                trans_layout.addWidget(cat_label)
                
                if trans.is_income:
                    amount_text = f"+{symbol}{amount_in_display:,.2f}"
                    color = COLORS.SUCCESS
                else:
                    amount_text = f"-{symbol}{amount_in_display:,.2f}"
                    color = COLORS.DANGER
                
                amount_label = QLabel(amount_text)
                amount_label.setStyleSheet(f"""
                    font-size: 11px;
                    font-weight: 600;
                    color: {color};
                """)
                trans_layout.addWidget(amount_label)
                
                content_layout.addWidget(trans_frame)
        else:
            empty_label = QLabel("-")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS.TEXT_MUTED};
            """)
            content_layout.addWidget(empty_label)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)


class WeeklySpendingView(QWidget):
    """
    Haftalık harcama ekranı - takvim görünümü.
    
    Haftanın her günü için sütunlar halinde gelir/gider gösterir.
    """
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.display_currency = BASE_CURRENCY
        self.selected_categories: Set[str] = set()
        self.category_checkboxes: Dict[str, QCheckBox] = {}
        self._init_current_week()
        self._setup_ui()
    
    def _init_current_week(self) -> None:
        """Mevcut haftayı başlatır."""
        today = date.today()
        self.current_week_start = today - timedelta(days=today.weekday())
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel(t("weekly_title"))
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
        """)
        title_layout.addWidget(title)
        
        self.date_range_label = QLabel(t("this_week"))
        self.date_range_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS.TEXT_SECONDARY};
        """)
        title_layout.addWidget(self.date_range_label)
        
        header_layout.addLayout(title_layout)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(4)
        
        self.prev_week_btn = QPushButton("❮")
        self.prev_week_btn.setFixedSize(36, 36)
        self.prev_week_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_week_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                border-radius: 8px;
                color: {COLORS.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                padding: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
                border-color: {COLORS.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.PRIMARY};
            }}
        """)
        self.prev_week_btn.clicked.connect(self._go_to_prev_week)
        nav_layout.addWidget(self.prev_week_btn)
        
        self.today_btn = QPushButton(t("today"))
        self.today_btn.setFixedHeight(36)
        self.today_btn.setMinimumWidth(80)
        self.today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                border-radius: 8px;
                color: {COLORS.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
                border-color: {COLORS.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.PRIMARY};
            }}
        """)
        self.today_btn.clicked.connect(self._go_to_today)
        nav_layout.addWidget(self.today_btn)
        
        self.next_week_btn = QPushButton("❯")
        self.next_week_btn.setFixedSize(36, 36)
        self.next_week_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_week_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                border-radius: 8px;
                color: {COLORS.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                padding: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
                border-color: {COLORS.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.PRIMARY};
            }}
        """)
        self.next_week_btn.clicked.connect(self._go_to_next_week)
        nav_layout.addWidget(self.next_week_btn)
        
        header_layout.addStretch()
        header_layout.addLayout(nav_layout)
        header_layout.addSpacing(16)
        
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
        
        header_layout.addLayout(currency_layout)
        layout.addLayout(header_layout)
        
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)
        
        self.avg_expense_card = self._create_summary_card(
            t("daily_avg_expense"),
            "₺0.00",
            COLORS.DANGER
        )
        summary_layout.addWidget(self.avg_expense_card)
        
        self.avg_income_card = self._create_summary_card(
            t("daily_avg_income"),
            "₺0.00",
            COLORS.SUCCESS
        )
        summary_layout.addWidget(self.avg_income_card)
        
        self.weekly_expense_card = self._create_summary_card(
            t("weekly_expense"),
            "₺0.00",
            COLORS.DANGER
        )
        summary_layout.addWidget(self.weekly_expense_card)
        
        self.weekly_income_card = self._create_summary_card(
            t("weekly_income"),
            "₺0.00",
            COLORS.SUCCESS
        )
        summary_layout.addWidget(self.weekly_income_card)
        
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        self.category_group = QGroupBox(t("category_filter"))
        self.category_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS.BG_CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                color: {COLORS.TEXT_SECONDARY};
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                font-size: 12px;
            }}
        """)
        
        category_scroll = QScrollArea()
        category_scroll.setWidgetResizable(True)
        category_scroll.setMaximumHeight(80)
        category_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
        """)
        
        self.category_container = QWidget()
        self.category_layout = QHBoxLayout(self.category_container)
        self.category_layout.setContentsMargins(8, 4, 8, 4)
        self.category_layout.setSpacing(16)
        
        category_scroll.setWidget(self.category_container)
        
        group_layout = QVBoxLayout(self.category_group)
        group_layout.setContentsMargins(8, 16, 8, 8)
        group_layout.addWidget(category_scroll)
        
        layout.addWidget(self.category_group)
        
        self.calendar_container = QFrame()
        self.calendar_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.BG_DARK};
                border: 1px solid {COLORS.BORDER};
                border-radius: 12px;
            }}
        """)
        self.calendar_layout = QHBoxLayout(self.calendar_container)
        self.calendar_layout.setContentsMargins(12, 12, 12, 12)
        self.calendar_layout.setSpacing(8)
        
        layout.addWidget(self.calendar_container, 1)
    
    def _create_summary_card(self, title: str, value: str, accent_color: str) -> QFrame:
        """Küçük özet kartı oluşturur."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.BG_CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 12px;
                border-left: 3px solid {accent_color};
            }}
        """)
        card.setFixedWidth(180)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS.TEXT_SECONDARY};
            font-size: 11px;
            font-weight: 500;
        """)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            color: {COLORS.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 700;
        """)
        layout.addWidget(value_label)
        
        return card
    
    def _go_to_prev_week(self) -> None:
        """Önceki haftaya geçer."""
        self.current_week_start -= timedelta(days=7)
        self.refresh()
    
    def _go_to_next_week(self) -> None:
        """Sonraki haftaya geçer."""
        self.current_week_start += timedelta(days=7)
        self.refresh()
    
    def _go_to_today(self) -> None:
        """Bugünün haftasına döner."""
        today = date.today()
        self.current_week_start = today - timedelta(days=today.weekday())
        self.refresh()
    
    def _on_currency_changed(self) -> None:
        """Para birimi değiştiğinde çağrılır."""
        self.display_currency = self.currency_combo.currentData()
        self.refresh()
    
    def _on_category_changed(self) -> None:
        """Kategori seçimi değiştiğinde çağrılır."""
        self.selected_categories = set()
        for category, checkbox in self.category_checkboxes.items():
            if checkbox.isChecked():
                self.selected_categories.add(category)
        self._update_averages()
    
    def _update_categories(self, all_categories: Set[str]) -> None:
        """Kategori checkbox'larını günceller."""
        current_categories = set(self.category_checkboxes.keys())
        
        if current_categories == all_categories:
            return
        
        while self.category_layout.count():
            item = self.category_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.category_checkboxes.clear()
        
        for category in sorted(all_categories):
            checkbox = QCheckBox(category)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {COLORS.TEXT_PRIMARY};
                    font-size: 12px;
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid {COLORS.BORDER};
                    border-radius: 4px;
                    background-color: {COLORS.BG_INPUT};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {COLORS.PRIMARY};
                    border-color: {COLORS.PRIMARY};
                }}
            """)
            checkbox.stateChanged.connect(self._on_category_changed)
            self.category_layout.addWidget(checkbox)
            self.category_checkboxes[category] = checkbox
        
        self.category_layout.addStretch()
        
        self.selected_categories = all_categories.copy()
    
    def _update_averages(self) -> None:
        """Ortalama değerlerini seçili kategorilere göre günceller."""
        week_start = self.current_week_start
        week_end = week_start + timedelta(days=6)
        
        all_transactions = self.controller.get_transactions_by_date_range(week_start, week_end)
        
        today = date.today()
        days_passed = today.weekday() + 1
        
        symbol = CURRENCIES[self.display_currency].symbol
        
        filtered_expense = 0.0
        filtered_income = 0.0
        
        for trans in all_transactions:
            category = trans.category or t(\"general\")
            if category in self.selected_categories:
                amount_in_display = convert_currency(
                    trans.amount,
                    trans.currency,
                    self.display_currency
                )
                
                if trans.is_expense:
                    filtered_expense += amount_in_display
                else:
                    filtered_income += amount_in_display
        
        avg_expense = filtered_expense / days_passed if days_passed > 0 else 0.0
        avg_income = filtered_income / days_passed if days_passed > 0 else 0.0
        
        avg_expense_label = self.avg_expense_card.findChild(QLabel, "value")
        if avg_expense_label:
            avg_expense_label.setText(f"{symbol}{avg_expense:,.2f}")
        
        avg_income_label = self.avg_income_card.findChild(QLabel, "value")
        if avg_income_label:
            avg_income_label.setText(f"{symbol}{avg_income:,.2f}")
    
    def refresh(self) -> None:
        """Haftalık verileri yeniler."""
        data = self.controller.get_weekly_spending_data_for_week(self.current_week_start)
        
        symbol = CURRENCIES[self.display_currency].symbol
        
        week_start = data['week_start']
        week_end = data['week_end']
        
        today = date.today()
        today_week_start = today - timedelta(days=today.weekday())
        is_current_week = (self.current_week_start == today_week_start)
        
        if is_current_week:
            self.date_range_label.setText(
                f"{t('this_week')} • {week_start.strftime('%d %B')} - {week_end.strftime('%d %B %Y')}"
            )
        else:
            self.date_range_label.setText(
                f"{week_start.strftime('%d %B')} - {week_end.strftime('%d %B %Y')}"
            )
        
        today = date.today()
        days_passed = today.weekday() + 1
        
        weekly_expense = 0.0
        weekly_income = 0.0
        
        all_transactions = self.controller.get_transactions_by_date_range(week_start, week_end)
        
        all_categories: Set[str] = set()
        daily_transactions: Dict[int, List] = {i: [] for i in range(7)}
        
        for trans in all_transactions:
            day_index = trans.transaction_date.weekday()
            if 0 <= day_index <= 6:
                daily_transactions[day_index].append(trans)
                
                category = trans.category or t("general")
                all_categories.add(category)
                
                amount_in_display = convert_currency(
                    trans.amount,
                    trans.currency,
                    self.display_currency
                )
                
                if trans.is_expense:
                    weekly_expense += amount_in_display
                else:
                    weekly_income += amount_in_display
        
        self._update_categories(all_categories)
        
        avg_expense = weekly_expense / days_passed if days_passed > 0 else 0.0
        avg_income = weekly_income / days_passed if days_passed > 0 else 0.0
        
        avg_expense_label = self.avg_expense_card.findChild(QLabel, "value")
        if avg_expense_label:
            avg_expense_label.setText(f"{symbol}{avg_expense:,.2f}")
        
        avg_income_label = self.avg_income_card.findChild(QLabel, "value")
        if avg_income_label:
            avg_income_label.setText(f"{symbol}{avg_income:,.2f}")
        
        weekly_expense_label = self.weekly_expense_card.findChild(QLabel, "value")
        if weekly_expense_label:
            weekly_expense_label.setText(f"{symbol}{weekly_expense:,.2f}")
        
        weekly_income_label = self.weekly_income_card.findChild(QLabel, "value")
        if weekly_income_label:
            weekly_income_label.setText(f"{symbol}{weekly_income:,.2f}")
        
        while self.calendar_layout.count():
            item = self.calendar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for day_index in range(7):
            day_date = week_start + timedelta(days=day_index)
            is_today = day_date == today
            transactions = daily_transactions.get(day_index, [])
            
            day_widget = DayColumnWidget(
                day_name=get_day_names_short()[day_index],
                day_date=day_date,
                is_today=is_today,
                transactions=transactions,
                display_currency=self.display_currency
            )
            day_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
            self.calendar_layout.addWidget(day_widget)
