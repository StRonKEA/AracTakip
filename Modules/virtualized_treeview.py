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
        self.displayed_data = []
        
    def set_data(self, data):
        """Tüm veriyi ayarla ve sayfalara böl"""
        self.all_data = data
        self.total_pages = (len(data) + self.page_size - 1) // self.page_size
        self.current_page = 0
        self._display_page(0)
        return self.total_pages
        
    def _display_page(self, page_num):
        """Belirli bir sayfayı göster"""
        if not self.all_data:
            return
            
        start_idx = page_num * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.all_data))
        
        # Önceki verileri temizle
        for item in self.get_children():
            self.delete(item)
            
        # Yeni sayfayı göster
        self.displayed_data = self.all_data[start_idx:end_idx]
        for i, record in enumerate(self.displayed_data):
            self.insert("", "end", values=record)
            
        # Sayfa bilgisini güncelle
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
            
    def goto_page(self, page_num):
        """Belirli bir sayfaya git"""
        if 0 <= page_num < self.total_pages:
            self._display_page(page_num)
            return True
        return False
            
    def get_current_page_info(self):
        """Mevcut sayfa bilgisini döndür"""
        if not self.all_data:
            return "0/0 (0 kayıt)"
            
        start_idx = self.current_page * self.page_size + 1
        end_idx = min((self.current_page + 1) * self.page_size, len(self.all_data))
        
        return f"Sayfa {self.current_page + 1}/{self.total_pages} ({start_idx}-{end_idx} / {len(self.all_data)} kayıt)"
    
    def get_selected_record_id(self):
        """Seçili kaydın ID'sini döndür"""
        selected = self.selection()
        if selected:
            item = self.item(selected[0])
            return item['values'][0]  # ID ilk sütunda
        return None
    
    def refresh_current_page(self):
        """Mevcut sayfayı yeniden yükle"""
        self._display_page(self.current_page)