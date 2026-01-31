"""
Ana Controller Modülü

UI ve Model katmanları arasındaki iş mantığı köprüsü.
Tüm veri işlemlerini yönetir ve view'lara veri sağlar.
"""

from datetime import date, timedelta
from typing import List, Optional, Dict

from config import (
    convert_to_base_currency,
    BASE_CURRENCY,
    CURRENCIES,
    UPCOMING_DAYS_THRESHOLD,
    TransactionType
)
from data.database import get_database
from models.account import Account, AccountRepository
from models.transaction import Transaction, TransactionRepository
from models.planned_item import PlannedItem, PlannedItemRepository


class MainController:
    """
    Ana controller sınıfı.
    
    UI ve Model katmanları arasındaki köprü görevi görür.
    İş mantığını ve veri akışını yönetir.
    """
    
    def __init__(self) -> None:
        """Controller başlatıcısı."""
        self._db = get_database()
        
        self._account_repo = AccountRepository()
        self._transaction_repo = TransactionRepository()
        self._planned_item_repo = PlannedItemRepository()
    

    def get_all_accounts(self) -> List[Account]:
        """
        Tüm hesapları getirir.
        
        Returns:
            Hesap listesi
        """
        return self._account_repo.get_all()
    
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """
        ID'ye göre hesap getirir.
        
        Args:
            account_id: Hesap ID'si
            
        Returns:
            Account nesnesi veya None
        """
        return self._account_repo.get_by_id(account_id)
    
    def get_transactions_by_account(self, account_id: int) -> List[Transaction]:
        """
        Hesaba ait tüm işlemleri getirir.
        
        Args:
            account_id: Hesap ID'si
            
        Returns:
            İşlem listesi (en yeni ilk)
        """
        return self._transaction_repo.get_by_account(account_id)
    
    def create_account(self, account: Account) -> Account:
        """
        Yeni hesap oluşturur.
        
        Args:
            account: Oluşturulacak hesap
            
        Returns:
            ID atanmış hesap
        """
        return self._account_repo.create(account)
    
    def update_account(self, account: Account) -> bool:
        """
        Hesap bilgilerini günceller.
        
        Args:
            account: Güncellenecek hesap
            
        Returns:
            Başarılı ise True
        """
        return self._account_repo.update(account)
    
    def delete_account(self, account_id: int) -> bool:
        """
        Hesabı siler.
        
        Args:
            account_id: Silinecek hesap ID'si
            
        Returns:
            Başarılı ise True
        """
        return self._account_repo.delete(account_id)
    
    def get_total_assets_in_base_currency(self) -> float:
        """
        Tüm hesapların toplam varlığını ana para birimi cinsinden hesaplar.
        
        Returns:
            Toplam varlık (TRY)
        """
        accounts = self._account_repo.get_all()
        total = 0.0
        
        for account in accounts:
            total += convert_to_base_currency(account.balance, account.currency)
        
        return total
    

    def get_all_transactions(self) -> List[Transaction]:
        """
        Tüm işlemleri getirir.
        
        Returns:
            İşlem listesi
        """
        return self._transaction_repo.get_all()
    
    def get_transactions_by_type(self, transaction_type: str) -> List[Transaction]:
        """
        Tipe göre işlemleri getirir.
        
        Args:
            transaction_type: 'income' veya 'expense'
            
        Returns:
            İşlem listesi
        """
        return self._transaction_repo.get_by_type(transaction_type)
    
    def get_recent_transactions(self, limit: int = 10) -> List[Transaction]:
        """
        Son N işlemi getirir.
        
        Args:
            limit: Maksimum kayıt sayısı
            
        Returns:
            İşlem listesi
        """
        return self._transaction_repo.get_recent(limit)
    
    def create_transaction(self, transaction: Transaction) -> Transaction:
        """
        Yeni işlem oluşturur ve hesap bakiyesini günceller.
        
        Args:
            transaction: Oluşturulacak işlem
            
        Returns:
            ID atanmış işlem
        """
        result = self._transaction_repo.create(transaction)
        
        amount_change = transaction.signed_amount
        self._account_repo.update_balance(transaction.account_id, amount_change)
        
        return result
    
    def update_transaction(
        self,
        old_transaction: Transaction,
        new_transaction: Transaction
    ) -> bool:
        """
        İşlem bilgilerini günceller ve bakiyeleri düzeltir.
        
        Args:
            old_transaction: Eski işlem
            new_transaction: Yeni işlem bilgileri
            
        Returns:
            Başarılı ise True
        """
        old_amount_change = old_transaction.signed_amount
        self._account_repo.update_balance(
            old_transaction.account_id,
            -old_amount_change
        )
        
        result = self._transaction_repo.update(new_transaction)
        
        new_amount_change = new_transaction.signed_amount
        self._account_repo.update_balance(
            new_transaction.account_id,
            new_amount_change
        )
        
        return result
    
    def delete_transaction(self, transaction: Transaction) -> bool:
        """
        İşlemi siler ve hesap bakiyesini düzeltir.
        
        Args:
            transaction: Silinecek işlem
            
        Returns:
            Başarılı ise True
        """
        amount_change = transaction.signed_amount
        self._account_repo.update_balance(
            transaction.account_id,
            -amount_change
        )
        
        return self._transaction_repo.delete(transaction.id)
    
    def get_transaction_summary(self) -> Dict[str, float]:
        """
        Gelir/gider özetini TRY cinsinden döndürür.
        
        Returns:
            {'income': toplam_gelir, 'expense': toplam_gider}
        """
        transactions = self._transaction_repo.get_all()
        
        income_total = 0.0
        expense_total = 0.0
        
        for trans in transactions:
            amount_in_try = convert_to_base_currency(trans.amount, trans.currency)
            if trans.is_income:
                income_total += amount_in_try
            else:
                expense_total += amount_in_try
        
        return {
            'income': income_total,
            'expense': expense_total
        }
    
    def get_transactions_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """
        Tarih aralığındaki işlemleri getirir.
        
        Args:
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi
            
        Returns:
            İşlem listesi
        """
        return self._transaction_repo.get_by_date_range(start_date, end_date)
    
    def get_weekly_spending_data(self) -> Dict:
        """
        Bu haftanın harcama verilerini döndürür.
        
        Pazartesi'den bugüne kadar olan giderleri hesaplar.
        Tüm tutarlar TRY'ye çevrilir.
        
        Returns:
            {
                'daily_spending': {0: [...], 1: [...], ...},  # 0=Pazartesi, Transaction listesi
                'daily_totals': [0.0, 0.0, ...],  # 7 günlük toplam (TRY)
                'weekly_total': float,  # Haftalık toplam (TRY)
                'daily_average': float,  # Günlük ortalama (TRY)
                'week_start': date,  # Pazartesi
                'week_end': date  # Pazar
            }
        """
        today = date.today()
        weekday = today.weekday()
        week_start = today - timedelta(days=weekday)
        week_end = week_start + timedelta(days=6)
        
        transactions = self._transaction_repo.get_by_date_range(week_start, week_end)
        
        daily_spending: Dict[int, List[Transaction]] = {i: [] for i in range(7)}
        daily_totals = [0.0] * 7
        
        for trans in transactions:
            if trans.is_expense:
                day_index = trans.transaction_date.weekday()
                if 0 <= day_index <= 6:
                    daily_spending[day_index].append(trans)
                    amount_in_try = convert_to_base_currency(trans.amount, trans.currency)
                    daily_totals[day_index] += amount_in_try
        
        weekly_total = sum(daily_totals)
        
        days_passed = weekday + 1
        daily_average = weekly_total / days_passed if days_passed > 0 else 0.0
        
        return {
            'daily_spending': daily_spending,
            'daily_totals': daily_totals,
            'weekly_total': weekly_total,
            'daily_average': daily_average,
            'week_start': week_start,
            'week_end': week_end
        }
    
    def get_weekly_spending_data_for_week(self, week_start_date: date) -> Dict:
        """
        Belirli bir haftanın harcama verilerini döndürür.
        
        Args:
            week_start_date: Haftanın başlangıç tarihi (Pazartesi)
            
        Returns:
            Haftalık harcama verileri dictionary'si
        """
        week_start = week_start_date
        week_end = week_start + timedelta(days=6)
        
        transactions = self._transaction_repo.get_by_date_range(week_start, week_end)
        
        daily_spending: Dict[int, List[Transaction]] = {i: [] for i in range(7)}
        daily_totals = [0.0] * 7
        
        for trans in transactions:
            if trans.is_expense:
                day_index = trans.transaction_date.weekday()
                if 0 <= day_index <= 6:
                    daily_spending[day_index].append(trans)
                    amount_in_try = convert_to_base_currency(trans.amount, trans.currency)
                    daily_totals[day_index] += amount_in_try
        
        weekly_total = sum(daily_totals)
        
        today = date.today()
        if week_start <= today <= week_end:
            days_passed = today.weekday() + 1
        elif today > week_end:
            days_passed = 7
        else:
            days_passed = 0
        
        daily_average = weekly_total / days_passed if days_passed > 0 else 0.0
        
        return {
            'daily_spending': daily_spending,
            'daily_totals': daily_totals,
            'weekly_total': weekly_total,
            'daily_average': daily_average,
            'week_start': week_start,
            'week_end': week_end
        }


    def get_all_planned_items(self) -> List[PlannedItem]:
        """
        Tüm planlanan işlemleri getirir.
        
        Returns:
            Planlanan işlem listesi
        """
        return self._planned_item_repo.get_all()
    
    def get_upcoming_payments(self) -> List[PlannedItem]:
        """
        Yaklaşan ödemeleri/gelirleri getirir.
        
        Returns:
            Yaklaşan planlanan işlemler listesi
        """
        return self._planned_item_repo.get_upcoming(UPCOMING_DAYS_THRESHOLD)
    
    def create_planned_item(self, item: PlannedItem) -> PlannedItem:
        """
        Yeni planlanan işlem oluşturur.
        
        Args:
            item: Oluşturulacak planlanan işlem
            
        Returns:
            ID atanmış planlanan işlem
        """
        return self._planned_item_repo.create(item)
    
    def update_planned_item(self, item: PlannedItem) -> bool:
        """
        Planlanan işlem bilgilerini günceller.
        
        Args:
            item: Güncellenecek planlanan işlem
            
        Returns:
            Başarılı ise True
        """
        return self._planned_item_repo.update(item)
    
    def delete_planned_item(self, item_id: int) -> bool:
        """
        Planlanan işlemi siler.
        
        Args:
            item_id: Silinecek planlanan işlem ID'si
            
        Returns:
            Başarılı ise True
        """
        return self._planned_item_repo.delete(item_id)
    
    def realize_planned_item(self, item: PlannedItem) -> bool:
        """
        Planlanan işlemi gerçek işleme dönüştürür.
        
        Planlanan işlemi siler ve aynı bilgilerle yeni bir
        Transaction oluşturur. Hesap bakiyesi güncellenir.
        
        Args:
            item: Gerçekleştirilecek planlanan işlem
            
        Returns:
            Başarılı ise True
        """
        try:
            transaction = Transaction(
                account_id=item.account_id,
                transaction_type=item.transaction_type,
                amount=item.amount,
                currency=item.currency,
                category=item.category,
                description=item.description,
                transaction_date=date.today()  # Bugünün tarihi ile
            )
            
            self.create_transaction(transaction)
            
            self._planned_item_repo.delete(item.id)
            
            return True
        except Exception as e:
            print(f"Hata: Planlanan işlem gerçekleştirilemedi - {e}")
            return False
    

    def close(self) -> None:
        """Veritabanı bağlantısını kapatır."""
        self._db.close()
