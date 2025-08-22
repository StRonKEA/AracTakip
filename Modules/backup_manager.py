# Modules/backup_manager.py
import os
import calendar
import zipfile
import time
import tempfile
import shutil
import gc  # <-- Gerekli modül eklendi
from datetime import datetime, time as dt_time, timedelta
from Modules.custom_windows import BackupNotificationWindow
from Modules.logger import logger

class BackupManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.last_monthly_backup = None
        
    def start_schedulers(self):
        """Tüm zamanlayıcıları başlatır."""
        self.schedule_daily_backup()
        logger.log_info("Yedekleme zamanlayıcıları başlatıldı")
        
    def schedule_daily_backup(self):
        """Her gün gece yarısı için yedeklemeyi zamanlar."""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        next_midnight = datetime.combine(tomorrow.date(), dt_time(0, 0))
        ms_until_midnight = int((next_midnight - now).total_seconds() * 1000)
        self.app.root.after(ms_until_midnight, self._perform_midnight_tasks)

    def _perform_midnight_tasks(self):
        """Gece yarısı yapılacak tüm işlemleri yürütür."""
        logger.log_info("Gece yarısı bakım görevleri başlatılıyor.")
        self.perform_backup(is_auto=True)
        
        now = datetime.now()
        is_last_day = now.day == calendar.monthrange(now.year, now.month)[1]
        if is_last_day and self.last_monthly_backup != now.month:
            self._perform_monthly_backup()
        
        self.schedule_daily_backup()

    def _perform_monthly_backup(self):
        """Aylık yedekleme işlemini başlatır."""
        notification = BackupNotificationWindow(self.app.root, title="Aylık Yedekleme", message="Ay sonu yedeklemesi yapılıyor...")
        self.app.root.after(100, lambda: self._backup_task(notification, is_monthly=True))

    def perform_backup(self, manual=False, is_auto=False):
        """Standart yedekleme işlemini başlatır."""
        title = "Otomatik Yedekleme" if is_auto else "Manuel Yedekleme"
        message = "Yedekleme yapılıyor, lütfen bekleyin..."
        notification = BackupNotificationWindow(self.app.root, title=title, message=message)
        self.app.root.after(100, lambda: self._backup_task(notification, manual=manual))

    def _backup_task(self, notification, manual=False, is_monthly=False):
        """Yedekleme ve sıkıştırma görevini en sağlam yöntemle yürütür."""
        final_backup_path = None
        temp_dir = None
        try:
            base_path = self.app.settings.get('backup_path', 'Yedekler')
            now = datetime.now()
            
            if is_monthly:
                subfolder = "Aylik"
                prev_month_date = now - timedelta(days=1)
                month_name = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][prev_month_date.month - 1]
                timestamp = f"{prev_month_date.year}_{prev_month_date.month:02d}_{month_name}"
            elif manual:
                subfolder = "Manuel"
                timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            else:
                subfolder = "Gunluk"
                timestamp = now.strftime("%Y-%m-%d")

            dest_folder = os.path.join(base_path, subfolder)
            os.makedirs(dest_folder, exist_ok=True)
            
            db_name = os.path.splitext(os.path.basename(self.app.db.db.db_path))[0]
            db_backup_filename = f"{db_name}_{timestamp}.db"
            
            temp_dir = tempfile.mkdtemp()
            temp_db_path = os.path.join(temp_dir, db_backup_filename)
            
            # Veritabanı bağlantısını bu blok içinde açıp kapattığından emin ol
            self.app.db.db.backup_database(temp_db_path)

            if self.app.settings.get('enable_backup_compression', True):
                final_backup_path = os.path.join(dest_folder, f"{db_name}_{timestamp}.zip")
                with zipfile.ZipFile(final_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(temp_db_path, db_backup_filename)
            else:
                final_backup_path = os.path.join(dest_folder, db_backup_filename)
                shutil.copy2(temp_db_path, final_backup_path)

            logger.log_info(f"Yedekleme tamamlandı: {final_backup_path}")
            
            if subfolder == "Gunluk":
                retention_map = {"7 Gün": 7, "45 Gün": 45}
                retention_days = retention_map.get(self.app.settings.get('daily_retention', '45 Gün'), 45)
                self.app.db.db.cleanup_old_backups(dest_folder, retention_days, db_name)
            
            if is_monthly: self.last_monthly_backup = now.month
            if not manual: self.app.last_backup_date = now.date()
            
            message = f"Yedekleme başarıyla tamamlandı.\nDosya: {os.path.basename(final_backup_path)}"
        except Exception as e:
            logger.log_error("Yedekleme hatası", e)
            message = f"Yedekleme sırasında bir hata oluştu!"
        finally:
            # --- HATA DÜZELTMESİNİN SON VE EN GÜÇLÜ HALİ ---
            # Geçici klasörü ve içindekileri silmeden önce tüm referansları temizle
            temp_db_path = None
            gc.collect()  # Python'un çöp toplayıcısını zorla çalıştır
            time.sleep(0.5) # İşletim sistemine dosyayı serbest bırakması için yarım saniye ver
            
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.log_error("Geçici yedekleme klasörü silinemedi", e)
            
            notification.on_complete(message)
            self.app.update_status_bar()

    def run_archive_process(self, date_str):
        notification = BackupNotificationWindow(self.app.root, title="Arşivleme", message="Kayıtlar arşivleniyor...")
        self.app.root.after(100, lambda: self._archive_task(notification, date_str))

    def _archive_task(self, notification, date_str):
        try:
            archive_folder = os.path.join(self.app.settings.get('backup_path', 'Yedekler'), "Arsiv")
            os.makedirs(archive_folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            archive_db_path = os.path.join(archive_folder, f"arsiv_{timestamp}.db")
            
            count = self.app.db.db.archive_records_before_date(archive_db_path, date_str)
            message = f"{count} adet kayıt başarıyla arşivlendi."
            logger.log_info(f"Arşivleme tamamlandı: {count} kayıt")
        except Exception as e:
            logger.log_error("Arşivleme hatası", e)
            message = "Arşivleme sırasında bir hata oluştu!"
        finally:
            notification.on_complete(message)
            self.app.populate_treeview()