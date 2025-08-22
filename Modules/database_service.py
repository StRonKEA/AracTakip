# Modules/database_service.py
from datetime import datetime
from Modules.logger import logger

class DatabaseService:
    """
    UI için optimize edilmiş database wrapper.
    Sadece UI'nin ihtiyaç duyduğu metodları expose eder.
    """
    
    def __init__(self, db_instance):
        self.db = db_instance
        self.months = {
            "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6,
            "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12
        }
    
    def check_connection(self):
        """Bağlantı durumunu kontrol et"""
        try:
            return self.db.check_connection()
        except Exception as e:
            logger.log_error("Bağlantı kontrol hatası", e)
            return False
    
    def add_record(self, data, notes):
        """Yeni kayıt ekle - UI için optimize"""
        try:
            return self.db.add_record(
                data["Plaka"], data["Dorse"], data["Sürücü"], data["Telefon"],
                data["Sürücünün"], data["Gelinen"], notes
            )
        except Exception as e:
            logger.log_error("Kayıt ekleme hatası", e)
            return False
    
    def get_filtered_records(self, year_var, month_var, status_filter=None, date_filter=None, search_term=None):
        """Filtrelenmiş kayıtları getir - UI için optimize"""
        try:
            if search_term:
                return self.db.search_records(search_term)
            else:
                year = int(year_var.get()) if year_var.get() else datetime.now().year
                month = list(self.months.values())[list(self.months.keys()).index(month_var.get())] if month_var.get() else datetime.now().month
                return self.db.fetch_records(year=year, month=month, status_filter=status_filter, date_filter=date_filter)
        except Exception as e:
            logger.log_error("Kayıt getirme hatası", e)
            return []
    
    def get_status_counts(self, year_var, month_var):
        """Durum sayılarını getir - UI için optimize"""
        try:
            year = int(year_var.get()) if year_var.get() else datetime.now().year
            month = list(self.months.values())[list(self.months.keys()).index(month_var.get())] if month_var.get() else datetime.now().month
            
            inside, checked_out = self.db.get_status_counts(year, month)
            return {'inside': inside, 'checked_out': checked_out}
        except Exception as e:
            logger.log_error("Durum sayacı hatası", e)
            return {'inside': 0, 'checked_out': 0}
    
    def get_record_status(self, record_id):
        """Kayıt durumunu getir"""
        record = self.db.get_record_by_id(record_id)
        return record[9] if record else None  # status alanı
    
    def checkout_vehicle(self, record_id):
        """Araca çıkış ver"""
        self.db.checkout_vehicle(record_id)
    
    def reactivate_vehicle(self, record_id):
        """Kaydı tekrar aktif yap"""
        self.db.reactivate_vehicle(record_id)
    
    def delete_record(self, record_id):
        """Kaydı sil"""
        self.db.delete_record(record_id)
    
    # --- Blacklist metodları ---
    def get_blacklist(self):
        return self.db.get_blacklist()
    
    def is_blacklisted(self, item_value, item_type):
        return self.db.is_blacklisted(item_value, item_type)
    
    def add_to_blacklist(self, item_value, item_type, reason):
        return self.db.add_to_blacklist(item_value, item_type, reason)
    
    def remove_from_blacklist(self, item_value, item_type):
        self.db.remove_from_blacklist(item_value, item_type)
    
    # --- Raporlama metodları ---
    def get_report_data(self, start_date, end_date):
        """Rapor verilerini getir"""
        try:
            return {
                'entry_data': self.db.get_entry_data_for_range(start_date, end_date),
                'top_firms': self.db.get_top_firms(start_date, end_date),
                'top_drivers': self.db.get_top_drivers(start_date, end_date),
                'top_vehicles': self.db.get_top_vehicles(start_date, end_date)
            }
        except Exception as e:
            logger.log_error("Rapor verisi getirme hatası", e)
            return {}
    
    # --- Yedekleme ve arşiv metodları ---
    def backup_database(self, backup_path):
        return self.db.backup_database(backup_path)
    
    def cleanup_old_backups(self, backup_dir, retention_days, prefix):
        self.db.cleanup_old_backups(backup_dir, retention_days, prefix)
    
    def archive_records_before_date(self, archive_db_path, date_str):
        return self.db.archive_records_before_date(archive_db_path, date_str)
    
    def get_oldest_record_date(self):
        return self.db.get_oldest_record_date()
    
    def get_record_count_before_date(self, date_str):
        return self.db.get_record_count_before_date(date_str)
    
    def fetch_custom_report_data(self, start_date, end_date, filters=None):
        return self.db.fetch_custom_report_data(start_date, end_date, filters)
    
    def get_record_by_id(self, record_id):
        return self.db.get_record_by_id(record_id)