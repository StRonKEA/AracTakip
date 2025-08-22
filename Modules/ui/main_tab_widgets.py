# Modules/ui/main_tab_widgets.py
import tkinter as tk
from tkinter import ttk
from Modules.logger import logger

def _clear_placeholder(event, widget, placeholder_map):
    """Placeholder temizle"""
    try:
        # Widget'in adını (key) placeholder_map'te bul
        widget_key = next((key for key, val in placeholder_map.items() if val == widget.get()), None)
        if widget_key and widget.get() == placeholder_map[widget_key]:
            widget.delete(0, tk.END)
            # Stil tkinter sürümüne göre değişebilir, basit tutalım
            widget.config(foreground='black') # Varsayılan metin rengi
    except Exception as e:
        logger.log_error("Placeholder temizleme hatası", e)


def _add_placeholder(event, widget, placeholder_map):
    """Placeholder ekle"""
    try:
        # Bu widget için bir placeholder var mı kontrol et
        widget_key = next((key for key, entry in event.widget.master.master.entries.items() if entry == widget), None)
        if widget_key and not widget.get():
            widget.insert(0, placeholder_map[widget_key])
            widget.config(foreground='grey')
    except Exception as e:
        # Bu hatayı loglamak çok gürültülü olabilir, şimdilik geçelim
        pass

def create_form_frame(parent, placeholder_map, add_callback, clear_callback):
    """Form çerçevesi oluştur"""
    try:
        form_frame = ttk.LabelFrame(parent, text="Yeni Araç Girişi", padding=(20, 10))
        form_frame.pack(fill='x', padx=10, pady=10)
        form_frame.columnconfigure((1, 3), weight=1)
        
        label_map = {
            "Plaka": "Plaka", "Dorse Plaka": "Dorse", "Sürücü": "Sürücü", 
            "Telefon": "Telefon", "Sürücünün Firması": "Sürücünün", "Gelinen Firma": "Gelinen"
        }
        
        entries = {}
        for i, (label_text, key) in enumerate(label_map.items()):
            row, col = i // 2, (i % 2) * 2
            ttk.Label(form_frame, text=f"{label_text}:").grid(row=row, column=col, padx=5, pady=8, sticky='w')
            
            entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=row, column=col + 1, padx=5, pady=8, sticky='ew')
            entries[key] = entry
            
            # Placeholder logic can be simplified or managed within the main app if needed
            # For now, let's keep it basic
            entry.insert(0, placeholder_map[key])
            entry.config(foreground='grey')
            entry.bind("<FocusIn>", lambda e, w=entry, p=placeholder_map[key]: (w.delete(0, tk.END), w.config(foreground='black')) if w.get() == p else None)
            entry.bind("<FocusOut>", lambda e, w=entry, p=placeholder_map[key]: (w.insert(0, p), w.config(foreground='grey')) if not w.get() else None)

        # Notlar alanı
        ttk.Label(form_frame, text="Notlar:").grid(row=3, column=0, padx=5, pady=8, sticky="nw")
        notes_entry = tk.Text(form_frame, height=3, wrap="word")
        notes_entry.grid(row=3, column=1, columnspan=3, padx=5, pady=8, sticky="ew")
        
        # Butonlar
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Yeni Araç Girişini Ekle", 
                  command=add_callback, style="Accent.TButton").pack(side='left', padx=5)
        ttk.Button(button_frame, text="Formu Temizle", 
                  command=clear_callback).pack(side='left', padx=5)
        
        return {
            'frame': form_frame,
            'entries': entries,
            'notes_entry': notes_entry
        }
        
    except Exception as e:
        logger.log_error("Form çerçevesi oluşturma hatası", e)
        raise

def create_filter_frame(parent, years, months, apply_callback, filter_callback, search_callback):
    """Filtre çerçevesi oluştur"""
    try:
        from datetime import datetime
        filter_frame = ttk.LabelFrame(parent, text="Görünüm ve Filtreleme", padding=(10,10))
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        year_var = tk.StringVar(value=str(datetime.now().year))
        month_var = tk.StringVar(value=list(months.keys())[datetime.now().month - 1])
        search_var = tk.StringVar()
        
        ttk.Label(filter_frame, text="Yıl:").pack(side='left', padx=(0, 5))
        year_combo = ttk.Combobox(filter_frame, textvariable=year_var, values=years, state="readonly", width=6)
        year_combo.pack(side='left', padx=5)
        year_combo.bind("<<ComboboxSelected>>", lambda e: apply_callback())
        
        ttk.Label(filter_frame, text="Ay:").pack(side='left', padx=(10, 5))
        month_combo = ttk.Combobox(filter_frame, textvariable=month_var, values=list(months.keys()), state="readonly", width=10)
        month_combo.pack(side='left', padx=5)
        month_combo.bind("<<ComboboxSelected>>", lambda e: apply_callback())
        
        ttk.Label(filter_frame, text="Ara:").pack(side='left', padx=(20, 5))
        search_entry = ttk.Entry(filter_frame, textvariable=search_var, width=30)
        search_entry.pack(side='left', padx=5)
        search_entry.bind("<KeyRelease>", lambda e: search_callback())
        
        status_frame = ttk.Frame(filter_frame)
        status_frame.pack(side='right', padx=10)
        
        inside_button = ttk.Button(status_frame, text="Aktif İçeride: 0", 
                                 command=lambda: filter_callback('inside'), style="Success.TButton")
        inside_button.pack(side='left', padx=5)
        
        checked_out_button = ttk.Button(status_frame, text="Çıkış Yapan: 0", 
                                      command=lambda: filter_callback('checked_out'), style="Danger.TButton")
        checked_out_button.pack(side='left', padx=5)
        
        ttk.Button(status_frame, text="Varsayılan Görünüm", 
                  command=apply_callback, style="Accent.TButton").pack(side='left', padx=10)
        
        filter_status_label = ttk.Label(parent, text="", foreground="red", 
                                      font=("Helvetica", 10, "bold"))
        filter_status_label.pack(fill='x', padx=10, pady=(0, 5))
        
        return {
            'year_var': year_var,
            'month_var': month_var,
            'search_var': search_var,
            'inside_button': inside_button,
            'checked_out_button': checked_out_button,
            'filter_status_label': filter_status_label
        }
        
    except Exception as e:
        logger.log_error("Filtre çerçevesi oluşturma hatası", e)
        raise

def create_actions_frame(parent, edit_callback, delete_callback, checkout_callback, reactivate_callback):
    """Aksiyon butonları çerçevesi"""
    try:
        actions_frame = ttk.LabelFrame(parent, text="Liste İşlemleri", padding=(10, 10))
        actions_frame.pack(fill='x', padx=10, pady=5)
        actions_frame.columnconfigure(1, weight=1)
        
        left_actions = ttk.Frame(actions_frame)
        left_actions.grid(row=0, column=0, sticky='w')
        
        right_actions = ttk.Frame(actions_frame)
        right_actions.grid(row=0, column=2, sticky='e')
        
        edit_button = ttk.Button(left_actions, text="Seçili Kaydı Düzenle", 
                               command=edit_callback, state="disabled")
        edit_button.pack(side='left', padx=5, pady=5)
        
        delete_button = ttk.Button(left_actions, text="Seçili Kaydı Sil", 
                                 command=delete_callback, state="disabled")
        delete_button.pack(side='left', padx=5, pady=5)
        
        checkout_button = ttk.Button(right_actions, text="Seçili Araca Çıkış Ver", 
                                   command=checkout_callback, state="disabled")
        checkout_button.pack(side='left', padx=5, pady=5)
        
        reactivate_button = ttk.Button(right_actions, text="Seçili Aracı Aktif Yap", 
                                     command=reactivate_callback, state="disabled")
        reactivate_button.pack(side='left', padx=5, pady=5)
        
        return {
            'edit_button': edit_button,
            'delete_button': delete_button,
            'checkout_button': checkout_button,
            'reactivate_button': reactivate_button
        }
        
    except Exception as e:
        logger.log_error("Aksiyon çerçevesi oluşturma hatası", e)
        raise
