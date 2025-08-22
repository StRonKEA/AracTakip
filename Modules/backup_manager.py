# Modules/backup_manager.py
import os
import calendar
from datetime import datetime, time, timedelta
from Modules.custom_windows import BackupNotificationWindow
from Modules.logger import logger

class BackupManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.last_monthly_backup = None
        
    def start_schedulers(self):
        """Tüm zamanlayıcıları başlat"""
        self.schedule_backup_check()
        self.schedule_daily_backup()
        logger.log_info("Yedekleme zamanlayıcıları başlatıldı")
        
    def schedule_daily_backup(self):
        """Her gün gece 00:00'da yedek almak için zamanlayıcı"""
        try:
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            next_midnight = datetime.combine(tomorrow.date(), time(0, 0))
            
            seconds_until_midnight = (next_midnight - now).total_seconds()
            milliseconds_until_midnight = int(seconds_until_midnight * 1000)
            
            self.app.root.after(milliseconds_until_midnight, self._perform_midnight_backup)
            
        except Exception as e:
            logger.log_error("Günlük yedekleme zamanlayıcı hatası", e)
            self.app.root.after(3600000, self.schedule_daily_backup)

    def _perform_midnight_backup(self):
        """Gece yarısı otomatik yedekleme işlemi"""
        try:
            now = datetime.now()
            
            # 1. Günlük yedekleme yap (her gece)
            self.perform_backup(is_daily=True)
            
            # 2. Ayın son günü ise aylık yedek de al
            last_day_of_month = calendar.monthrange(now.year, now.month)[1]
            if now.day == last_day_of_month:
                if self.last_monthly_backup != now.month:
                    self._perform_monthly_backup()
                    self.last_monthly_backup = now.month
            
            # Yarın gece yarısı için tekrar zamanla
            self.schedule_daily_backup()
            
        except Exception as e:
            logger.log_error("Gece yarısı yedekleme hatası", e)
            self.schedule_daily_backup()

    def _perform_monthly_backup(self):
        """Aylık yedekleme işlemi - Tkinter thread-safe olmadığı için after kullanıyoruz"""
        try:
            notification = BackupNotificationWindow(
                self.app.root, 
                title="Aylık Yedekleme", 
                message="Ay sonu yedeklemesi yapılıyor...\nLütfen bekleyin."
            )
            
            # Threading yerine after ile zamanlı işlem
            self.app.root.after(100, lambda: self._monthly_backup_task(notification))
            
        except Exception as e:
            logger.log_error("Aylık yedekleme başlatma hatası", e)

    def _monthly_backup_task(self, notification):
        """Aylık yedekleme görevi - UI thread'inde çalışır"""
        try:
            base_path = self.app.settings['backup_path']
            now = datetime.now()
            previous_month = now.month - 1 if now.month > 1 else 12
            previous_year = now.year if now.month > 1 else now.year - 1
            
            monthly_folder = os.path.join(base_path, "Aylik")
            os.makedirs(monthly_folder, exist_ok=True)
            
            month_name = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][previous_month - 1]
            
            final_path = os.path.join(
                monthly_folder, 
                f"aylik_{previous_year}_{previous_month:02d}_{month_name}.db"
            )
            
            backup_path = self.app.db.db.backup_database(final_path)
            message = f"Aylık yedekleme tamamlandı!\n{month_name} {previous_year} ayı yedeği kaydedildi."
            logger.log_info(f"Aylık yedek alındı: {backup_path}")
            
            # Aylık yedek tarihini kaydet
            self.last_monthly_backup = now.month
            
        except Exception as e:
            logger.log_error("Aylık yedekleme hatası", e)
            message = "Aylık yedekleme sırasında hata oluştu!"
        finally:
            notification.on_complete(message)

    def perform_backup(self, manual=False, is_daily=False):
        """Yedekleme işlemi - Threading yerine after kullanıyoruz"""
        try:
            if not manual:
                countdown_time = 5
                notification = BackupNotificationWindow(
                    self.app.root, 
                    title="Yedekleme" if is_daily else "Manuel Yedekleme",
                    message=f"Yedekleme başlıyor...\n{countdown_time} saniye"
                )
                
                # Geri sayım animasyonu
                for i in range(countdown_time, 0, -1):
                    self.app.root.after((countdown_time - i) * 1000, 
                                       lambda x=i: notification.label.config(
                                           text=f"Yedekleme başlıyor...\n{x} saniye"
                                       ))
                
                # Geri sayım bitince yedeklemeyi başlat
                self.app.root.after(countdown_time * 1000, 
                                  lambda: self._backup_task(notification, manual, is_daily))
            else:
                notification = BackupNotificationWindow(
                    self.app.root, 
                    title="Manuel Yedekleme", 
                    message="Yedekleme yapılıyor, lütfen bekleyin..."
                )
                # Hemen yedeklemeyi başlat
                self.app.root.after(100, lambda: self._backup_task(notification, manual, is_daily))
                
        except Exception as e:
            logger.log_error("Yedekleme başlatma hatası", e)

    def _backup_task(self, notification, manual, is_daily):
        """Yedekleme görevi - UI thread'inde çalışır"""
        backup_path = None
        try:
            base_path = self.app.settings['backup_path']
            now = datetime.now()
            freq = self.app.settings['backup_freq']
            
            if manual:
                subfolder = "Manuel"
            elif is_daily:
                subfolder = "Gunluk"
            elif freq == "Haftalık":
                subfolder = "Haftalik"
            elif freq == "Aylık":
                subfolder = "Aylik"
            else:
                subfolder = "Gunluk"
            
            dest_folder = os.path.join(base_path, subfolder)
            timestamp = now.strftime("%Y-%m-%d_%H-%M")
            final_path = os.path.join(dest_folder, 
                f"{os.path.splitext(os.path.basename(self.app.db.db.db_path))[0]}_{timestamp}.db")
            
            backup_path = self.app.db.db.backup_database(final_path)
            
            # Günlük yedekler için temizleme
            if is_daily or subfolder == "Gunluk":
                retention_map = {"7 Gün": 7, "45 Gün": 45, "90 Gün": 90, "Tümünü Sakla": 0}
                retention_days = retention_map.get(self.app.settings['daily_retention'], 45)
                self.app.db.db.cleanup_old_backups(dest_folder, retention_days, 
                    os.path.splitext(os.path.basename(self.app.db.db.db_path))[0])

            logger.log_info(f"Yedekleme tamamlandı: {backup_path}")
            
        except Exception as e:
            logger.log_error("Yedekleme hatası", e)
        finally:
            success_message = f"Yedekleme başarıyla tamamlandı.\nKonum: {os.path.basename(backup_path)}" if backup_path else "Yedekleme sırasında hata oluştu!"
            notification.on_complete(success_message)
            
            if backup_path and not manual:
                self.app.last_backup_date = datetime.now().date()
            if backup_path:
                self.app.root.after(100, self.app.update_status_bar)

    def schedule_backup_check(self):
        """Yedekleme kontrol zamanlayıcısı"""
        try:
            now = datetime.now()
            freq = self.app.settings['backup_freq']
            should_backup = False
            
            if freq == "Günlük" and now.date() > self.app.last_backup_date:
                should_backup = True
            elif freq == "Haftalık" and now.weekday() == 6 and now.date() > self.app.last_backup_date:
                should_backup = True
            elif freq == "Aylık" and now.day == 1 and now.date() > self.app.last_backup_date:
                should_backup = True
                
            if should_backup:
                self.perform_backup()
                
            self.app.root.after(3600 * 1000, self.schedule_backup_check)
            
        except Exception as e:
            logger.log_error("Yedekleme kontrol hatası", e)

    def run_archive_process(self, date_str):
        """Arşivleme işlemi - Threading yerine after kullanıyoruz"""
        try:
            notification = BackupNotificationWindow(
                self.app.root, 
                title="Arşivleme", 
                message="Kayıtlar arşivleniyor, lütfen bekleyin..."
            )
            
            # Threading yerine after ile zamanlı işlem
            self.app.root.after(100, lambda: self._archive_task(notification, date_str))
            
        except Exception as e:
            logger.log_error("Arşivleme başlatma hatası", e)

    def _archive_task(self, notification, date_str):
        """Arşivleme görevi - UI thread'inde çalışır"""
        message = ""
        try:
            archive_folder = os.path.join(self.app.settings['backup_path'], "Arsiv")
            os.makedirs(archive_folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            archive_db_path = os.path.join(archive_folder, f"arsiv_{timestamp}.db")
            
            archived_count = self.app.db.db.archive_records_before_date(archive_db_path, date_str)
            message = f"{archived_count} adet kayıt başarıyla arşivlendi."
            logger.log_info(f"Arşivleme tamamlandı: {archived_count} kayıt")
            
        except Exception as e:
            logger.log_error("Arşivleme hatası", e)
            message = "Arşivleme sırasında bir hata oluştu!\nDetaylar hata kayıt dosyasına yazıldı."
        finally:
            notification.on_complete(message)
            self.app.root.after(100, self.app.populate_treeview)