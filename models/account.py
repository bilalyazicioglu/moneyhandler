"""
Hesap (Account) Modeli ve Repository

Bu modül hesap/cüzdan veri sınıfını ve veritabanı işlemlerini içerir.
Repository pattern ile veritabanı işlemleri soyutlanmıştır.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from data.database import get_database


@dataclass
class Account:
    """
    Hesap/Cüzdan veri sınıfı.
    
    Attributes:
        id: Benzersiz hesap kimliği
        name: Hesap adı (örn: "Nakit Cüzdan", "Ziraat Bankası")
        account_type: Hesap tipi ('cash' veya 'bank')
        currency: Para birimi kodu (TRY, USD, EUR)
        balance: Güncel bakiye
        description: Hesap açıklaması
        created_at: Oluşturulma tarihi
        updated_at: Son güncelleme tarihi
    """
    name: str
    account_type: str = "cash"
    currency: str = "TRY"
    balance: float = 0.0
    description: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Veri doğrulama."""
        if self.account_type not in ("cash", "bank"):
            raise ValueError(f"Geçersiz hesap tipi: {self.account_type}")
        if self.currency not in ("TRY", "USD", "EUR"):
            raise ValueError(f"Geçersiz para birimi: {self.currency}")


class AccountRepository:
    """
    Hesap veritabanı işlemleri repository sınıfı.
    
    CRUD operasyonları ve özel sorgular için metodlar sağlar.
    """
    
    def __init__(self) -> None:
        """Repository başlatıcısı."""
        self._db = get_database()
    
    def create(self, account: Account) -> Account:
        """
        Yeni bir hesap oluşturur.
        
        Args:
            account: Oluşturulacak hesap nesnesi
            
        Returns:
            ID atanmış hesap nesnesi
        """
        query = """
            INSERT INTO accounts (name, account_type, currency, balance, description)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self._db.execute(
            query,
            (
                account.name,
                account.account_type,
                account.currency,
                account.balance,
                account.description
            )
        )
        account.id = cursor.lastrowid
        return account
    
    def get_all(self) -> List[Account]:
        """
        Tüm hesapları getirir.
        
        Returns:
            Hesap listesi
        """
        query = "SELECT * FROM accounts ORDER BY name"
        rows = self._db.fetch_all(query)
        return [self._row_to_account(row) for row in rows]
    
    def get_by_id(self, account_id: int) -> Optional[Account]:
        """
        ID'ye göre hesap getirir.
        
        Args:
            account_id: Hesap ID'si
            
        Returns:
            Hesap nesnesi veya None
        """
        query = "SELECT * FROM accounts WHERE id = ?"
        row = self._db.fetch_one(query, (account_id,))
        return self._row_to_account(row) if row else None
    
    def update(self, account: Account) -> bool:
        """
        Hesap bilgilerini günceller.
        
        Args:
            account: Güncellenecek hesap nesnesi
            
        Returns:
            Güncelleme başarılı ise True
        """
        if account.id is None:
            raise ValueError("Hesap ID'si belirtilmeli")
        
        query = """
            UPDATE accounts
            SET name = ?, account_type = ?, currency = ?, 
                balance = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        cursor = self._db.execute(
            query,
            (
                account.name,
                account.account_type,
                account.currency,
                account.balance,
                account.description,
                account.id
            )
        )
        return cursor.rowcount > 0
    
    def delete(self, account_id: int) -> bool:
        """
        Hesabı siler.
        
        Args:
            account_id: Silinecek hesap ID'si
            
        Returns:
            Silme başarılı ise True
        """
        query = "DELETE FROM accounts WHERE id = ?"
        cursor = self._db.execute(query, (account_id,))
        return cursor.rowcount > 0
    
    def update_balance(self, account_id: int, amount: float) -> bool:
        """
        Hesap bakiyesini günceller (ekleme/çıkarma).
        
        Args:
            account_id: Hesap ID'si
            amount: Eklenecek/çıkarılacak miktar (negatif olabilir)
            
        Returns:
            Güncelleme başarılı ise True
        """
        query = """
            UPDATE accounts
            SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        cursor = self._db.execute(query, (amount, account_id))
        return cursor.rowcount > 0
    
    def get_total_balance_by_currency(self) -> dict:
        """
        Para birimine göre toplam bakiyeleri hesaplar.
        
        Returns:
            Para birimi -> toplam bakiye sözlüğü
        """
        query = """
            SELECT currency, SUM(balance) as total
            FROM accounts
            GROUP BY currency
        """
        rows = self._db.fetch_all(query)
        return {row["currency"]: row["total"] for row in rows}
    
    def _row_to_account(self, row) -> Account:
        """
        Veritabanı satırını Account nesnesine dönüştürür.
        
        Args:
            row: sqlite3.Row nesnesi
            
        Returns:
            Account nesnesi
        """
        return Account(
            id=row["id"],
            name=row["name"],
            account_type=row["account_type"],
            currency=row["currency"],
            balance=row["balance"],
            description=row["description"] or "",
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
