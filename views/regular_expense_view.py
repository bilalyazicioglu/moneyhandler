"""
Düzenli Gider View Modülü

Düzenli gider yönetimi ekranı widget'ı.
Kira, fatura, abonelik gibi aylık giderlerin takibi için kullanılır.
"""

from datetime import date
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
    QFrame
)
from PyQt6.QtGui import QColor

from config import COLORS, CURRENCIES, t
from models.regular_expense import RegularExpense, ExpensePayment, RegularExpenseRepository
from views.forms import RegularExpenseDialog, RecordExpensePaymentDialog

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class RegularExpenseView(QWidget):
    """
    Düzenli gider yönetimi ekranı widget'ı.
    
    Signals:
        expense_changed: Düzenli gider değiştiğinde
        payment_recorded: Ödeme kaydedildiğinde
    """
    
    expense_changed = pyqtSignal()
    payment_recorded = pyqtSignal()
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._selected_expense: Optional[RegularExpense] = None
        self._repo = RegularExpenseRepository()
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel(t("regular_expense_tab"))
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel(t("pending_expenses"))
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        self.add_btn = QPushButton(t("new_regular_expense"))
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
        self.add_btn.clicked.connect(self._on_add_expense)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", t("expense_name"), t("category"), t("amount"), t("table_expected_day"), t("table_avg_delay")
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 100)
        
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        splitter.addWidget(self.table)
        
        self.detail_panel = self._create_detail_panel()
        splitter.addWidget(self.detail_panel)
        
        splitter.setSizes([650, 350])
        layout.addWidget(splitter)
    
    def _create_detail_panel(self) -> QFrame:
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
        
        self.detail_title = QLabel(t("regular_expense_details"))
        self.detail_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS.TEXT_PRIMARY};
            border: none;
        """)
        layout.addWidget(self.detail_title)
        
        stats_layout = QHBoxLayout()
        
        self.stat_amount = self._create_stat_card(t("amount"), "₺0")
        stats_layout.addWidget(self.stat_amount)
        
        self.stat_day = self._create_stat_card(t("expected_day"), "-")
        stats_layout.addWidget(self.stat_day)
        
        self.stat_delay = self._create_stat_card(t("avg_delay"), "-")
        stats_layout.addWidget(self.stat_delay)
        
        layout.addLayout(stats_layout)
        
        history_label = QLabel(t("payment_history"))
        history_label.setStyleSheet(f"""
            color: {COLORS.TEXT_SECONDARY};
            font-size: 13px;
            font-weight: 600;
            border: none;
            margin-top: 8px;
        """)
        layout.addWidget(history_label)
        
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(4)
        self.payment_table.setHorizontalHeaderLabels([
            t("expected_day"), t("actual_date"), t("amount"), t("delay_status")
        ])
        
        payment_header = self.payment_table.horizontalHeader()
        payment_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        payment_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        payment_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        payment_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.payment_table.setColumnWidth(0, 90)
        self.payment_table.setColumnWidth(1, 90)
        self.payment_table.setColumnWidth(2, 90)
        
        self.payment_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.payment_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payment_table.verticalHeader().setVisible(False)
        self.payment_table.setShowGrid(False)
        self.payment_table.setMaximumHeight(200)
        
        layout.addWidget(self.payment_table)
        
        self.no_payments_label = QLabel(t("no_payments_yet"))
        self.no_payments_label.setStyleSheet(f"""
            color: {COLORS.TEXT_MUTED};
            font-size: 13px;
            border: none;
            padding: 20px;
        """)
        self.no_payments_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.no_payments_label)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        self.record_btn = QPushButton(t("record_expense"))
        self.record_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_LIGHT};
            }}
        """)
        self.record_btn.clicked.connect(self._on_record_payment)
        btn_layout.addWidget(self.record_btn)
        
        self.edit_btn = QPushButton(t("save"))
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        self.edit_btn.clicked.connect(self._on_edit_expense)
        btn_layout.addWidget(self.edit_btn)
        
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
        self.delete_btn.clicked.connect(self._on_delete_expense)
        btn_layout.addWidget(self.delete_btn)
        
        layout.addLayout(btn_layout)
        
        self._set_detail_enabled(False)
        
        return panel
    
    def _create_stat_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 12, 12, 12)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {COLORS.TEXT_SECONDARY};
            font-size: 11px;
            border: none;
        """)
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setObjectName("value")
        value_widget.setStyleSheet(f"""
            color: {COLORS.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 700;
            border: none;
        """)
        layout.addWidget(value_widget)
        
        return card
    
    def _set_detail_enabled(self, enabled: bool) -> None:
        self.record_btn.setEnabled(enabled)
        self.edit_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        
        if not enabled:
            self.detail_title.setText(t("regular_expense_details"))
            self.stat_amount.findChild(QLabel, "value").setText("₺0")
            self.stat_day.findChild(QLabel, "value").setText("-")
            self.stat_delay.findChild(QLabel, "value").setText("-")
            self.payment_table.setRowCount(0)
            self.payment_table.hide()
            self.no_payments_label.show()
    
    def _on_selection_changed(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_expense = None
            self._set_detail_enabled(False)
            return
        
        row = selected_rows[0].row()
        expense_id = int(self.table.item(row, 0).text())
        
        self._selected_expense = self._repo.get_by_id(expense_id)
        
        if self._selected_expense:
            self._load_detail(self._selected_expense)
            self._set_detail_enabled(True)
    
    def _load_detail(self, expense: RegularExpense) -> None:
        self.detail_title.setText(expense.name)
        
        symbol = CURRENCIES[expense.currency].symbol
        self.stat_amount.findChild(QLabel, "value").setText(f"{symbol}{expense.amount:,.2f}")
        self.stat_day.findChild(QLabel, "value").setText(str(expense.expected_day))
        
        avg_delay = self._repo.get_average_delay(expense.id)
        if avg_delay < 0:
            delay_text = f"-{abs(avg_delay):.1f}"
            delay_color = COLORS.SUCCESS
        elif avg_delay == 0:
            delay_text = t("on_time")
            delay_color = COLORS.INFO
        else:
            delay_text = f"{avg_delay:.1f} {t('days_late')}"
            delay_color = COLORS.WARNING if avg_delay <= 3 else COLORS.DANGER
        
        delay_label = self.stat_delay.findChild(QLabel, "value")
        delay_label.setText(delay_text)
        delay_label.setStyleSheet(f"""
            color: {delay_color};
            font-size: 16px;
            font-weight: 700;
            border: none;
        """)
        
        payments = self._repo.get_payments(expense.id, limit=6)
        
        if payments:
            self.payment_table.show()
            self.no_payments_label.hide()
            self.payment_table.setRowCount(len(payments))
            
            for row, payment in enumerate(payments):
                expected_item = QTableWidgetItem(payment.expected_date.strftime("%d.%m.%Y"))
                self.payment_table.setItem(row, 0, expected_item)
                
                actual_item = QTableWidgetItem(payment.actual_date.strftime("%d.%m.%Y"))
                self.payment_table.setItem(row, 1, actual_item)
                
                amount_item = QTableWidgetItem(f"{symbol}{payment.amount:,.2f}")
                self.payment_table.setItem(row, 2, amount_item)
                
                delay = payment.delay_days
                if delay < 0:
                    status_text = f"{abs(delay)} {t('days_early')}"
                    color = COLORS.SUCCESS
                elif delay == 0:
                    status_text = t('on_time')
                    color = COLORS.INFO
                elif delay <= 3:
                    status_text = f"{delay} {t('days_late')}"
                    color = COLORS.WARNING
                else:
                    status_text = f"{delay} {t('days_late')}"
                    color = COLORS.DANGER
                
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QColor(color))
                self.payment_table.setItem(row, 3, status_item)
        else:
            self.payment_table.hide()
            self.no_payments_label.show()
    
    def _get_category_text(self, category: str) -> str:
        mapping = {
            "rent": t("category_rent"),
            "utilities": t("category_utilities"),
            "subscription": t("category_subscription"),
            "insurance": t("category_insurance"),
            "other": t("category_other_expense"),
        }
        return mapping.get(category, category)
    
    def refresh(self) -> None:
        expenses = self._repo.get_all(active_only=True)
        
        self.table.setRowCount(len(expenses))
        
        for row, expense in enumerate(expenses):
            id_item = QTableWidgetItem(str(expense.id))
            self.table.setItem(row, 0, id_item)
            
            name_item = QTableWidgetItem(expense.name)
            self.table.setItem(row, 1, name_item)
            
            category_text = self._get_category_text(expense.category)
            category_item = QTableWidgetItem(category_text)
            self.table.setItem(row, 2, category_item)
            
            symbol = CURRENCIES[expense.currency].symbol
            amount_text = f"{symbol}{expense.amount:,.2f}"
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setForeground(QColor(COLORS.SUCCESS))
            self.table.setItem(row, 3, amount_item)
            
            day_item = QTableWidgetItem(str(expense.expected_day))
            day_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, day_item)
            
            avg_delay = self._repo.get_average_delay(expense.id)
            if avg_delay < 0:
                delay_text = f"-{abs(avg_delay):.1f}"
                delay_color = COLORS.SUCCESS
            elif avg_delay == 0:
                delay_text = "0"
                delay_color = COLORS.INFO
            else:
                delay_text = f"+{avg_delay:.1f}"
                delay_color = COLORS.DANGER if avg_delay > 3 else COLORS.WARNING
            
            delay_item = QTableWidgetItem(delay_text)
            delay_item.setForeground(QColor(delay_color))
            delay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, delay_item)
    
    def _on_add_expense(self) -> None:
        accounts = self.controller.get_all_accounts()
        if not accounts:
            QMessageBox.warning(
                self,
                t("warning"),
                t("msg_create_account_first")
            )
            return
        
        dialog = RegularExpenseDialog(self, accounts=accounts)
        if dialog.exec():
            expense = dialog.get_data()
            self._repo.create(expense)
            self.refresh()
            self.expense_changed.emit()
    
    def _on_edit_expense(self) -> None:
        if not self._selected_expense:
            return
        
        accounts = self.controller.get_all_accounts()
        dialog = RegularExpenseDialog(self, self._selected_expense, accounts)
        if dialog.exec():
            updated = dialog.get_data()
            self._repo.update(updated)
            self.refresh()
            self.expense_changed.emit()
    
    def _on_delete_expense(self) -> None:
        if not self._selected_expense:
            return
        
        reply = QMessageBox.question(
            self,
            t("warning"),
            t("msg_delete_regular_expense"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._repo.delete(self._selected_expense.id)
            self._selected_expense = None
            self._set_detail_enabled(False)
            self.refresh()
            self.expense_changed.emit()
    
    def _on_record_payment(self) -> None:
        if not self._selected_expense:
            return
        
        dialog = RecordExpensePaymentDialog(self, self._selected_expense)
        if dialog.exec():
            payment = dialog.get_data()
            self._repo.record_payment(payment)
            self._load_detail(self._selected_expense)
            
            QMessageBox.information(
                self,
                t("success"),
                t("expense_payment_recorded")
            )
            self.payment_recorded.emit()
