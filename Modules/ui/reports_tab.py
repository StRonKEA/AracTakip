# Modules/ui/reports_tab.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import calendar
from Modules.logger import logger

def create_reports_tab(parent, update_callback):
    """Raporlar sekmesi oluşturur."""
    try:
        reports_main_frame = ttk.Frame(parent)
        reports_main_frame.pack(expand=True, fill='both')
        
        options_frame = ttk.LabelFrame(reports_main_frame, text="Raporlama Seçenekleri", padding=(20, 10))
        options_frame.pack(fill='x', padx=10, pady=10)
        
        today = datetime.now()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        start_date_var = tk.StringVar(value=first_day.strftime("%d.%m.%Y"))
        end_date_var = tk.StringVar(value=last_day.strftime("%d.%m.%Y"))
        
        ttk.Label(options_frame, text="Başlangıç Tarihi:").pack(side='left', padx=5)
        ttk.Entry(options_frame, textvariable=start_date_var, width=12).pack(side='left', padx=5)
        
        ttk.Label(options_frame, text="Bitiş Tarihi:").pack(side='left', padx=5)
        ttk.Entry(options_frame, textvariable=end_date_var, width=12).pack(side='left', padx=5)
        
        ttk.Button(options_frame, text="Rapor Oluştur", 
                  command=update_callback, style="Accent.TButton").pack(side='left', padx=10)
        
        canvas = tk.Canvas(reports_main_frame)
        scrollbar = ttk.Scrollbar(reports_main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        report_widgets = {}
        report_specs = {
            "📊 Genel Bakış": (("Tarih", 150), ("Giriş Sayısı", 100)),
            "🏢 Firma Analizi": (("Sıra", 50), ("Firma", 300), ("Giriş Sayısı", 100)),
            "👤 Sürücü Performansı": (("Sıra", 50), ("Sürücü", 300), ("Giriş Sayısı", 100)),
            "🚚 Araç Sıklığı": (("Sıra", 50), ("Plaka", 150), ("Giriş Sayısı", 100))
        }
        
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.columnconfigure(1, weight=1)
        
        for i, (title, columns) in enumerate(report_specs.items()):
            row, col = i // 2, i % 2
            card = ttk.LabelFrame(scrollable_frame, text=title, padding=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.rowconfigure(0, weight=1)
            card.columnconfigure(0, weight=1)
            
            tree = ttk.Treeview(card, columns=[c[0] for c in columns], show="headings", height=6)
            for col_name, col_width in columns:
                tree.heading(col_name, text=col_name)
                tree.column(col_name, width=col_width, anchor="center")
            
            tree.pack(expand=True, fill="both")
            report_widgets[title] = tree
        
        return {
            'start_date_var': start_date_var,
            'end_date_var': end_date_var,
            'report_widgets': report_widgets,
            'scrollable_frame': scrollable_frame
        }
        
    except Exception as e:
        logger.log_error("Raporlar sekmesi oluşturma hatası", e)
        raise

def update_reports_data_on_ui(report_widgets, report_data):
    """Rapor verilerini UI'da günceller."""
    for report_name, tree in report_widgets.items():
        for i in tree.get_children():
            tree.delete(i)
    
    if not report_data:
        for tree in report_widgets.values():
            tree.insert("", "end", values=("Veri bulunamadı.", ""))
        return
    
    report_functions = {
        "📊 Genel Bakış": lambda: [("Toplam Giriş", sum(c for d, c in report_data.get('entry_data', [])))] + 
                                 [(datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y"), c) for d, c in report_data.get('entry_data', [])],
        "🏢 Firma Analizi": lambda: [(i, f, c) for i, (f, c) in enumerate(report_data.get('top_firms', []), 1)],
        "👤 Sürücü Performansı": lambda: [(i, d, c) for i, (d, c) in enumerate(report_data.get('top_drivers', []), 1)],
        "🚚 Araç Sıklığı": lambda: [(i, v, c) for i, (v, c) in enumerate(report_data.get('top_vehicles', []), 1)]
    }
    
    for name, func in report_functions.items():
        data = func()
        tree = report_widgets[name]
        if data:
            for row in data:
                tree.insert("", "end", values=row)
        else:
            tree.insert("", "end", values=("Veri bulunamadı.", ""))
