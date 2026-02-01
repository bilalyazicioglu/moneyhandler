"""
Düzenli Gider (RegularExpense) Modeli ve Repository

Bu modül düzenli gider tanımlarını ve ödeme geçmişini yönetir.
Kira, fatura, abonelik gibi aylık giderlerin takibi için kullanılır.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from data.database import get_database


class ExpenseCategory:
    """Düzenli gider kategori sabitleri."""
    RENT = "rent"
    UTILITIES = "utilities"
    SUBSCRIPTION = "subscription"
    INSURANCE = "insurance"
    OTHER = "other"


@dataclass
class RegularExpense:
    """Düzenli gider tanımı veri sınıfı."""
    account_id: int
    name: str
    category: str
    amount: float
    expected_day: int
    currency: str = "TRY"
    description: str = ""
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        if not 1 <= self.expected_day <= 31:
            raise ValueError(f"Beklenen gün 1-31 arasında olmalı: {self.expected_day}")
        if self.amount < 0:
            raise ValueError("Tutar negatif olamaz")
    
    def get_expected_date_for_month(self, year: int, month: int) -> date:
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        day = min(self.expected_day, last_day)
        return date(year, month, day)


@dataclass
class ExpensePayment:
    """Gerçekleşen ödeme kaydı veri sınıfı."""
    regular_expense_id: int
    expected_date: date
    actual_date: date
    amount: float
    currency: str = "TRY"
    notes: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    @property
    def delay_days(self) -> int:
        return (self.actual_date - self.expected_date).days
    
    @property
    def is_early(self) -> bool:
        return self.delay_days < 0
    
    @property
    def is_on_time(self) -> bool:
        return self.delay_days == 0
    
    @property
    def is_late(self) -> bool:
        return self.delay_days > 0


class RegularExpenseRepository:
    """Düzenli gider veritabanı işlemleri repository sınıfı."""
    
    def __init__(self) -> None:
        self._db = get_database()
    
    def create(self, expense: RegularExpense) -> RegularExpense:
        query = """
            INSERT INTO regular_expenses 
            (account_id, name, category, amount, currency, expected_day, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._db.execute(
            query,
            (
                expense.account_id,
                expense.name,
                expense.category,
                expense.amount,
                expense.currency,
                expense.expected_day,
                expense.description,
                1 if expense.is_active else 0
            )
        )
        expense.id = cursor.lastrowid
        return expense
    
    def get_all(self, active_only: bool = True) -> List[RegularExpense]:
        if active_only:
            query = "SELECT * FROM regular_expenses WHERE is_active = 1 ORDER BY expected_day ASC"
        else:
            query = "SELECT * FROM regular_expenses ORDER BY expected_day ASC"
        rows = self._db.fetch_all(query)
        return [self._row_to_regular_expense(row) for row in rows]
    
    def get_by_id(self, expense_id: int) -> Optional[RegularExpense]:
        query = "SELECT * FROM regular_expenses WHERE id = ?"
        row = self._db.fetch_one(query, (expense_id,))
        return self._row_to_regular_expense(row) if row else None
    
    def update(self, expense: RegularExpense) -> bool:
        if expense.id is None:
            raise ValueError("Düzenli gider ID'si belirtilmeli")
        
        query = """
            UPDATE regular_expenses
            SET account_id = ?, name = ?, category = ?, amount = ?,
                currency = ?, expected_day = ?, description = ?, is_active = ?
            WHERE id = ?
        """
        cursor = self._db.execute(
            query,
            (
                expense.account_id,
                expense.name,
                expense.category,
                expense.amount,
                expense.currency,
                expense.expected_day,
                expense.description,
                1 if expense.is_active else 0,
                expense.id
            )
        )
        return cursor.rowcount > 0
    
    def delete(self, expense_id: int) -> bool:
        query = "DELETE FROM regular_expenses WHERE id = ?"
        cursor = self._db.execute(query, (expense_id,))
        return cursor.rowcount > 0
    
    def record_payment(self, payment: ExpensePayment) -> ExpensePayment:
        delay = payment.delay_days
        query = """
            INSERT INTO expense_payments 
            (regular_expense_id, expected_date, actual_date, amount, currency, delay_days, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._db.execute(
            query,
            (
                payment.regular_expense_id,
                payment.expected_date.isoformat(),
                payment.actual_date.isoformat(),
                payment.amount,
                payment.currency,
                delay,
                payment.notes
            )
        )
        payment.id = cursor.lastrowid
        return payment
    
    def get_payments(self, expense_id: int, limit: int = 12) -> List[ExpensePayment]:
        query = """
            SELECT * FROM expense_payments 
            WHERE regular_expense_id = ?
            ORDER BY actual_date DESC
            LIMIT ?
        """
        rows = self._db.fetch_all(query, (expense_id, limit))
        return [self._row_to_expense_payment(row) for row in rows]
    
    def get_average_delay(self, expense_id: int) -> float:
        query = """
            SELECT AVG(delay_days) as avg_delay
            FROM expense_payments
            WHERE regular_expense_id = ?
        """
        row = self._db.fetch_one(query, (expense_id,))
        return row["avg_delay"] if row and row["avg_delay"] is not None else 0.0
    
    def get_pending_this_month(self) -> List[RegularExpense]:
        today = date.today()
        first_day = date(today.year, today.month, 1)
        
        query = """
            SELECT re.* FROM regular_expenses re
            WHERE re.is_active = 1
            AND NOT EXISTS (
                SELECT 1 FROM expense_payments ep
                WHERE ep.regular_expense_id = re.id
                AND ep.expected_date >= ?
            )
        """
        rows = self._db.fetch_all(query, (first_day.isoformat(),))
        return [self._row_to_regular_expense(row) for row in rows]
    
    def _row_to_regular_expense(self, row) -> RegularExpense:
        return RegularExpense(
            id=row["id"],
            account_id=row["account_id"],
            name=row["name"],
            category=row["category"],
            amount=row["amount"],
            currency=row["currency"],
            expected_day=row["expected_day"],
            description=row["description"] or "",
            is_active=bool(row["is_active"]),
            created_at=row["created_at"]
        )
    
    def _row_to_expense_payment(self, row) -> ExpensePayment:
        expected = row["expected_date"]
        actual = row["actual_date"]
        
        if isinstance(expected, str):
            expected = date.fromisoformat(expected)
        if isinstance(actual, str):
            actual = date.fromisoformat(actual)
        
        return ExpensePayment(
            id=row["id"],
            regular_expense_id=row["regular_expense_id"],
            expected_date=expected,
            actual_date=actual,
            amount=row["amount"],
            currency=row["currency"],
            notes=row["notes"] or "",
            created_at=row["created_at"]
        )
