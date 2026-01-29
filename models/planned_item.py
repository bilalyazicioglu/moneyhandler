"""
Planlanan İşlem (PlannedItem) Modeli ve Repository

Bu modül beklenen/planlanan işlem veri sınıfını ve
veritabanı işlemlerini içerir. Planlanan işlemler gerçekleştir
butonu ile gerçek işlemlere dönüştürülebilir.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

from config import TransactionType
from data.database import get_database


@dataclass
class PlannedItem:
    """
    Planlanan/Beklenen İşlem veri sınıfı.
    
    Attributes:
        id: Benzersiz kimlik
        account_id: İlişkili hesap ID'si
        transaction_type: İşlem tipi ('income' veya 'expense')
        amount: Planlanan tutar
        currency: Para birimi kodu
        category: İşlem kategorisi
        description: Açıklama
        planned_date: Planlanan tarih
        is_recurring: Tekrarlanan mı?
        recurrence_period: Tekrar periyodu ('daily', 'weekly', 'monthly', 'yearly')
        created_at: Kayıt oluşturulma tarihi
    """
    account_id: int
    transaction_type: str
    amount: float
    planned_date: date
    currency: str = "TRY"
    category: str = ""
    description: str = ""
    is_recurring: bool = False
    recurrence_period: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Veri doğrulama."""
        if self.transaction_type not in (TransactionType.INCOME, TransactionType.EXPENSE):
            raise ValueError(f"Geçersiz işlem tipi: {self.transaction_type}")
        if self.amount < 0:
            raise ValueError("İşlem tutarı negatif olamaz")
    
    @property
    def is_income(self) -> bool:
        """İşlemin gelir olup olmadığını döndürür."""
        return self.transaction_type == TransactionType.INCOME
    
    @property
    def is_expense(self) -> bool:
        """İşlemin gider olup olmadığını döndürür."""
        return self.transaction_type == TransactionType.EXPENSE
    
    @property
    def is_overdue(self) -> bool:
        """Vadesi geçmiş mi kontrolü."""
        return self.planned_date < date.today()
    
    @property
    def days_until(self) -> int:
        """Planlanan tarihe kalan gün sayısı."""
        return (self.planned_date - date.today()).days


class PlannedItemRepository:
    """
    Planlanan işlem veritabanı işlemleri repository sınıfı.
    """
    
    def __init__(self) -> None:
        """Repository başlatıcısı."""
        self._db = get_database()
    
    def create(self, item: PlannedItem) -> PlannedItem:
        """
        Yeni bir planlanan işlem oluşturur.
        
        Args:
            item: Oluşturulacak planlanan işlem nesnesi
            
        Returns:
            ID atanmış planlanan işlem nesnesi
        """
        query = """
            INSERT INTO planned_items 
            (account_id, transaction_type, amount, currency, category, 
             description, planned_date, is_recurring, recurrence_period)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._db.execute(
            query,
            (
                item.account_id,
                item.transaction_type,
                item.amount,
                item.currency,
                item.category,
                item.description,
                item.planned_date.isoformat(),
                1 if item.is_recurring else 0,
                item.recurrence_period
            )
        )
        item.id = cursor.lastrowid
        return item
    
    def get_all(self) -> List[PlannedItem]:
        """
        Tüm planlanan işlemleri tarihe göre sıralı getirir.
        
        Returns:
            Planlanan işlem listesi
        """
        query = "SELECT * FROM planned_items ORDER BY planned_date ASC"
        rows = self._db.fetch_all(query)
        return [self._row_to_planned_item(row) for row in rows]
    
    def get_by_id(self, item_id: int) -> Optional[PlannedItem]:
        """
        ID'ye göre planlanan işlem getirir.
        
        Args:
            item_id: Planlanan işlem ID'si
            
        Returns:
            PlannedItem nesnesi veya None
        """
        query = "SELECT * FROM planned_items WHERE id = ?"
        row = self._db.fetch_one(query, (item_id,))
        return self._row_to_planned_item(row) if row else None
    
    def get_upcoming(self, days: int = 7) -> List[PlannedItem]:
        """
        Yaklaşan planlanan işlemleri getirir (Dashboard için).
        
        Args:
            days: Kaç gün ileriye bakılacak
            
        Returns:
            Yaklaşan planlanan işlemler listesi
        """
        end_date = date.today() + timedelta(days=days)
        query = """
            SELECT * FROM planned_items 
            WHERE planned_date <= ?
            ORDER BY planned_date ASC
        """
        rows = self._db.fetch_all(query, (end_date.isoformat(),))
        return [self._row_to_planned_item(row) for row in rows]
    
    def get_overdue(self) -> List[PlannedItem]:
        """
        Vadesi geçmiş planlanan işlemleri getirir.
        
        Returns:
            Vadesi geçmiş işlemler listesi
        """
        today = date.today()
        query = """
            SELECT * FROM planned_items 
            WHERE planned_date < ?
            ORDER BY planned_date ASC
        """
        rows = self._db.fetch_all(query, (today.isoformat(),))
        return [self._row_to_planned_item(row) for row in rows]
    
    def update(self, item: PlannedItem) -> bool:
        """
        Planlanan işlem bilgilerini günceller.
        
        Args:
            item: Güncellenecek planlanan işlem nesnesi
            
        Returns:
            Güncelleme başarılı ise True
        """
        if item.id is None:
            raise ValueError("Planlanan işlem ID'si belirtilmeli")
        
        query = """
            UPDATE planned_items
            SET account_id = ?, transaction_type = ?, amount = ?,
                currency = ?, category = ?, description = ?, 
                planned_date = ?, is_recurring = ?, recurrence_period = ?
            WHERE id = ?
        """
        cursor = self._db.execute(
            query,
            (
                item.account_id,
                item.transaction_type,
                item.amount,
                item.currency,
                item.category,
                item.description,
                item.planned_date.isoformat(),
                1 if item.is_recurring else 0,
                item.recurrence_period,
                item.id
            )
        )
        return cursor.rowcount > 0
    
    def delete(self, item_id: int) -> bool:
        """
        Planlanan işlemi siler.
        
        Args:
            item_id: Silinecek planlanan işlem ID'si
            
        Returns:
            Silme başarılı ise True
        """
        query = "DELETE FROM planned_items WHERE id = ?"
        cursor = self._db.execute(query, (item_id,))
        return cursor.rowcount > 0
    
    def get_total_upcoming_expenses(self, days: int = 30) -> float:
        """
        Yaklaşan giderlerin toplamını hesaplar.
        
        Args:
            days: Kaç gün ileriye bakılacak
            
        Returns:
            Toplam beklenen gider tutarı
        """
        end_date = date.today() + timedelta(days=days)
        query = """
            SELECT SUM(amount) as total
            FROM planned_items 
            WHERE transaction_type = 'expense' AND planned_date <= ?
        """
        row = self._db.fetch_one(query, (end_date.isoformat(),))
        return row["total"] if row and row["total"] else 0.0
    
    def _row_to_planned_item(self, row) -> PlannedItem:
        """
        Veritabanı satırını PlannedItem nesnesine dönüştürür.
        
        Args:
            row: sqlite3.Row nesnesi
            
        Returns:
            PlannedItem nesnesi
        """
        plan_date = row["planned_date"]
        if isinstance(plan_date, str):
            plan_date = date.fromisoformat(plan_date)
        
        return PlannedItem(
            id=row["id"],
            account_id=row["account_id"],
            transaction_type=row["transaction_type"],
            amount=row["amount"],
            currency=row["currency"],
            category=row["category"] or "",
            description=row["description"] or "",
            planned_date=plan_date,
            is_recurring=bool(row["is_recurring"]),
            recurrence_period=row["recurrence_period"],
            created_at=row["created_at"]
        )
