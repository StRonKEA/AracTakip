# database.py
import sqlite3
import os
from datetime import datetime, timedelta
from Modules.logger import logger

class Database:
    def __init__(self, db_path):
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._update_schema()
        logger.log_info("Veritabanı bağlantısı kuruldu")

    def check_connection(self):
        try:
            self.cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _update_schema(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, plaka TEXT, dorsePlaka TEXT, 
            surucu TEXT, telefon TEXT, surucuFirma TEXT, gelinenFirma TEXT, 
            entryDate TEXT, exitDate TEXT, status TEXT, notes TEXT
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
            value TEXT NOT NULL, reason TEXT, date_added TEXT, UNIQUE(type, value)
        )""")
        # Indexler
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_entry_date ON vehicles(entryDate)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_plaka ON vehicles(plaka)")
        self.conn.commit()

    def add_record(self, plaka, dorsePlaka, surucu, telefon, surucuFirma, gelinenFirma, notes):
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        params = (plaka.upper(), dorsePlaka.upper(), surucu.upper(), telefon, surucuFirma.upper(), gelinenFirma.upper(), notes, entry_time, 'inside')
        self.cursor.execute("INSERT INTO vehicles (plaka, dorsePlaka, surucu, telefon, surucuFirma, gelinenFirma, notes, entryDate, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
        self.conn.commit()
        return True

    def fetch_records(self, year=None, month=None, status_filter=None, date_filter=None):
        query = "SELECT * FROM vehicles"
        conditions, params = [], []
        
        if year: conditions.append("strftime('%Y', entryDate) = ?"); params.append(str(year))
        if month: conditions.append("strftime('%m', entryDate) = ?"); params.append(f"{month:02d}")
        if status_filter: conditions.append("status = ?"); params.append(status_filter)
        
        if conditions: query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"
        
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchall()

    def search_records(self, search_term):
        term = f"%{search_term.upper()}%"
        query = "SELECT * FROM vehicles WHERE UPPER(plaka) LIKE ? OR UPPER(dorsePlaka) LIKE ? OR UPPER(surucu) LIKE ? OR UPPER(gelinenFirma) LIKE ? ORDER BY id DESC LIMIT 1000"
        self.cursor.execute(query, (term, term, term, term))
        return self.cursor.fetchall()

    def get_record_by_id(self, record_id):
        self.cursor.execute("SELECT * FROM vehicles WHERE id = ?", (record_id,))
        return self.cursor.fetchone()

    def update_record(self, record_id, plaka, dorsePlaka, surucu, telefon, surucuFirma, gelinenFirma, notes, entryDate, exitDate):
        params = (plaka.upper(), dorsePlaka.upper(), surucu.upper(), telefon, surucuFirma.upper(), gelinenFirma.upper(), notes, entryDate, exitDate, record_id)
        self.cursor.execute("UPDATE vehicles SET plaka=?, dorsePlaka=?, surucu=?, telefon=?, surucuFirma=?, gelinenFirma=?, notes=?, entryDate=?, exitDate=? WHERE id=?", params)
        self.conn.commit()

    def delete_record(self, record_id):
        self.cursor.execute("DELETE FROM vehicles WHERE id = ?", (record_id,))
        self.conn.commit()

    def checkout_vehicle(self, record_id):
        exit_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute("UPDATE vehicles SET exitDate = ?, status = 'checked_out' WHERE id = ?", (exit_time, record_id))
        self.conn.commit()
        
    def reactivate_vehicle(self, record_id):
        self.cursor.execute("UPDATE vehicles SET exitDate = NULL, status = 'inside' WHERE id = ?", (record_id,))
        self.conn.commit()

    def get_blacklist(self):
        self.cursor.execute("SELECT type, value, reason, date_added FROM blacklist ORDER BY date_added DESC")
        return self.cursor.fetchall()

    def add_to_blacklist(self, item_value, item_type, reason):
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            self.cursor.execute("INSERT INTO blacklist (type, value, reason, date_added) VALUES (?, ?, ?, ?)", (item_type.upper(), item_value.upper(), reason, date_added))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_from_blacklist(self, item_value, item_type):
        self.cursor.execute("DELETE FROM blacklist WHERE type = ? AND value = ?", (item_type.upper(), item_value.upper()))
        self.conn.commit()

    def get_status_counts(self, year, month):
        params = (str(year), f"{month:02d}")
        self.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'inside' AND strftime('%Y', entryDate) = ? AND strftime('%m', entryDate) = ?", params)
        inside = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'checked_out' AND strftime('%Y', entryDate) = ? AND strftime('%m', entryDate) = ?", params)
        checked_out = self.cursor.fetchone()[0]
        return inside, checked_out

    def get_entry_data_for_range(self, start_date, end_date):
        self.cursor.execute("SELECT strftime('%Y-%m-%d', entryDate), COUNT(*) FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? GROUP BY 1 ORDER BY 1 ASC", (start_date, end_date))
        return self.cursor.fetchall()

    def get_top_firms(self, start_date, end_date, limit=10):
        self.cursor.execute("SELECT gelinenFirma, COUNT(*) c FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? AND gelinenFirma != '' GROUP BY 1 ORDER BY 2 DESC LIMIT ?", (start_date, end_date, limit))
        return self.cursor.fetchall()

    def get_top_drivers(self, start_date, end_date, limit=10):
        self.cursor.execute("SELECT surucu, COUNT(*) c FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? AND surucu != '' GROUP BY 1 ORDER BY 2 DESC LIMIT ?", (start_date, end_date, limit))
        return self.cursor.fetchall()
        
    def get_top_vehicles(self, start_date, end_date, limit=10):
        self.cursor.execute("SELECT plaka, COUNT(*) c FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? AND plaka != '' GROUP BY 1 ORDER BY 2 DESC LIMIT ?", (start_date, end_date, limit))
        return self.cursor.fetchall()

    def backup_database(self, backup_path):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with sqlite3.connect(backup_path) as bck:
            self.conn.backup(bck)
        return backup_path
    
    def cleanup_old_backups(self, backup_dir, retention_days, prefix):
        """Belirtilen klasördeki eski .db veya .zip yedeklerini siler."""
        if retention_days <= 0: return
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for filename in os.listdir(backup_dir):
            if filename.startswith(prefix) and (filename.endswith(".db") or filename.endswith(".zip")):
                try:
                    # Dosya adından tarihi al (örn: arac_veritabani_2025-08-22.zip)
                    date_part = filename.split('_')[-1].split('.')[0]
                    file_date = datetime.strptime(date_part, "%Y-%m-%d")
                    if file_date < cutoff_date:
                        os.remove(os.path.join(backup_dir, filename))
                        logger.log_info(f"Eski yedek silindi: {filename}")
                except (IndexError, ValueError):
                    continue
            
    def get_oldest_record_date(self):
        self.cursor.execute("SELECT MIN(entryDate) FROM vehicles")
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_record_count_before_date(self, date_str):
        self.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE entryDate < ?", (date_str,))
        return self.cursor.fetchone()[0]

    def archive_records_before_date(self, archive_db_path, date_str):
        self.cursor.execute("SELECT * FROM vehicles WHERE entryDate < ?", (date_str,))
        records_to_archive = self.cursor.fetchall()
        if not records_to_archive: return 0
        
        archive_conn = sqlite3.connect(archive_db_path)
        archive_cursor = archive_conn.cursor()
        archive_cursor.execute("CREATE TABLE IF NOT EXISTS vehicles (id INTEGER, plaka TEXT, dorsePlaka TEXT, surucu TEXT, telefon TEXT, surucuFirma TEXT, gelinenFirma TEXT, entryDate TEXT, exitDate TEXT, status TEXT, notes TEXT)")
        archive_cursor.executemany("INSERT INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?)", records_to_archive)
        archive_conn.commit()
        archive_conn.close()
        
        self.cursor.execute("DELETE FROM vehicles WHERE entryDate < ?", (date_str,))
        self.conn.commit()
        return len(records_to_archive)

    def get_record_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM vehicles")
        return self.cursor.fetchone()[0]