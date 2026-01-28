"""
Planlanan İşlemler View Modülü

Beklenen/Planlanan işlemler listesi ekranı widget'ı.
Planlanan işlem listesi, ekleme, düzenleme, silme ve gerçekleştirme işlemleri.
"""

from typing import TYPE_CHECKING

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
    QMessageBox
)
from PyQt6.QtGui import QColor

from config import COLORS, CURRENCIES
from models.planned_item import PlannedItem
from views.forms import PlannedItemDialog

if TYPE_CHECKING:
    from controllers.main_controller import MainController


class PlannedItemsView(QWidget):
    """
    Planlanan işlem yönetimi ekranı widget'ı.
    
    Signals:
        planned_item_changed: Planlanan işlem değiştiğinde
        item_realized: Planlanan işlem gerçekleştirildiğinde
    """
    
    planned_item_changed = pyqtSignal()
    item_realized = pyqtSignal()
    
    def __init__(self, controller: 'MainController', parent=None) -> None:
        """
        PlannedItemsView başlatıcısı.
        
        Args:
            controller: Ana controller referansı
            parent: Üst widget
        """
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Başlık ve butonlar
        header_layout = QHBoxLayout()
        
        # Sol taraf: Başlık
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("Planlanan İşlemler")
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Beklenen gelir ve giderlerinizi yönetin")
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Yeni planlanan işlem butonu
        self.add_btn = QPushButton("Yeni Planlanan İşlem")
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
        self.add_btn.clicked.connect(self._on_add_planned_item)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Bilgi kartı
        info_card = QLabel(
            "Gerçekleştir butonuna tıklayarak planlanan işlemi gerçek bir işleme dönüştürebilirsiniz."
        )
        info_card.setStyleSheet(f"""
            color: {COLORS.TEXT_SECONDARY};
            padding: 16px 20px;
            background-color: {COLORS.BG_CARD};
            border: 1px solid {COLORS.BORDER};
            border-left: 4px solid {COLORS.INFO};
            border-radius: 8px;
            font-size: 13px;
        """)
        layout.addWidget(info_card)
        
        # Planlanan işlem tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Hesap", "Tip", "Kategori", "Açıklama", "Tutar", "İşlemler"
        ])
        
        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(6, 140)
        self.table.setColumnWidth(7, 280)
        
        # ID sütununu gizle
        self.table.setColumnHidden(0, True)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        layout.addWidget(self.table)
    
    def refresh(self) -> None:
        """Planlanan işlem listesini yeniler."""
        planned_items = self.controller.get_all_planned_items()
        accounts = {a.id: a for a in self.controller.get_all_accounts()}
        
        self.table.setRowCount(len(planned_items))
        
        for row, item in enumerate(planned_items):
            # ID (gizli)
            id_item = QTableWidgetItem(str(item.id))
            self.table.setItem(row, 0, id_item)
            
            # Tarih
            date_str = item.planned_date.strftime("%d.%m.%Y")
            date_item = QTableWidgetItem(date_str)
            
            # Vadesi geçmiş mi kontrol
            if item.is_overdue:
                date_item.setForeground(QColor(COLORS.DANGER))
                date_item.setToolTip("Vadesi geçmiş!")
            elif item.days_until <= 7:
                date_item.setForeground(QColor(COLORS.WARNING))
                date_item.setToolTip(f"{item.days_until} gün kaldı")
            
            self.table.setItem(row, 1, date_item)
            
            # Hesap
            account = accounts.get(item.account_id)
            account_name = account.name if account else "-"
            self.table.setItem(row, 2, QTableWidgetItem(account_name))
            
            # Tip
            if item.is_income:
                type_text = "Gelir"
                color = COLORS.SUCCESS
            else:
                type_text = "Gider"
                color = COLORS.DANGER
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor(color))
            self.table.setItem(row, 3, type_item)
            
            # Kategori
            self.table.setItem(row, 4, QTableWidgetItem(item.category or "-"))
            
            # Açıklama
            self.table.setItem(row, 5, QTableWidgetItem(item.description or "-"))
            
            # Tutar
            symbol = CURRENCIES[item.currency].symbol
            amount_text = f"{symbol}{item.amount:,.2f}"
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setForeground(QColor(color))
            self.table.setItem(row, 6, amount_item)
            
            # İşlem butonları
            self._add_action_buttons(row, item)
    
    def _add_action_buttons(self, row: int, item: PlannedItem) -> None:
        """
        Satıra işlem butonlarını ekler.
        
        Args:
            row: Satır indeksi
            item: Planlanan işlem nesnesi
        """
        button_widget = QWidget()
        button_widget.setStyleSheet("background-color: transparent;")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(8, 4, 8, 4)
        button_layout.setSpacing(8)
        
        # Gerçekleştir butonu
        realize_btn = QPushButton("Gerçekleştir")
        realize_btn.setFixedHeight(32)
        realize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        realize_btn.setToolTip("Bu planlanan işlemi gerçek işleme dönüştür")
        realize_btn.clicked.connect(lambda: self._on_realize_item(item))
        button_layout.addWidget(realize_btn)
        
        # Düzenle butonu
        edit_btn = QPushButton("Düzenle")
        edit_btn.setFixedHeight(32)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_ELEVATED};
                border: 1px solid {COLORS.BORDER};
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_INPUT};
                border-color: {COLORS.BORDER_LIGHT};
            }}
        """)
        edit_btn.clicked.connect(lambda: self._on_edit_planned_item(item))
        button_layout.addWidget(edit_btn)
        
        # Sil butonu
        delete_btn = QPushButton("Sil")
        delete_btn.setFixedHeight(32)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS.DANGER};
                color: {COLORS.DANGER};
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.DANGER};
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        delete_btn.clicked.connect(lambda: self._on_delete_planned_item(item))
        button_layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row, 7, button_widget)
    
    def _on_add_planned_item(self) -> None:
        """Yeni planlanan işlem ekleme."""
        accounts = self.controller.get_all_accounts()
        if not accounts:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Planlanan işlem eklemek için önce bir hesap oluşturmalısınız!"
            )
            return
        
        dialog = PlannedItemDialog(self, accounts=accounts)
        if dialog.exec():
            planned_item = dialog.get_data()
            self.controller.create_planned_item(planned_item)
            self.refresh()
            self.planned_item_changed.emit()
    
    def _on_edit_planned_item(self, item: PlannedItem) -> None:
        """
        Planlanan işlem düzenleme.
        
        Args:
            item: Düzenlenecek planlanan işlem
        """
        accounts = self.controller.get_all_accounts()
        dialog = PlannedItemDialog(self, item, accounts)
        if dialog.exec():
            updated_item = dialog.get_data()
            self.controller.update_planned_item(updated_item)
            self.refresh()
            self.planned_item_changed.emit()
    
    def _on_delete_planned_item(self, item: PlannedItem) -> None:
        """
        Planlanan işlem silme.
        
        Args:
            item: Silinecek planlanan işlem
        """
        reply = QMessageBox.question(
            self,
            "Planlanan İşlem Sil",
            "Bu planlanan işlemi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_planned_item(item.id)
            self.refresh()
            self.planned_item_changed.emit()
    
    def _on_realize_item(self, item: PlannedItem) -> None:
        """
        Planlanan işlemi gerçek işleme dönüştürür.
        
        Args:
            item: Gerçekleştirilecek planlanan işlem
        """
        reply = QMessageBox.question(
            self,
            "İşlemi Gerçekleştir",
            f"Bu planlanan işlemi gerçek bir işleme dönüştürmek istediğinize emin misiniz?\n\n"
            f"Tutar: {CURRENCIES[item.currency].symbol}{item.amount:,.2f}\n"
            f"Tip: {'Gelir' if item.is_income else 'Gider'}\n\n"
            f"Bu işlem hesap bakiyesini güncelleyecek ve planlanan işlemi silecektir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.controller.realize_planned_item(item)
            if success:
                QMessageBox.information(
                    self,
                    "Başarılı",
                    "Planlanan işlem başarıyla gerçekleştirildi!"
                )
                self.refresh()
                self.item_realized.emit()
            else:
                QMessageBox.warning(
                    self,
                    "Hata",
                    "İşlem gerçekleştirilirken bir hata oluştu."
                )
