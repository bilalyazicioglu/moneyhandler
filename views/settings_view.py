"""
Ayarlar View Modülü

Uygulama ayarları ekranı widget'ı.
Dil seçimi ve diğer uygulama ayarları.
"""

from typing import TYPE_CHECKING
import json
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QGroupBox,
    QFrame,
    QMessageBox,
    QPushButton
)

from config import COLORS, t, CURRENT_LANGUAGE, get_database_path

if TYPE_CHECKING:
    from controllers.main_controller import MainController


def get_settings_path() -> Path:
    """Ayarlar dosyasının yolunu döndürür."""
    db_path = get_database_path()
    return db_path.parent / "settings.json"


def load_settings() -> dict:
    """Ayarları dosyadan yükler."""
    settings_path = get_settings_path()
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"language": "tr"}


def save_settings(settings: dict) -> None:
    """Ayarları dosyaya kaydeder."""
    settings_path = get_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)


class SettingsView(QWidget):
    """
    Ayarlar ekranı widget'ı.
    
    Attributes:
        controller: Ana uygulama controller'ı
    """
    
    language_changed = pyqtSignal(str)
    
    def __init__(self, controller: 'MainController') -> None:
        """
        Widget başlatıcısı.
        
        Args:
            controller: Ana uygulama controller'ı
        """
        super().__init__()
        self.controller = controller
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        title = QLabel(t("settings_title"))
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS.TEXT_PRIMARY};
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel(t("settings_subtitle"))
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 14px;")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        language_group = QGroupBox(t("language_settings"))
        language_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS.BG_CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 12px;
                margin-top: 16px;
                padding: 20px;
                font-weight: 600;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        language_layout = QVBoxLayout(language_group)
        language_layout.setSpacing(16)
        
        lang_row = QHBoxLayout()
        lang_row.setSpacing(16)
        
        lang_label = QLabel(t("select_language"))
        lang_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS.TEXT_PRIMARY};
            font-weight: 500;
        """)
        lang_row.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(200)
        self.language_combo.addItem("🇹🇷 Türkçe", "tr")
        self.language_combo.addItem("🇬🇧 English", "en")
        self.language_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS.BG_INPUT};
                border: 1px solid {COLORS.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border-color: {COLORS.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
        """)
        
        settings = load_settings()
        current_lang = settings.get("language", "tr")
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self.language_combo)
        
        lang_row.addStretch()
        language_layout.addLayout(lang_row)
        
        info_label = QLabel(t("language_restart_note"))
        info_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS.TEXT_SECONDARY};
            padding: 8px 12px;
            background-color: {COLORS.BG_ELEVATED};
            border-radius: 6px;
        """)
        info_label.setWordWrap(True)
        language_layout.addWidget(info_label)
        
        layout.addWidget(language_group)
        
        about_group = QGroupBox(t("about_app"))
        about_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS.BG_CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 12px;
                margin-top: 16px;
                padding: 20px;
                font-weight: 600;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        about_layout = QVBoxLayout(about_group)
        about_layout.setSpacing(8)
        
        app_name = QLabel("MoneyHandler")
        app_name.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS.TEXT_PRIMARY};
        """)
        about_layout.addWidget(app_name)
        
        version_label = QLabel(t("version") + ": 1.0.0")
        version_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS.TEXT_SECONDARY};
        """)
        about_layout.addWidget(version_label)
        
        desc_label = QLabel(t("app_description"))
        desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS.TEXT_SECONDARY};
            margin-top: 8px;
        """)
        desc_label.setWordWrap(True)
        about_layout.addWidget(desc_label)
        
        layout.addWidget(about_group)
        
        layout.addStretch()
    
    def _on_language_changed(self, index: int) -> None:
        """Dil değiştiğinde çağrılır."""
        new_lang = self.language_combo.currentData()
        settings = load_settings()
        
        if settings.get("language") != new_lang:
            settings["language"] = new_lang
            save_settings(settings)
            
            QMessageBox.information(
                self,
                t("language_changed_title"),
                t("language_changed_message")
            )
            
            self.language_changed.emit(new_lang)
    
    def refresh(self) -> None:
        """Görünümü yeniler."""
        pass
