# main_app.py
import tkinter as tk
from tkinter import ttk
import sv_ttk
from datetime import datetime, timedelta
import os
import calendar

# Modüllerden importlar
from database import Database
from Modules.database_service import DatabaseService
from Modules.helpers import get_db_path
from Modules.backup_manager import BackupManager
from Modules.logger import logger
from Modules.virtualized_treeview import VirtualizedTreeview
from Modules.custom_windows import CustomMessageBox

# UI importları
from Modules.ui.menu import create_main_menu
from Modules.ui.main_tab_widgets import create_form_frame, create_filter_frame, create_actions_frame
from Modules.ui.reports_tab import create_reports_tab
from Modules.ui.treeview_setup import create_treeview, populate_treeview_data, create_right_click_menu, update_right_click_menu_state

# Handler importları
from Modules.handlers import main_handlers, menu_handlers, window_handlers

class VehicleApp:
    def __init__(self, root, settings):
        try:
            logger.log_info("VehicleApp başlatılıyor")
            self.root = root
            self.settings = settings
            sv_ttk.set_theme(self.settings.get('theme', 'light'))
            
            db_instance = Database(get_db_path())
            self.db = DatabaseService(db_instance)
            self.backup_manager = BackupManager(self)
            
            self.root.title("Sönmez Flament Araç Takip Programı")
            self.root.state('zoomed')
            self.root.minsize(1200, 750)
            
            self.setup_variables()
            self.apply_styles()
            self.create_widgets()
            
            self.check_virtualization_and_populate()
            self.backup_manager.start_schedulers()
            
            self.root.after(100, self.center_window)
            logger.log_info("VehicleApp başarıyla başlatıldı")
            
        except Exception as e:
            logger.log_error("VehicleApp başlatma hatası", e)
            raise

    def setup_variables(self):
        self.last_backup_date = datetime.now().date() - timedelta(days=1)
        self.use_virtualization_for_current_data = False
        self.placeholder_map = {
            "Plaka": "Plaka giriniz", "Dorse": "Dorse plakası (varsa)", 
            "Sürücü": "Sürücü adı soyadı", "Telefon": "Telefon numarası", 
            "Sürücünün": "Sürücü firma adı", "Gelinen": "Gelinen firma adı"
        }

    def apply_styles(self):
        style = ttk.Style()
        style.configure('Bold.TLabel', font=('Segoe UI', 9, 'bold'))
        style.configure("Success.TButton")
        style.configure("Danger.TButton")

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(expand=True, fill="both")
        
        self.create_menu_bar()
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.main_tab = ttk.Frame(self.notebook)
        self.reports_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Ana Kayıtlar")
        self.notebook.add(self.reports_tab, text="Raporlar ve İstatistikler")
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: window_handlers.on_tab_change(self, e))

        self.create_main_tab_widgets()
        self.create_reports_tab_widgets()
        self.setup_system_status(main_container)
        
        self.tree.bind("<<TreeviewSelect>>", self.update_action_buttons_state)

    def create_menu_bar(self):
        menu_commands = {
            'settings': lambda: menu_handlers.open_settings_window(self),
            'export_excel': lambda: menu_handlers.export_to_excel(self),
            'custom_report': lambda: menu_handlers.open_custom_report_generator(self),
            'blacklist': lambda: menu_handlers.open_blacklist_manager(self),
            'exit': self.root.quit,
            'backup_now': lambda: menu_handlers.manual_backup(self),
            'restore_backup': lambda: menu_handlers.restore_from_backup(self),
            'show_errors': lambda: menu_handlers.show_error_logs(self),
            'about': lambda: menu_handlers.show_about(self)
        }
        self.menu_bar = create_main_menu(self.root, menu_commands)

    def create_main_tab_widgets(self):
        form_data = create_form_frame(self.main_tab, self.placeholder_map, lambda: main_handlers.add_record(self), self.clear_form)
        self.entries, self.notes_entry = form_data['entries'], form_data['notes_entry']
        
        years = [str(y) for y in range(datetime.now().year, datetime.now().year - 6, -1)]
        months = { "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6, "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12 }
        
        filter_data = create_filter_frame(self.main_tab, years, months, lambda: main_handlers.apply_filters(self), lambda s: main_handlers.filter_by_status(self, s), lambda: main_handlers.on_search(self))
        self.year_var, self.month_var, self.search_var = filter_data['year_var'], filter_data['month_var'], filter_data['search_var']
        self.inside_button, self.checked_out_button = filter_data['inside_button'], filter_data['checked_out_button']
        self.filter_status_label = filter_data['filter_status_label']
        
        action_data = create_actions_frame(self.main_tab, self.open_editor_window, lambda: main_handlers.delete_record(self), lambda: main_handlers.checkout_selected(self), lambda: main_handlers.reactivate_record(self))
        self.edit_button, self.delete_button = action_data['edit_button'], action_data['delete_button']
        self.checkout_button, self.reactivate_button = action_data['checkout_button'], action_data['reactivate_button']
        
        tree_data = create_treeview(self.main_tab, self.settings)
        self.tree, self.pagination_frame = tree_data['tree'], tree_data['pagination_frame']
        
        self.create_pagination_controls()
        
        self.right_click_menu = create_right_click_menu(self.root, self.add_empty_row, self.open_editor_window, lambda: main_handlers.reactivate_record(self), lambda: main_handlers.delete_record(self))
        self.tree.bind("<Button-3>", self.show_right_click_menu)

    def create_pagination_controls(self):
        self.prev_page_button = ttk.Button(self.pagination_frame, text="<< Önceki Sayfa", command=self._prev_page)
        self.prev_page_button.pack(side='left', padx=5)
        self.page_info_label = ttk.Label(self.pagination_frame, text="Sayfa 1/1", anchor="center")
        self.page_info_label.pack(side='left', expand=True, fill='x')
        self.next_page_button = ttk.Button(self.pagination_frame, text="Sonraki Sayfa >>", command=self._next_page)
        self.next_page_button.pack(side='right', padx=5)
        self.pagination_frame.grid_remove()
        
    def create_reports_tab_widgets(self):
        reports_data = create_reports_tab(self.reports_tab, lambda: window_handlers.update_reports_data(self))
        self.start_date_var, self.end_date_var, self.report_widgets = reports_data['start_date_var'], reports_data['end_date_var'], reports_data['report_widgets']

    def setup_system_status(self, parent):
        ttk.Separator(parent, orient='horizontal').pack(side='bottom', fill='x', padx=10)
        status_bar = ttk.Frame(parent)
        status_bar.pack(side='bottom', fill='x', padx=10, pady=5)
        
        db_frame = ttk.Frame(status_bar); db_frame.pack(side='left', padx=15, pady=0)
        ttk.Label(db_frame, text="Veritabanı:", style='Bold.TLabel').pack(side='left')
        self.db_status_label = ttk.Label(db_frame, text="Bağlanıyor...", font=("Segoe UI", 9)); self.db_status_label.pack(side='left', padx=5)
        
        backup_frame = ttk.Frame(status_bar); backup_frame.pack(side='left', padx=15, pady=0)
        ttk.Label(backup_frame, text="Günlük Yedek:", style='Bold.TLabel').pack(side='left')
        self.backup_status_label = ttk.Label(backup_frame, text="-", font=("Segoe UI", 9), cursor="hand2"); self.backup_status_label.pack(side='left', padx=5)
        self.backup_status_label.bind("<Button-1>", lambda e: self._show_last_backup_info())
        
        monthly_frame = ttk.Frame(status_bar); monthly_frame.pack(side='left', padx=15, pady=0)
        ttk.Label(monthly_frame, text="Aylık Yedek:", style='Bold.TLabel').pack(side='left')
        self.monthly_backup_status_label = ttk.Label(monthly_frame, text="-", font=("Segoe UI", 9), cursor="hand2"); self.monthly_backup_status_label.pack(side='left', padx=5)
        self.monthly_backup_status_label.bind("<Button-1>", lambda e: self._show_monthly_backup_info())
        
        error_frame = ttk.Frame(status_bar); error_frame.pack(side='left', padx=15, pady=0)
        ttk.Label(error_frame, text="Hata Durumu:", style='Bold.TLabel').pack(side='left')
        self.error_status_label = ttk.Label(error_frame, text="-", font=("Segoe UI", 9), cursor="hand2"); self.error_status_label.pack(side='left', padx=5)
        self.error_status_label.bind("<Button-1>", lambda e: menu_handlers.show_error_logs(self))
        
        self.root.after(1000, self.update_status_bar)

    def update_status_bar(self):
        try:
            db_status = self.db.check_connection()
            self.db_status_label.config(text="✅ Bağlı" if db_status else "❌ Bağlantı Hatası", foreground="green" if db_status else "red")
            
            days_ago = (datetime.now().date() - self.last_backup_date).days
            if days_ago == 0: status, color = "✅ Bugün alındı", "green"
            elif days_ago == 1: status, color = "⏰ Dün alındı", "orange"
            else: status, color = f"⏰ {days_ago} gündür alınmadı", "red"
            self.backup_status_label.config(text=status, foreground=color)
            
            monthly_status, monthly_color = self._get_monthly_backup_status()
            self.monthly_backup_status_label.config(text=monthly_status, foreground=monthly_color)
            
            error_status, error_color = self._get_error_status()
            self.error_status_label.config(text=error_status, foreground=error_color)
        except Exception as e:
            logger.log_error("Durum çubuğu güncelleme hatası", e)
        self.root.after(60000, self.update_status_bar)

    def _get_monthly_backup_status(self):
        now = datetime.now()
        is_last_day = now.day == calendar.monthrange(now.year, now.month)[1]
        last_backup_month = self.backup_manager.last_monthly_backup
        if last_backup_month == now.month: return "✅ Bu ay alındı", "green"
        if is_last_day: return "⚠️ Bugün alınacak", "orange"
        prev_month = now.month - 1 if now.month > 1 else 12
        if last_backup_month is not None and last_backup_month != prev_month: return "❌ Geçen ay alınmadı", "red"
        return "✅ Takip ediliyor", "green"

    def _get_error_status(self):
        from Modules.helpers import get_log_dir
        log_dir = get_log_dir()
        today_file = f"{datetime.now().strftime('%Y-%m-%d')}_hatalar.txt"
        error_file = os.path.join(log_dir, today_file)
        if os.path.exists(error_file) and os.path.getsize(error_file) > 0: return "❌ Bugün hata oluştu", "red"
        return "✅ Hatasız", "green"

    def _show_last_backup_info(self):
        CustomMessageBox(self.root, "Yedekleme Bilgisi", "Günlük yedekler her gece 00:00'da otomatik alınır.")

    def _show_monthly_backup_info(self):
        now = datetime.now()
        last_day = calendar.monthrange(now.year, now.month)[1]
        last_backup_month = self.backup_manager.last_monthly_backup or 'Hiç'
        CustomMessageBox(self.root, "Aylık Yedek Bilgisi", f"Aylık yedekler her ayın son günü ({last_day}. gün) otomatik alınır.\nSon alınan aylık yedek: {last_backup_month}. ay")
    
    def check_virtualization_and_populate(self):
        total_records = self.db.db.get_record_count()
        threshold = self.settings.get("virtualization_threshold", 100)
        self.use_virtualization_for_current_data = self.settings.get("enable_virtualization", True) and total_records > threshold
        self.populate_treeview()

    def populate_treeview(self, status_filter=None, date_filter=None, search_term=None):
        try:
            records = self.db.get_filtered_records(self.year_var, self.month_var, status_filter, date_filter, search_term)
            
            if self.use_virtualization_for_current_data and isinstance(self.tree, VirtualizedTreeview):
                processed_data = self._process_records_for_display(records)
                self.tree.set_data(processed_data)
            else:
                populate_treeview_data(self.tree, records, self.filter_status_label, status_filter, date_filter, search_term)
            
            self.update_status_counts()
            self._update_pagination_controls()
            self.update_action_buttons_state()
        except Exception as e:
            logger.log_error("Treeview doldurma hatası", e)

    def _process_records_for_display(self, records):
        """
        Veritabanı kayıtlarını Sanal Treeview için uygun formata dönüştürür.
        Artık (değerler, etiketler) formatında bir yapı döndürür.
        """
        processed = []
        for record in records:
            (id, plaka, dorse, surucu, tel, s_firma, g_firma, entry, exit, status, notes) = record
            try:
                entry_date = datetime.strptime(entry, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y") if entry else "-"
                entry_time = datetime.strptime(entry, "%Y-%m-%d %H:%M").strftime("%H:%M") if entry else "-"
                exit_zaman = datetime.strptime(exit, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M") if exit else "-"
            except (ValueError, TypeError):
                entry_date, entry_time, exit_zaman = entry, "", exit
            
            note_display = "🗒️ Not Var" if notes and notes.strip() else ""
            tag = ('checked_out',) if status == 'checked_out' else ('inside',)
            
            record_values = (id, entry_date, entry_time, plaka, dorse, surucu, tel, s_firma, g_firma, note_display, exit_zaman)
            
            # --- DEĞİŞİKLİK BURADA ---
            processed.append((record_values, tag))
            # --- DEĞİŞİKLİK BİTTİ ---

        return processed

    def update_status_counts(self):
        counts = self.db.get_status_counts(self.year_var, self.month_var)
        self.inside_button.config(text=f"Aktif İçeride: {counts['inside']}")
        self.checked_out_button.config(text=f"Çıkış Yapan: {counts['checked_out']}")

    def update_action_buttons_state(self, event=None):
        selected_item = self.tree.focus()
        state = "normal" if selected_item else "disabled"
        self.edit_button.config(state=state)
        self.delete_button.config(state=state)
        if selected_item:
            record_id = self.tree.item(selected_item)['values'][0]
            record_status = self.db.get_record_status(record_id)
            is_inside = (record_status == 'inside')
            self.checkout_button.config(state="normal" if is_inside else "disabled")
            self.reactivate_button.config(state="disabled" if is_inside else "normal")
        else:
            self.checkout_button.config(state="disabled")
            self.reactivate_button.config(state="disabled")

    def show_right_click_menu(self, event):
        selected_item = self.tree.identify_row(event.y)
        if selected_item:
            self.tree.selection_set(selected_item)
            record_id = self.tree.item(selected_item)['values'][0]
            record_status = self.db.get_record_status(record_id)
            update_right_click_menu_state(self.right_click_menu, record_status)
        self.right_click_menu.post(event.x_root, event.y_root)

    def clear_form(self):
        for key, entry in self.entries.items():
            entry.delete(0, 'end')
            placeholder = self.placeholder_map[key]
            entry.insert(0, placeholder)
            entry.config(foreground='grey')
        self.notes_entry.delete("1.0", "end")
        self.entries["Plaka"].focus()

    def open_editor_window(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        record_id = self.tree.item(selected_item)['values'][0]
        record = self.db.get_record_by_id(record_id)
        if not record: return
        
        editor = tk.Toplevel(self.root); editor.title("Kayıt Düzenle")
        labels = ["Plaka", "Dorse Plaka", "Sürücü", "Telefon", "Sürücü Firması", "Gelinen Firma", "Notlar", "Giriş Tarihi/Saati", "Çıkış Tarihi/Saati"]
        entries = {}
        data_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 10, 7: 7, 8: 8}
        
        for i, label in enumerate(labels):
            ttk.Label(editor, text=label).grid(row=i, column=0, padx=10, pady=5, sticky='w')
            entry = ttk.Entry(editor, width=40)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entry.insert(0, record[data_map.get(i)] or "")
            entries[label] = entry

        def save_changes():
            values = [e.get() for e in entries.values()]
            self.db.db.update_record(record_id, *values)
            self.check_virtualization_and_populate()
            editor.destroy()

        ttk.Button(editor, text="Değişiklikleri Kaydet", command=save_changes).grid(row=len(labels), columnspan=2, pady=10)
        editor.transient(self.root); editor.grab_set()

    def add_empty_row(self):
        CustomMessageBox(self.root, "Bilgi", "Bu özellik şu anda aktif değil.", 'info')

    def _prev_page(self):
        if isinstance(self.tree, VirtualizedTreeview) and self.tree.prev_page(): self._update_pagination_controls()

    def _next_page(self):
        if isinstance(self.tree, VirtualizedTreeview) and self.tree.next_page(): self._update_pagination_controls()

    def _update_pagination_controls(self):
        if self.use_virtualization_for_current_data and isinstance(self.tree, VirtualizedTreeview):
            self.pagination_frame.grid()
            self.page_info_label.config(text=self.tree.get_current_page_info())
            self.prev_page_button.config(state="normal" if self.tree.current_page > 0 else "disabled")
            self.next_page_button.config(state="normal" if self.tree.current_page < self.tree.total_pages - 1 else "disabled")
        else:
            self.pagination_frame.grid_remove()