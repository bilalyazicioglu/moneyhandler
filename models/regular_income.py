"""
Düzenli Gelir (RegularIncome) Modeli ve Repository

Bu modül düzenli gelir tanımlarını ve ödeme geçmişini yönetir.
Maaş, burs, harçlık gibi aylık gelirlerin takibi için kullanılır.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from data.database import get_database


# Düzenli gelir kategorileri
class IncomeCategory:
    """Düzenli gelir kategori sabitleri."""
    SALARY = "salary"
    SCHOLARSHIP = "scholarship"
    ALLOWANCE = "allowance"
    RENTAL = "rental"
    OTHER = "other"


@dataclass
class RegularIncome:
    """
    Düzenli gelir tanımı veri sınıfı.
    
    Attributes:
        id: Benzersiz kimlik
        account_id: İlişkili hesap ID'si
        name: Gelir adı (örn: "İş Maaşı", "YKS Bursu")
        category: Kategori (salary, scholarship, allowance, rental, other)
        amount: Beklenen tutar
        expected_day: Ayın kaçıncı günü bekleniyor (1-31)
        currency: Para birimi kodu
        description: Açıklama
        is_active: Aktif mi?
        created_at: Oluşturulma tarihi
    """
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
        """Veri doğrulama."""
        if not 1 <= self.expected_day <= 31:
            raise ValueError(f"Beklenen gün 1-31 arasında olmalı: {self.expected_day}")
        if self.amount < 0:
            raise ValueError("Tutar negatif olamaz")
    
    def get_expected_date_for_month(self, year: int, month: int) -> date:
        """
        Belirli bir ay için beklenen tarihi hesaplar.
        
        Eğer beklenen gün ayın gün sayısından büyükse,
        ayın son günü kullanılır.
        """
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        day = min(self.expected_day, last_day)
        return date(year, month, day)


@dataclass
class IncomePayment:
    """
    Gerçekleşen ödeme kaydı veri sınıfı.
    
    Attributes:
        id: Benzersiz kimlik
        regular_income_id: İlişkili düzenli gelir ID'si
        expected_date: Beklenen tarih
        actual_date: Gerçekleşen tarih
        amount: Gerçekleşen tutar
        delay_days: Gecikme günü (negatif = erken, pozitif = geç, 0 = zamanında)
        currency: Para birimi
        notes: Notlar
        created_at: Oluşturulma tarihi
    """
    regular_income_id: int
    expected_date: date
    actual_date: date
    amount: float
    currency: str = "TRY"
    notes: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    @property
    def delay_days(self) -> int:
        """Gecikme günlerini hesaplar."""
        return (self.actual_date - self.expected_date).days
    
    @property
    def is_early(self) -> bool:
        """Erken mi?"""
        return self.delay_days < 0
    
    @property
    def is_on_time(self) -> bool:
        """Zamanında mı?"""
        return self.delay_days == 0
    
    @property
    def is_late(self) -> bool:
        """Geç mi?"""
        return self.delay_days > 0


class RegularIncomeRepository:
    """
    Düzenli gelir veritabanı işlemleri repository sınıfı.
    """
    
    def __init__(self) -> None:
        """Repository başlatıcısı."""
        self._db = get_database()
    
    def create(self, income: RegularIncome) -> RegularIncome:
        """
        Yeni bir düzenli gelir oluşturur.
        
        Args:
            income: Oluşturulacak düzenli gelir nesnesi
            
        Returns:
            ID atanmış düzenli gelir nesnesi
        """
        query = """
            INSERT INTO regular_incomes 
            (account_id, name, category, amount, currency, expected_day, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._db.execute(
            query,
            (
                income.account_id,
                income.name,
                income.category,
                income.amount,
                income.currency,
                income.expected_day,
                income.description,
                1 if income.is_active else 0
            )
        )
        income.id = cursor.lastrowid
        return income
    
    def get_all(self, active_only: bool = True) -> List[RegularIncome]:
        """
        Tüm düzenli gelirleri getirir.
        
        Args:
            active_only: Sadece aktif olanları getir
            
        Returns:
            Düzenli gelir listesi
        """
        if active_only:
            query = "SELECT * FROM regular_incomes WHERE is_active = 1 ORDER BY expected_day ASC"
        else:
            query = "SELECT * FROM regular_incomes ORDER BY expected_day ASC"
        rows = self._db.fetch_all(query)
        return [self._row_to_regular_income(row) for row in rows]
    
    def get_by_id(self, income_id: int) -> Optional[RegularIncome]:
        """
        ID'ye göre düzenli gelir getirir.
        
        Args:
            income_id: Düzenli gelir ID'si
            
        Returns:
            RegularIncome nesnesi veya None
        """
        query = "SELECT * FROM regular_incomes WHERE id = ?"
        row = self._db.fetch_one(query, (income_id,))
        return self._row_to_regular_income(row) if row else None
    
    def update(self, income: RegularIncome) -> bool:
        """
        Düzenli gelir bilgilerini günceller.
        
        Args:
            income: Güncellenecek düzenli gelir nesnesi
            
        Returns:
            Güncelleme başarılı ise True
        """
        if income.id is None:
            raise ValueError("Düzenli gelir ID'si belirtilmeli")
        
        query = """
            UPDATE regular_incomes
            SET account_id = ?, name = ?, category = ?, amount = ?,
                currency = ?, expected_day = ?, description = ?, is_active = ?
            WHERE id = ?
        """
        cursor = self._db.execute(
            query,
            (
                income.account_id,
                income.name,
                income.category,
                income.amount,
                income.currency,
                income.expected_day,
                income.description,
                1 if income.is_active else 0,
                income.id
            )
        )
        return cursor.rowcount > 0
    
    def delete(self, income_id: int) -> bool:
        """
        Düzenli geliri siler.
        
        Args:
            income_id: Silinecek düzenli gelir ID'si
            
        Returns:
            Silme başarılı ise True
        """
        query = "DELETE FROM regular_incomes WHERE id = ?"
        cursor = self._db.execute(query, (income_id,))
        return cursor.rowcount > 0
    
    def record_payment(self, payment: IncomePayment) -> IncomePayment:
        """
        Yeni bir ödeme kaydı oluşturur.
        
        Args:
            payment: Oluşturulacak ödeme kaydı
            
        Returns:
            ID atanmış ödeme kaydı
        """
        delay = payment.delay_days
        query = """
            INSERT INTO income_payments 
            (regular_income_id, expected_date, actual_date, amount, currency, delay_days, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._db.execute(
            query,
            (
                payment.regular_income_id,
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
    
    def get_payments(self, income_id: int, limit: int = 12) -> List[IncomePayment]:
        """
        Belirli bir düzenli gelirin ödeme geçmişini getirir.
        
        Args:
            income_id: Düzenli gelir ID'si
            limit: Maksimum kayıt sayısı
            
        Returns:
            Ödeme kayıtları listesi (en yeniden eskiye)
        """
        query = """
            SELECT * FROM income_payments 
            WHERE regular_income_id = ?
            ORDER BY actual_date DESC
            LIMIT ?
        """
        rows = self._db.fetch_all(query, (income_id, limit))
        return [self._row_to_income_payment(row) for row in rows]
    
    def get_average_delay(self, income_id: int) -> float:
        """
        Belirli bir düzenli gelirin ortalama gecikme süresini hesaplar.
        
        Args:
            income_id: Düzenli gelir ID'si
            
        Returns:
            Ortalama gecikme günü (negatif = ortalama erken)
        """
        query = """
            SELECT AVG(delay_days) as avg_delay
            FROM income_payments
            WHERE regular_income_id = ?
        """
        row = self._db.fetch_one(query, (income_id,))
        return row["avg_delay"] if row and row["avg_delay"] is not None else 0.0
    
    def get_pending_this_month(self) -> List[RegularIncome]:
        """
        Bu ay henüz ödeme kaydedilmemiş düzenli gelirleri getirir.
        
        Returns:
            Bekleyen düzenli gelir listesi
        """
        today = date.today()
        first_day = date(today.year, today.month, 1)
        
        query = """
            SELECT ri.* FROM regular_incomes ri
            WHERE ri.is_active = 1
            AND NOT EXISTS (
                SELECT 1 FROM income_payments ip
                WHERE ip.regular_income_id = ri.id
                AND ip.expected_date >= ?
            )
        """
        rows = self._db.fetch_all(query, (first_day.isoformat(),))
        return [self._row_to_regular_income(row) for row in rows]
    
    def _row_to_regular_income(self, row) -> RegularIncome:
        """
        Veritabanı satırını RegularIncome nesnesine dönüştürür.
        """
        return RegularIncome(
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
    
    def _row_to_income_payment(self, row) -> IncomePayment:
        """
        Veritabanı satırını IncomePayment nesnesine dönüştürür.
        """
        expected = row["expected_date"]
        actual = row["actual_date"]
        
        if isinstance(expected, str):
            expected = date.fromisoformat(expected)
        if isinstance(actual, str):
            actual = date.fromisoformat(actual)
        
        return IncomePayment(
            id=row["id"],
            regular_income_id=row["regular_income_id"],
            expected_date=expected,
            actual_date=actual,
            amount=row["amount"],
            currency=row["currency"],
            notes=row["notes"] or "",
            created_at=row["created_at"]
        )
