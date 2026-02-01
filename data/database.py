"""
Veritabanı Yönetim Modülü

SQLite veritabanı bağlantısını yöneten ve tablo yapısını oluşturan modül.
Singleton pattern ile tek bir bağlantı örneği kullanılır.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from config import DATABASE_PATH


class DatabaseManager:
    """
    SQLite veritabanı bağlantı yöneticisi.
    
    Singleton pattern kullanarak tek bir veritabanı bağlantısı sağlar.
    Context manager desteği ile güvenli bağlantı yönetimi sunar.
    
    Attributes:
        _instance: Singleton örneği
        _connection: SQLite bağlantı nesnesi
    """
    
    _instance: Optional['DatabaseManager'] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls) -> 'DatabaseManager':
        """Singleton pattern implementasyonu."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """DatabaseManager başlatıcısı."""
        if self._connection is None:
            self._ensure_directory()
            self._connect()
            self._create_tables()
    
    def _ensure_directory(self) -> None:
        """Veritabanı dizininin var olduğundan emin olur."""
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    def _connect(self) -> None:
        """Veritabanına bağlantı kurar."""
        self._connection = sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False
        )
        # Row factory ile sözlük benzeri erişim
        self._connection.row_factory = sqlite3.Row
        # Foreign key desteğini etkinleştir
        self._connection.execute("PRAGMA foreign_keys = ON")
    
    def _create_tables(self) -> None:
        """
        Veritabanı tablolarını oluşturur.
        
        Tablolar:
        - accounts: Hesap/Cüzdan bilgileri
        - transactions: Gerçekleşen işlemler (gelir/gider)
        - planned_items: Planlanan/Beklenen işlemler
        """
        cursor = self._connection.cursor()
        
        # Hesaplar tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL DEFAULT 'cash',
                currency TEXT NOT NULL DEFAULT 'TRY',
                balance REAL NOT NULL DEFAULT 0.0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # İşlemler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('income', 'expense')),
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'TRY',
                category TEXT,
                description TEXT,
                transaction_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        """)
        
        # Planlanan işlemler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planned_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('income', 'expense')),
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'TRY',
                category TEXT,
                description TEXT,
                planned_date DATE NOT NULL,
                is_recurring INTEGER DEFAULT 0,
                recurrence_period TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        """)
        
        # Düzenli gelir tanımları tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regular_incomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'TRY',
                expected_day INTEGER NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        """)
        
        # Ödeme geçmişi tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regular_income_id INTEGER NOT NULL,
                expected_date DATE NOT NULL,
                actual_date DATE NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'TRY',
                delay_days INTEGER NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (regular_income_id) REFERENCES regular_incomes(id) ON DELETE CASCADE
            )
        """)
        
        self._connection.commit()
    
    @property
    def connection(self) -> sqlite3.Connection:
        """
        Veritabanı bağlantısını döndürür.
        
        Returns:
            Aktif SQLite bağlantısı
        """
        return self._connection
    
    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager ile güvenli cursor erişimi sağlar.
        
        Yields:
            SQLite cursor nesnesi
            
        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM accounts")
                rows = cursor.fetchall()
        """
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute(
        self,
        query: str,
        params: tuple = ()
    ) -> sqlite3.Cursor:
        """
        SQL sorgusu çalıştırır ve sonucu döndürür.
        
        Args:
            query: SQL sorgu metni
            params: Sorgu parametreleri
            
        Returns:
            Cursor nesnesi
        """
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        self._connection.commit()
        return cursor
    
    def fetch_all(
        self,
        query: str,
        params: tuple = ()
    ) -> list[sqlite3.Row]:
        """
        SQL sorgusu çalıştırır ve tüm sonuçları döndürür.
        
        Args:
            query: SQL sorgu metni
            params: Sorgu parametreleri
            
        Returns:
            Sorgu sonuçları listesi
        """
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(
        self,
        query: str,
        params: tuple = ()
    ) -> Optional[sqlite3.Row]:
        """
        SQL sorgusu çalıştırır ve tek bir sonuç döndürür.
        
        Args:
            query: SQL sorgu metni
            params: Sorgu parametreleri
            
        Returns:
            Tek bir satır veya None
        """
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    
    def close(self) -> None:
        """Veritabanı bağlantısını kapatır."""
        if self._connection:
            self._connection.close()
            self._connection = None
            DatabaseManager._instance = None


# Global veritabanı örneği oluşturma fonksiyonu
def get_database() -> DatabaseManager:
    """
    Veritabanı yöneticisi örneğini döndürür.
    
    Returns:
        DatabaseManager singleton örneği
    """
    return DatabaseManager()
