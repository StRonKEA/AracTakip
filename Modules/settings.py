# Modules/settings.py
import tkinter as tk
from tkinter import ttk, filedialog
import calendar
from datetime import datetime, timedelta
from Modules.custom_windows import CustomMessageBox
from Modules.helpers import save_settings, manual_cleanup_logs
from Modules.logger import logger

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, current_settings, app_instance):
        super().__init__(parent)
        self.parent = parent
        self.app = app_instance
        self.title("Ayarlar")
        self.transient(parent)
        self.grab_set()
        
        self.settings = current_settings.copy()
        self.theme_var = tk.StringVar(value=self.settings['theme'])
        self.font_size_var = tk.StringVar(value=self.settings['font_size'])
        self.backup_freq_var = tk.StringVar(value=self.settings['backup_freq'])
        self.backup_path_var = tk.StringVar(value=self.settings['backup_path'])
        self.daily_retention_var = tk.StringVar(value=self.settings.get('daily_retention', '45 Gün'))
        self.gunluk_temizleme_var = tk.StringVar(value=self.settings.get('gunluk_temizleme', '30 Gün'))
        self.hata_temizleme_var = tk.StringVar(value=self.settings.get('hata_temizleme', '30 Gün'))
        self.archive_period_var = tk.StringVar(value="1 Yıllık Arşiv")

        main_container = ttk.Frame(self, padding="10")
        main_container.pack(expand=True, fill="both")
        main_container.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=0)
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        self.create_appearance_tab()
        self.create_backup_tab()
        self.create_log_tab()
        self.create_archive_tab()
        
        self.create_action_buttons(main_container)
        
        self.geometry("700x600")
        self.minsize(650, 550)
        self.center_window(parent)
        self.wait_window(self)
        logger.log_info("Ayarlar penceresi açıldı")

    def create_appearance_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="Görünüm")
        
        theme_frame = ttk.LabelFrame(tab, text="Uygulama Teması", padding=10)
        theme_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(theme_frame, text="Açık Tema", variable=self.theme_var, value="light").pack(anchor='w', padx=5)
        ttk.Radiobutton(theme_frame, text="Koyu Tema", variable=self.theme_var, value="dark").pack(anchor='w', padx=5)
        
        font_frame = ttk.LabelFrame(tab, text="Yazı Tipi Boyutu", padding=10)
        font_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(font_frame, text="Küçük", variable=self.font_size_var, value="Küçük").pack(anchor='w', padx=5)
        ttk.Radiobutton(font_frame, text="Normal", variable=self.font_size_var, value="Normal").pack(anchor='w', padx=5)
        ttk.Radiobutton(font_frame, text="Büyük", variable=self.font_size_var, value="Büyük").pack(anchor='w', padx=5)

    def create_backup_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="Yedekleme")
        
        freq_frame = ttk.LabelFrame(tab, text="Otomatik Yedekleme Sıklığı", padding=10)
        freq_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(freq_frame, text="Günlük", variable=self.backup_freq_var, value="Günlük").pack(anchor='w', padx=5)
        ttk.Radiobutton(freq_frame, text="Haftalık (Her Pazar)", variable=self.backup_freq_var, value="Haftalık").pack(anchor='w', padx=5)
        ttk.Radiobutton(freq_frame, text="Aylık (Ayın 1'i)", variable=self.backup_freq_var, value="Aylık").pack(anchor='w', padx=5)
        
        info_label = ttk.Label(freq_frame, text="Not: Günlük yedekler her gece 00:00'da otomatik alınır ve 45 gün saklanır.\nAylık yedekler her ayın son günü otomatik alınır.", 
                              foreground="blue", font=("Helvetica", 9, "italic"))
        info_label.pack(anchor='w', padx=5, pady=(10, 0))
        
        retention_frame = ttk.LabelFrame(tab, text="Günlük Yedek Saklama Süresi", padding=10)
        retention_frame.pack(fill='x', pady=5)
        
        ttk.Label(retention_frame, text="Bu ayar sadece 'Günlük' yedekleme için geçerlidir.").pack(anchor='w', padx=5, pady=(0,5))
        
        ttk.Radiobutton(retention_frame, text="Son 7 Günü Sakla", variable=self.daily_retention_var, value="7 Gün").pack(anchor='w', padx=5)
        ttk.Radiobutton(retention_frame, text="Son 45 Günü Sakla", variable=self.daily_retention_var, value="45 Gün").pack(anchor='w', padx=5)

        path_frame = ttk.LabelFrame(tab, text="Yedekleme Klasörü", padding=10)
        path_frame.pack(fill='x', pady=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.backup_path_var, state='readonly')
        path_entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        
        ttk.Button(path_frame, text="...", command=self._select_backup_path, width=4).pack(side='left')

    def create_log_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="Log Ayarları")
        
        gunluk_frame = ttk.LabelFrame(tab, text="Günlük Kayıt Temizleme", padding=10)
        gunluk_frame.pack(fill='x', pady=5)
        
        ttk.Label(gunluk_frame, text="Günlük dosyalarını şu sıklıkta temizle:").pack(anchor='w', padx=5, pady=(0,5))
        
        gunluk_options = ["1 Gün", "7 Gün", "30 Gün"]
        for option in gunluk_options:
            ttk.Radiobutton(gunluk_frame, text=option, variable=self.gunluk_temizleme_var, value=option).pack(anchor='w', padx=5)
        
        hata_frame = ttk.LabelFrame(tab, text="Hata Kayıt Temizleme", padding=10)
        hata_frame.pack(fill='x', pady=10)
        
        ttk.Label(hata_frame, text="Hata dosyalarını şu sıklıkta temizle:").pack(anchor='w', padx=5, pady=(0,5))
        
        hata_options = ["1 Gün", "7 Gün", "30 Gün"]
        for option in hata_options:
            ttk.Radiobutton(hata_frame, text=option, variable=self.hata_temizleme_var, value=option).pack(anchor='w', padx=5)
        
        temizleme_frame = ttk.LabelFrame(tab, text="Manuel Temizleme", padding=10)
        temizleme_frame.pack(fill='x', pady=10)
        
        ttk.Label(temizleme_frame, text="Tüm eski logları hemen temizle:").pack(anchor='w', padx=5, pady=(0,10))
        
        ttk.Button(temizleme_frame, text="Tüm Eski Logları Temizle", 
                  command=self._manual_cleanup, style="Accent.TButton").pack(pady=5)
        
        ttk.Label(temizleme_frame, text="Not: Bugünün logları silinmez", foreground="red", font=("Helvetica", 9)).pack(anchor='w', padx=5)

    def create_archive_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="Arşivleme")
        
        archive_frame = ttk.LabelFrame(tab, text="Veri Arşivleme ve Bakım", padding=10)
        archive_frame.pack(fill='x', pady=5)
        
        ttk.Label(archive_frame, text="Bu özellik, performansı artırmak için eski kayıtları\nana veritabanından ayrı bir arşiv dosyasına taşır.\nBu işlem geri alınamaz.", justify='left').pack(anchor='w', padx=5, pady=(0,10))
        
        info_frame = ttk.Frame(archive_frame)
        info_frame.pack(fill='x', pady=5)
        
        ttk.Label(info_frame, text="Mevcut Durum:", style='Bold.TLabel').pack(anchor='w', padx=5)
        self.archive_info_label = ttk.Label(info_frame, text="Hesaplanıyor...", foreground='blue')
        self.archive_info_label.pack(anchor='w', padx=5, pady=(0,10))
        
        ttk.Separator(archive_frame).pack(fill='x', pady=10)
        
        options_frame = ttk.Frame(archive_frame)
        options_frame.pack(fill='x', pady=10)
        
        ttk.Label(options_frame, text="Arşivlenecek Kayıtlar:", style='Bold.TLabel').pack(anchor='w', padx=5, pady=(5,0))
        
        archive_options = ["3 Aydan Eski", "6 Aydan Eski", "1 Yıllık Arşiv", "2 Yıllık Arşiv"]
        for option in archive_options:
            ttk.Radiobutton(options_frame, text=option, variable=self.archive_period_var, value=option).pack(anchor='w', padx=5)
        
        info_label = ttk.Label(archive_frame, text="Not: '1 Yıllık Arşiv' seçeneği geçen yılın tüm kayıtlarını arşivler.\nÖrneğin: 2025 Ocak ayında 2024 yılının tamamı arşivlenir.", 
                              foreground="green", font=("Helvetica", 9))
        info_label.pack(anchor='w', padx=5, pady=(5,0))
        
        button_frame = ttk.Frame(archive_frame)
        button_frame.pack(fill='x', pady=15)
        
        ttk.Button(button_frame, text="Seçilen Kayıtları Şimdi Arşivle", 
                  command=self._run_archive, style="Accent.TButton").pack()
        
        ttk.Label(archive_frame, text="Not: Arşivlenen kayıtlar ana veritabanından silinir\nve ayrı bir arşiv dosyasına taşınır.", 
                 foreground="red", font=("Helvetica", 9)).pack(anchor='w', padx=5, pady=(10,0))
        
        self.update_archive_info()

    def create_action_buttons(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(btn_frame, text="Kaydet ve Kapat", 
                   command=self._save_and_apply, style="Accent.TButton").pack(side='right')
        ttk.Button(btn_frame, text="İptal", 
                   command=self.destroy).pack(side='right', padx=10)

    def _select_backup_path(self):
        path = filedialog.askdirectory(title="Yedekleme Klasörünü Seçin", initialdir=self.backup_path_var.get())
        if path:
            self.backup_path_var.set(path)

    def _manual_cleanup(self):
        dialog = CustomMessageBox(self, "Onay", 
            "Tüm eski log dosyaları (bugünküler hariç) silinecektir.\nBu işlem geri alınamaz!\n\nDevam edilsin mi?", "yesno")
        
        if dialog.result:
            deleted_count = manual_cleanup_logs()
            CustomMessageBox(self, "Temizleme Tamamlandı", 
                f"{deleted_count} adet eski log dosyası silindi.\nBugünün logları korundu.", "info")

    def update_archive_info(self):
        try:
            oldest_date_str = self.app.db.get_oldest_record_date()
            if oldest_date_str:
                oldest_date = datetime.strptime(oldest_date_str, "%Y-%m-%d %H:%M")
                self.archive_info_label.config(text=f"En eski kayıt tarihi: {oldest_date.strftime('%d.%m.%Y')}")
            else:
                self.archive_info_label.config(text="Arşivlenecek eski kayıt bulunmuyor.")
        except Exception as e:
            self.archive_info_label.config(text="Arşiv bilgisi alınamadı")
            logger.log_error("Arşiv bilgisi alınamadı", e)

    def _run_archive(self):
        period = self.archive_period_var.get()
        
        current_year = datetime.now().year
        if period == "1 Yıllık Arşiv":
            start_date = f"{current_year - 1}-01-01"
            end_date = f"{current_year - 1}-12-31 23:59"
            display_text = f"{current_year - 1} yılı"
        elif period == "2 Yıllık Arşiv":
            start_date = f"{current_year - 2}-01-01"
            end_date = f"{current_year - 2}-12-31 23:59"
            display_text = f"{current_year - 2} yılı"
        else:
            period_map = {"3 Aydan Eski": 90, "6 Aydan Eski": 180}
            days_to_subtract = period_map.get(period, 90)
            archive_date_limit = datetime.now() - timedelta(days=days_to_subtract)
            start_date = "1900-01-01"
            end_date = archive_date_limit.strftime("%Y-%m-%d %H:%M")
            display_text = f"{period} ({archive_date_limit.strftime('%d.%m.%Y')}'den eski)"
        
        try:
            if period in ["1 Yıllık Arşiv", "2 Yıllık Arşiv"]:
                count = self.app.db.get_record_count_before_date(f"{current_year}-01-01")
            else:
                count = self.app.db.get_record_count_before_date(end_date)
                
        except Exception as e:
            CustomMessageBox(self, "Hata", f"Arşivleme sorgusu sırasında hata: {e}", "info")
            logger.log_error("Arşivleme sorgu hatası", e)
            return
        
        if count == 0:
            CustomMessageBox(self, "Bilgi", "Seçilen kritere uygun arşivlenecek kayıt bulunamadı.", "info")
            return
        
        if period in ["1 Yıllık Arşiv", "2 Yıllık Arşiv"]:
            msg = f"{display_text} kayıtları arşivlenecektir. Toplam {count} kayıt.\n\nBu işlem geri alınamaz! Emin misiniz?"
        else:
            msg = f"{display_text} {count} adet kayıt arşivlenecektir.\n\nBu işlem geri alınamaz! Emin misiniz?"
            
        dialog = CustomMessageBox(self, "Arşivleme Onayı", msg, "yesno")
        
        if dialog.result:
            if period in ["1 Yıllık Arşiv", "2 Yıllık Arşiv"]:
                self.app.backup_manager.run_archive_process(end_date)
            else:
                self.app.backup_manager.run_archive_process(end_date)

    def _save_and_apply(self):
        self.settings['theme'] = self.theme_var.get()
        self.settings['font_size'] = self.font_size_var.get()
        self.settings['backup_freq'] = self.backup_freq_var.get()
        self.settings['backup_path'] = self.backup_path_var.get()
        self.settings['daily_retention'] = self.daily_retention_var.get()
        self.settings['gunluk_temizleme'] = self.gunluk_temizleme_var.get()
        self.settings['hata_temizleme'] = self.hata_temizleme_var.get()
        
        save_settings(self.settings)
        self.app.settings = self.settings
        
        from Modules.helpers import cleanup_logs
        cleanup_logs(self.settings)
        
        CustomMessageBox(self, "Ayarlar Kaydedildi", 
            "Ayarlar kaydedildi ve log temizleme uygulandı.\nTema gibi bazı ayarların geçerli olması için programı yeniden başlatmanız gerekebilir.", 'info')
        logger.log_info("Ayarlar kaydedildi ve log temizleme uygulandı")
        self.destroy()

    def center_window(self, parent):
        self.update_idletasks()
        parent_geo = parent.geometry().split('+')
        parent_x, parent_y = int(parent_geo[1]), int(parent_geo[2])
        parent_w, parent_h = [int(i) for i in parent_geo[0].split('x')]
        w, h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')