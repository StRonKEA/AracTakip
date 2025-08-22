# Modules/ui/treeview_setup.py
import tkinter as tk
from tkinter import ttk
from Modules.virtualized_treeview import VirtualizedTreeview
from datetime import datetime

def create_treeview(parent, settings):
    """Treeview oluşturur."""
    page_size = settings.get("page_size", 100)
    
    tree_container = ttk.Frame(parent)
    tree_container.pack(expand=True, fill='both', padx=10, pady=10)
    tree_container.rowconfigure(0, weight=1)
    tree_container.columnconfigure(0, weight=1)

    tree_frame = ttk.Frame(tree_container)
    tree_frame.grid(row=0, column=0, sticky="nsew")
    
    pagination_frame = ttk.Frame(tree_container)
    pagination_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
    
    tree_columns = ("Sıra No", "Giriş Tarihi", "Giriş Saati", "Plaka", "Dorse Plaka", 
                     "Sürücü", "Telefon", "Sürücü Firması", "Gelinen Firma", "Notlar", "Çıkış Zamanı")
    
    tree = VirtualizedTreeview(tree_frame, columns=tree_columns, show='headings', page_size=page_size)
    
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor='center')
    
    tree.column("Sıra No", width=60, stretch=tk.NO)
    tree.column("Notlar", width=150, stretch=tk.NO)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    tree.pack(expand=True, fill='both')
    
    tree.tag_configure('checked_out', background='#ffdddd', foreground='black')
    tree.tag_configure('inside', background='#d0f0c0', foreground='black')
    
    return {
        'tree': tree,
        'tree_frame': tree_container,
        'pagination_frame': pagination_frame
    }

def populate_treeview_data(tree, records, status_label, status_filter, date_filter, search_term):
    """Treeview'ı verilerle doldurur (Standart Mod için)."""
    for item in tree.get_children():
        tree.delete(item)
    
    filter_text = ""
    if search_term:
        filter_text = f"Arama: '{search_term}'"
    elif status_filter:
        filter_text = f"Sadece '{'İçeridekiler' if status_filter == 'inside' else 'Çıkış Yapanlar'}' gösteriliyor."
    elif date_filter:
        filter_text_map = {"today": "Bugünün Kayıtları", "yesterday": "Dünün Kayıtları", "last_7_days": "Son 7 Günün Kayıtları"}
        filter_text = filter_text_map.get(date_filter, "")
    
    status_label.config(text=f"FİLTRE AKTİF: {filter_text}" if filter_text else "")
    
    for record in records:
        (id, plaka, dorse, surucu, tel, s_firma, g_firma, entry, exit, status, notes) = record
        
        try:
            entry_date = datetime.strptime(entry, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y") if entry else "-"
            entry_time = datetime.strptime(entry, "%Y-%m-%d %H:%M").strftime("%H:%M") if entry else "-"
            exit_zaman = datetime.strptime(exit, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M") if exit else "-"
        except (ValueError, TypeError):
            entry_date, entry_time, exit_zaman = entry, "", exit
        
        tag = 'checked_out' if status == 'checked_out' else 'inside' if status == 'inside' else ''
        note_display = "🗒️ Notu Oku" if notes and notes.strip() else ""
        
        tree.insert("", "end", values=(id, entry_date, entry_time, plaka, dorse, surucu, tel, 
                                     s_firma, g_firma, note_display, exit_zaman), tags=(tag,))

def create_right_click_menu(parent, add_empty_callback, edit_callback, reactivate_callback, delete_callback):
    """Sağ tık menüsü oluşturur."""
    menu = tk.Menu(parent, tearoff=0)
    menu.add_command(label="Yeni Boş Satır Ekle", command=add_empty_callback)
    menu.add_command(label="Seçili Satırı Düzenle", command=edit_callback)
    menu.add_command(label="Tekrar Aktif Yap", command=reactivate_callback)
    menu.add_separator()
    menu.add_command(label="Seçili Satırı Sil", command=delete_callback)
    return menu

def update_right_click_menu_state(menu, record_status):
    """Sağ tık menüsünün durumunu günceller."""
    is_checked_out = (record_status == 'checked_out')
    menu.entryconfig("Seçili Satırı Düzenle", state="normal")
    menu.entryconfig("Seçili Satırı Sil", state="normal")
    menu.entryconfig("Tekrar Aktif Yap", state="normal" if is_checked_out else "disabled")
