# Modules/reporting.py
import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import calendar
import webbrowser
import os
import traceback
from datetime import datetime
from Modules.custom_windows import CustomMessageBox
from Modules.helpers import get_app_path
from Modules.logger import logger

# PDF oluşturma için reportlab kütüphanesinden gerekli modülleri import et
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.log_warning("ReportLab kütüphanesi yüklü değil, PDF export özelliği devre dışı")

class CustomReportGenerator(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.parent = parent
        # 📌 DEĞİŞTİ: db → db.db (wrapper'dan ana database'e)
        self.db = db.db if hasattr(db, 'db') else db
        self.title("Özel Rapor Oluşturucu")
        self.transient(parent)
        self.grab_set()
        
        self.setup_pdf_font()
        self.available_columns = {
            "Giriş Tarihi": "entryDate", "Plaka": "plaka", "Dorse Plaka": "dorsePlaka", "Sürücü": "surucu",
            "Telefon": "telefon", "Sürücü Firması": "surucuFirma", "Gelinen Firma": "gelinenFirma",
            "Çıkış Tarihi": "exitDate", "Notlar": "notes", "Bekleme Süresi": "calculated_wait_time"
        }
        
        self.column_vars = {name: tk.BooleanVar(value=True) for name in self.available_columns}
        self.column_vars["Çıkış Tarihi"].set(False)
        self.column_vars["Notlar"].set(False)
        self.column_vars["Bekleme Süresi"].set(False)
        
        self._create_widgets()
        self.geometry("900x650")
        self.center_window(parent)
        self.wait_window(self)

    def setup_pdf_font(self):
        if not REPORTLAB_AVAILABLE:
            return
        
        self.pdf_font_name = 'Helvetica'
        fonts_to_try = [('SegoeUI', 'segoeui.ttf'), ('Arial', 'arial.ttf')]
        font_dir = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Fonts")
        
        for font_name, font_filename in fonts_to_try:
            try:
                font_path = os.path.join(font_dir, font_filename)
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.pdf_font_name = font_name
                    break
            except Exception as e:
                logger.log_warning(f"Font yükleme hatası: {font_name}", e)
                continue

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill="both")
        
        columns_frame = ttk.LabelFrame(main_frame, text="1. Raporda Gösterilecek Sütunları Seçin", padding=10)
        columns_frame.pack(fill="x", pady=(0, 10))
        
        for i, name in enumerate(self.available_columns):
            cb = ttk.Checkbutton(columns_frame, text=name, variable=self.column_vars[name], 
                                command=self._update_sort_combobox)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=5, pady=2)
        
        filter_frame = ttk.LabelFrame(main_frame, text="2. Verileri Filtreleyin (İsteğe Bağlı)", padding=10)
        filter_frame.pack(fill="x", pady=(0, 10))
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)
        
        self.filters = {}
        filter_map = {"Plaka": "plaka", "Sürücü": "surucu", "Gelinen Firma": "gelinenFirma"}
        
        for i, (label, col) in enumerate(filter_map.items()):
            ttk.Label(filter_frame, text=f"{label}:").grid(row=0, column=i*2, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(filter_frame)
            entry.grid(row=0, column=i*2+1, padx=5, pady=5, sticky="ew")
            self.filters[col] = entry
        
        today = datetime.now()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        ttk.Label(filter_frame, text="Başlangıç Tarihi:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.start_date_var = tk.StringVar(value=first_day.strftime("%d.%m.%Y"))
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(filter_frame, text="Bitiş Tarihi:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.end_date_var = tk.StringVar(value=last_day.strftime("%d.%m.%Y"))
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=15).grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        options_frame = ttk.LabelFrame(main_frame, text="3. Sıralama ve Çıktı Ayarları", padding=10)
        options_frame.pack(fill="x")
        
        ttk.Label(options_frame, text="Sırala:").pack(side="left", padx=5)
        self.sort_combo = ttk.Combobox(options_frame, state="readonly", width=15)
        self.sort_combo.pack(side="left", padx=5)
        
        self.sort_order_var = tk.StringVar(value="Artan")
        self.sort_order_combo = ttk.Combobox(options_frame, textvariable=self.sort_order_var, 
                                            values=["Artan", "Azalan"], state="readonly", width=8)
        self.sort_order_combo.pack(side="left", padx=5)
        
        ttk.Label(options_frame, text="Format:").pack(side="left", padx=(20, 5))
        self.format_var = tk.StringVar(value="Excel")
        self.format_combo = ttk.Combobox(options_frame, textvariable=self.format_var, 
                                        values=["Excel", "HTML", "PDF"], state="readonly", width=8)
        self.format_combo.pack(side="left", padx=5)
        
        self._update_sort_combobox()
        
        action_frame = ttk.Frame(main_frame, padding="10 20 0 0")
        action_frame.pack(fill="x")
        
        ttk.Button(action_frame, text="Rapor Oluştur", style="Accent.TButton", 
                  command=self._generate_report).pack(side="right")
        ttk.Button(action_frame, text="Kapat", command=self.destroy).pack(side="right", padx=10)

    def _update_sort_combobox(self):
        selected = [name for name, var in self.column_vars.items() if var.get()]
        self.sort_combo['values'] = selected
        
        if selected:
            current_selection = self.sort_combo.get()
            if not current_selection or current_selection not in selected:
                self.sort_combo.set(selected[0])

    def _generate_report(self):
        try:
            start_date = datetime.strptime(self.start_date_var.get(), "%d.%m.%Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            CustomMessageBox(self, "Hata", "Lütfen tarihleri GG.AA.YYYY formatında girin.", "info")
            return
        
        output_format = self.format_var.get()
        
        if output_format == "PDF" and not REPORTLAB_AVAILABLE:
            CustomMessageBox(self, "Hata", "PDF oluşturma için 'reportlab' kütüphanesi gerekli.\n\nLütfen komut satırına 'pip install reportlab' yazarak yükleyin.", "info")
            return
        
        filters = {col: entry.get().strip() for col, entry in self.filters.items()}
        selected_cols = [name for name, var in self.column_vars.items() if var.get()]
        
        if not selected_cols:
            CustomMessageBox(self, "Hata", "Lütfen en az bir sütun seçin.", "info")
            return
        
        # 📌 DEĞİŞTİ: self.db → self.db (artık doğrudan ana database)
        raw_data = self.db.fetch_custom_report_data(start_date, end_date, filters)
        
        if not raw_data:
            CustomMessageBox(self, "Bilgi", "Seçilen kriterlere uygun kayıt bulunamadı.", "info")
            return
        
        processed_data = self._process_data(raw_data)
        
        sort_by_display_name = self.sort_combo.get()
        sort_by_key = self.available_columns.get(sort_by_display_name)
        sort_reverse = self.sort_order_var.get() == "Azalan"
        
        if sort_by_key == 'calculated_wait_time':
            processed_data.sort(key=lambda x: x.get('wait_time_seconds', 0), reverse=sort_reverse)
        elif sort_by_key:
            processed_data.sort(key=lambda x: str(x.get(sort_by_key, '')), reverse=sort_reverse)
        
        df_data = [{col_name: row.get(self.available_columns[col_name]) for col_name in selected_cols} for row in processed_data]
        df = pd.DataFrame(df_data, columns=selected_cols)
        
        file_ext = f".{output_format.lower()}"
        file_path = filedialog.asksaveasfilename(
            defaultextension=file_ext, 
            filetypes=[(f"{output_format} Dosyaları", f"*{file_ext}")], 
            title=f"Raporu {output_format} Olarak Kaydet"
        )
        
        if not file_path:
            return
        
        try:
            if output_format == "Excel":
                df.to_excel(file_path, index=False)
                logger.log_info(f"Excel raporu oluşturuldu: {file_path}")
            elif output_format == "HTML":
                self._export_to_html(df, file_path)
                logger.log_info(f"HTML raporu oluşturuldu: {file_path}")
            elif output_format == "PDF":
                self._export_to_pdf(df, file_path)
                logger.log_info(f"PDF raporu oluşturuldu: {file_path}")
                
            CustomMessageBox(self, "Başarılı", f"Rapor başarıyla oluşturuldu:\n{os.path.basename(file_path)}", 'info')
            
            if output_format == "HTML":
                webbrowser.open(file_path)
                
        except Exception as e:
            CustomMessageBox(self, "Hata", f"Rapor oluşturulurken bir hata oluştu:\n{e}", 'info')
            logger.log_error("Rapor oluşturma hatası", e)
            
    def _process_data(self, data):
        results = []
        for row in data:
            record = dict(zip([desc[0] for desc in self.db.cursor.description], row))
            
            wait_str, wait_seconds = "-", 0
            if record.get('entryDate') and record.get('exitDate'):
                try:
                    start = datetime.strptime(record['entryDate'], "%Y-%m-%d %H:%M")
                    end = datetime.strptime(record['exitDate'], "%Y-%m-%d %H:%M")
                    delta = end - start
                    wait_seconds = delta.total_seconds()
                    
                    days, remainder = divmod(wait_seconds, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    wait_str = ""
                    if days > 0:
                        wait_str += f"{int(days)} gün "
                    if hours > 0:
                        wait_str += f"{int(hours)} sa "
                    if minutes > 0:
                        wait_str += f"{int(minutes)} dk"
                    
                    wait_str = wait_str.strip() or "0 dk"
                except (ValueError, TypeError):
                    wait_str = "Hesaplanamadı"
            
            record['calculated_wait_time'] = wait_str
            record['wait_time_seconds'] = wait_seconds
            
            try:
                if record.get('entryDate'):
                    record['entryDate'] = datetime.strptime(record['entryDate'], "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
                if record.get('exitDate'):
                    record['exitDate'] = datetime.strptime(record['exitDate'], "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
            except (ValueError, TypeError):
                pass
            
            results.append(record)
        
        return results

    def _export_to_html(self, df, file_path):
        html_template = """<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><title>Özel Rapor</title><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background-color:#f5f5f5;color:#333}h1{color:#005fb8}table{width:100%;border-collapse:collapse;margin-top:20px;box-shadow:0 2px 4px rgba(0,0,0,.1)}th,td{padding:12px 15px;text-align:left;border-bottom:1px solid #ddd}thead tr{background-color:#0078d4;color:#fff}tbody tr:nth-child(even){background-color:#f2f2f2}tbody tr:hover{background-color:#e2e2e2}</style></head><body><h1>Özel Rapor - {report_date}</h1>{table}</body></html>"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_template.format(
                report_date=datetime.now().strftime("%d.%m.%Y %H:%M"),
                table=df.to_html(index=False, escape=True, na_rep="-")
            ))

    def _export_to_pdf(self, df, file_path):
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = styles['h1']
        title_style.fontName = self.pdf_font_name
        title_style.textColor = colors.HexColor("#005fb8")
        
        title = Paragraph(f"Özel Rapor - {datetime.now().strftime('%d.%m.%Y')}", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        data = [df.columns.tolist()] + df.astype(str).values.tolist()
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0078d4")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.pdf_font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f2f2f2")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        table = Table(data)
        table.setStyle(style)
        story.append(table)
        doc.build(story)

    def center_window(self, parent):
        self.update_idletasks()
        parent_geo = parent.geometry().split('+')
        parent_x, parent_y = int(parent_geo[1]), int(parent_geo[2])
        parent_w, parent_h = [int(i) for i in parent_geo[0].split('x')]
        w, h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')