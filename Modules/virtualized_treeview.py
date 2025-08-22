# Modules/virtualized_treeview.py
import tkinter as tk
from tkinter import ttk
from Modules.logger import logger

class VirtualizedTreeview(ttk.Treeview):
    """Büyük veri setleri için optimize edilmiş treeview"""
    
    def __init__(self, parent, columns, page_size=100, **kwargs):
        super().__init__(parent, columns=columns, **kwargs)
        self.page_size = page_size
        self.current_page = 0
        self.total_pages = 0
        self.all_data = []
        
    def set_data(self, data):
        """Tüm veriyi ayarla ve sayfalara böl"""
        self.all_data = data
        self.total_pages = (len(data) + self.page_size - 1) // self.page_size if self.page_size > 0 else 1
        self.current_page = 0
        self._display_page(0)
        return self.total_pages
        
    def _display_page(self, page_num):
        """Belirli bir sayfayı göster"""
        self.delete(*self.get_children()) # Önceki verileri temizle
        
        if not self.all_data:
            return
            
        start_idx = page_num * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.all_data))
        
        # --- DEĞİŞİKLİK BURADA ---
        # Artık her bir kayıt için hem değerleri hem de renk etiketini alıyoruz
        for record_values, record_tags in self.all_data[start_idx:end_idx]:
            self.insert("", "end", values=record_values, tags=record_tags)
        # --- DEĞİŞİKLİK BİTTİ ---
            
        self.current_page = page_num
        
    def next_page(self):
        """Sonraki sayfaya git"""
        if self.current_page < self.total_pages - 1:
            self._display_page(self.current_page + 1)
            return True
        return False
            
    def prev_page(self):
        """Önceki sayfaya git"""
        if self.current_page > 0:
            self._display_page(self.current_page - 1)
            return True
        return False
            
    def get_current_page_info(self):
        """Mevcut sayfa bilgisini döndür"""
        if not self.all_data:
            return "0/0 (0 kayıt)"
            
        start_idx = self.current_page * self.page_size + 1
        end_idx = min((self.current_page + 1) * self.page_size, len(self.all_data))
        
        return f"Sayfa {self.current_page + 1}/{self.total_pages} ({start_idx}-{end_idx} / {len(self.all_data)} kayıt)"