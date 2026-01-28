"""
İşlem (Transaction) Modeli ve Repository

Bu modül gerçekleşen işlem (gelir/gider) veri sınıfını ve
veritabanı işlemlerini içerir.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from config import TransactionType
from data.database import get_database


@dataclass
class Transaction:
    """
    İşlem (Gelir/Gider) veri sınıfı.
    
    Attributes:
        id: Benzersiz işlem kimliği
        account_id: İlişkili hesap ID'si
        transaction_type: İşlem tipi ('income' veya 'expense')
        amount: İşlem tutarı (pozitif değer)
        currency: Para birimi kodu
        category: İşlem kategorisi
        description: İşlem açıklaması
        transaction_date: İşlem tarihi
        created_at: Kayıt oluşturulma tarihi
    """
    account_id: int
    transaction_type: str
    amount: float
    transaction_date: date
    currency: str = "TRY"
    category: str = ""
    description: str = ""
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
    def signed_amount(self) -> float:
        """İşaretli tutarı döndürür (gider için negatif)."""
        return self.amount if self.is_income else -self.amount


class TransactionRepository:
    """
    İşlem veritabanı işlemleri repository sınıfı.
    
    CRUD operasyonları ve filtreleme için metodlar sağlar.
    """
    
    def __init__(self) -> None:
        """Repository başlatıcısı."""
        self._db = get_database()
    
    def create(self, transaction: Transaction) -> Transaction:
        """
        Yeni bir işlem oluşturur.
        
        Args:
            transaction: Oluşturulacak işlem nesnesi
            
        Returns:
            ID atanmış işlem nesnesi
        """
        query = """
            INSERT INTO transactions 
            (account_id, transaction_type, amount, currency, category, description, transaction_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._db.execute(
            query,
            (
                transaction.account_id,
                transaction.transaction_type,
                transaction.amount,
                transaction.currency,
                transaction.category,
                transaction.description,
                transaction.transaction_date.isoformat()
            )
        )
        transaction.id = cursor.lastrowid
        return transaction
    
    def get_all(self) -> List[Transaction]:
        """
        Tüm işlemleri tarihe göre sıralı getirir.
        
        Returns:
            İşlem listesi (en yeni ilk)
        """
        query = "SELECT * FROM transactions ORDER BY transaction_date DESC, id DESC"
        rows = self._db.fetch_all(query)
        return [self._row_to_transaction(row) for row in rows]
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        ID'ye göre işlem getirir.
        
        Args:
            transaction_id: İşlem ID'si
            
        Returns:
            İşlem nesnesi veya None
        """
        query = "SELECT * FROM transactions WHERE id = ?"
        row = self._db.fetch_one(query, (transaction_id,))
        return self._row_to_transaction(row) if row else None
    
    def get_by_account(self, account_id: int) -> List[Transaction]:
        """
        Hesaba göre işlemleri getirir.
        
        Args:
            account_id: Hesap ID'si
            
        Returns:
            İşlem listesi
        """
        query = """
            SELECT * FROM transactions 
            WHERE account_id = ? 
            ORDER BY transaction_date DESC, id DESC
        """
        rows = self._db.fetch_all(query, (account_id,))
        return [self._row_to_transaction(row) for row in rows]
    
    def get_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """
        Tarih aralığına göre işlemleri getirir.
        
        Args:
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi
            
        Returns:
            İşlem listesi
        """
        query = """
            SELECT * FROM transactions 
            WHERE transaction_date BETWEEN ? AND ?
            ORDER BY transaction_date DESC, id DESC
        """
        rows = self._db.fetch_all(
            query,
            (start_date.isoformat(), end_date.isoformat())
        )
        return [self._row_to_transaction(row) for row in rows]
    
    def get_by_type(self, transaction_type: str) -> List[Transaction]:
        """
        Tipe göre işlemleri getirir.
        
        Args:
            transaction_type: 'income' veya 'expense'
            
        Returns:
            İşlem listesi
        """
        query = """
            SELECT * FROM transactions 
            WHERE transaction_type = ?
            ORDER BY transaction_date DESC, id DESC
        """
        rows = self._db.fetch_all(query, (transaction_type,))
        return [self._row_to_transaction(row) for row in rows]
    
    def get_recent(self, limit: int = 10) -> List[Transaction]:
        """
        Son N işlemi getirir (Dashboard için).
        
        Args:
            limit: Maksimum kayıt sayısı
            
        Returns:
            İşlem listesi
        """
        query = """
            SELECT * FROM transactions 
            ORDER BY transaction_date DESC, id DESC 
            LIMIT ?
        """
        rows = self._db.fetch_all(query, (limit,))
        return [self._row_to_transaction(row) for row in rows]
    
    def update(self, transaction: Transaction) -> bool:
        """
        İşlem bilgilerini günceller.
        
        Args:
            transaction: Güncellenecek işlem nesnesi
            
        Returns:
            Güncelleme başarılı ise True
        """
        if transaction.id is None:
            raise ValueError("İşlem ID'si belirtilmeli")
        
        query = """
            UPDATE transactions
            SET account_id = ?, transaction_type = ?, amount = ?,
                currency = ?, category = ?, description = ?, transaction_date = ?
            WHERE id = ?
        """
        cursor = self._db.execute(
            query,
            (
                transaction.account_id,
                transaction.transaction_type,
                transaction.amount,
                transaction.currency,
                transaction.category,
                transaction.description,
                transaction.transaction_date.isoformat(),
                transaction.id
            )
        )
        return cursor.rowcount > 0
    
    def delete(self, transaction_id: int) -> bool:
        """
        İşlemi siler.
        
        Args:
            transaction_id: Silinecek işlem ID'si
            
        Returns:
            Silme başarılı ise True
        """
        query = "DELETE FROM transactions WHERE id = ?"
        cursor = self._db.execute(query, (transaction_id,))
        return cursor.rowcount > 0
    
    def get_summary_by_type(self) -> dict:
        """
        Tip bazında toplam tutarları hesaplar.
        
        Returns:
            {'income': toplam_gelir, 'expense': toplam_gider}
        """
        query = """
            SELECT transaction_type, SUM(amount) as total
            FROM transactions
            GROUP BY transaction_type
        """
        rows = self._db.fetch_all(query)
        result = {TransactionType.INCOME: 0.0, TransactionType.EXPENSE: 0.0}
        for row in rows:
            result[row["transaction_type"]] = row["total"] or 0.0
        return result
    
    def _row_to_transaction(self, row) -> Transaction:
        """
        Veritabanı satırını Transaction nesnesine dönüştürür.
        
        Args:
            row: sqlite3.Row nesnesi
            
        Returns:
            Transaction nesnesi
        """
        # transaction_date string ise date'e çevir
        trans_date = row["transaction_date"]
        if isinstance(trans_date, str):
            trans_date = date.fromisoformat(trans_date)
        
        return Transaction(
            id=row["id"],
            account_id=row["account_id"],
            transaction_type=row["transaction_type"],
            amount=row["amount"],
            currency=row["currency"],
            category=row["category"] or "",
            description=row["description"] or "",
            transaction_date=trans_date,
            created_at=row["created_at"]
        )
