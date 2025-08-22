# database.py
import sqlite3
import os
import shutil
from datetime import datetime, timedelta
from Modules.logger import logger

class Database:
    """
    SQLite veritabanı işlemlerini yöneten ana sınıf.
    Tüm veritabanı operasyonları burada.
    """
    
    def __init__(self, db_path):
        # Veritabanı dizinini oluştur
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        # Farklı thread'lerden erişime izin ver
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._update_schema()
        logger.log_info("Veritabanı bağlantısı kuruldu")

    def check_connection(self):
        """Bağlantıyı kontrol et"""
        try:
            self.cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.log_error("Veritabanı bağlantı hatası", e)
            return False

    def _update_schema(self):
        """Veritabanı şemasını oluşturur ve günceller."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT, dorsePlaka TEXT, surucu TEXT, telefon TEXT,
            surucuFirma TEXT, gelinenFirma TEXT, entryDate TEXT,
            exitDate TEXT, status TEXT, notes TEXT
        )""")
        
        self.cursor.execute("PRAGMA table_info(vehicles)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'notes' not in columns:
            self.cursor.execute("ALTER TABLE vehicles ADD COLUMN notes TEXT")
            
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
            value TEXT NOT NULL, reason TEXT, date_added TEXT,
            UNIQUE(type, value)
        )""")
        
        # Performans için indexler
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_entry_date ON vehicles(entryDate)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON vehicles(status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_plaka ON vehicles(plaka)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_surucu ON vehicles(surucu)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_gelinen_firma ON vehicles(gelinenFirma)")
        
        self.conn.commit()

    # --- TEMEL CRUD İŞLEMLERİ ---
    def add_record(self, plaka, dorsePlaka, surucu, telefon, surucuFirma, gelinenFirma, notes):
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        status = 'inside'
        params = (
            plaka.upper(), dorsePlaka.upper(), surucu.upper(), telefon.upper(),
            surucuFirma.upper(), gelinenFirma.upper(), notes, entry_time, status
        )
        self.cursor.execute("""
        INSERT INTO vehicles (plaka, dorsePlaka, surucu, telefon, surucuFirma, gelinenFirma, notes, entryDate, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, params)
        self.conn.commit()
        logger.log_info(f"Yeni kayıt eklendi: {plaka}")
        return True

    def fetch_records(self, year=None, month=None, status_filter=None, date_filter=None):
        query = "SELECT * FROM vehicles"
        conditions, params = [], []
        
        if year:
            conditions.append("strftime('%Y', entryDate) = ?")
            params.append(str(year))
        if month:
            conditions.append("strftime('%m', entryDate) = ?")
            params.append(f"{month:02d}")
        if status_filter in ['inside', 'checked_out']:
            conditions.append("status = ?")
            params.append(status_filter)
        if date_filter:
            if date_filter == 'today':
                start_date = datetime.now().strftime("%Y-%m-%d")
                conditions.append("strftime('%Y-%m-%d', entryDate) = ?")
                params.append(start_date)
            elif date_filter == 'yesterday':
                start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                conditions.append("strftime('%Y-%m-%d', entryDate) = ?")
                params.append(start_date)
            elif date_filter == 'last_7_days':
                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                end_date = datetime.now().strftime("%Y-%m-%d")
                conditions.append("entryDate BETWEEN ? AND ?")
                params.append(start_date)
                params.append(end_date + " 23:59")
                
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY id DESC"
        
        # Performans için: LIMIT ekle (çok büyük veri setleri için)
        if not any([year, month, status_filter, date_filter]):
            query += " LIMIT 5000"  # Filtre yoksa maksimum 5000 kayıt
        
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchall()

    def search_records(self, search_term):
        search_term = f"%{search_term.upper()}%"
        query = """
        SELECT * FROM vehicles WHERE
            UPPER(plaka) LIKE ? OR UPPER(dorsePlaka) LIKE ? OR UPPER(surucu) LIKE ? OR
            UPPER(telefon) LIKE ? OR UPPER(surucuFirma) LIKE ? OR UPPER(gelinenFirma) LIKE ? OR
            UPPER(notes) LIKE ?
        ORDER BY id DESC
        LIMIT 1000  # Arama sonuçlarını sınırla
        """
        params = (search_term,) * 7
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_record_by_id(self, record_id):
        self.cursor.execute("SELECT * FROM vehicles WHERE id = ?", (record_id,))
        return self.cursor.fetchone()

    def get_latest_record_by_plate(self, plate_number, plate_type='plaka'):
        column_name = "plaka" if plate_type == 'plaka' else "dorsePlaka"
        query = f"SELECT * FROM vehicles WHERE {column_name} = ? ORDER BY id DESC LIMIT 1"
        self.cursor.execute(query, (plate_number.upper(),))
        return self.cursor.fetchone()

    def update_record(self, record_id, plaka, dorsePlaka, surucu, telefon, surucuFirma, gelinenFirma, notes, entryDate, exitDate):
        params = (
            plaka.upper(), dorsePlaka.upper(), surucu.upper(), telefon.upper(),
            surucuFirma.upper(), gelinenFirma.upper(), notes, entryDate, exitDate, record_id
        )
        self.cursor.execute("""
        UPDATE vehicles SET plaka = ?, dorsePlaka = ?, surucu = ?, telefon = ?, 
        surucuFirma = ?, gelinenFirma = ?, notes = ?, entryDate = ?, exitDate = ? WHERE id = ?
        """, params)
        self.conn.commit()
        logger.log_info(f"Kayıt güncellendi: {record_id}")

    def delete_record(self, record_id):
        self.cursor.execute("DELETE FROM vehicles WHERE id = ?", (record_id,))
        self.conn.commit()
        logger.log_info(f"Kayıt silindi: {record_id}")

    def checkout_vehicle(self, record_id):
        exit_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute("UPDATE vehicles SET exitDate = ?, status = 'checked_out' WHERE id = ?", (exit_time, record_id))
        self.conn.commit()
        logger.log_info(f"Çıkış verildi: {record_id}")
        
    def reactivate_vehicle(self, record_id):
        self.cursor.execute("UPDATE vehicles SET exitDate = NULL, status = 'inside' WHERE id = ?", (record_id,))
        self.conn.commit()
        logger.log_info(f"Kayıt tekrar aktif yapıldı: {record_id}")

    # --- BLACKLIST İŞLEMLERİ ---
    def get_blacklist(self):
        self.cursor.execute("SELECT type, value, reason, date_added FROM blacklist ORDER BY date_added DESC")
        return self.cursor.fetchall()

    def is_blacklisted(self, item_value, item_type):
        self.cursor.execute("SELECT * FROM blacklist WHERE type = ? AND value = ?", (item_type.upper(), item_value.upper()))
        return self.cursor.fetchone()

    def add_to_blacklist(self, item_value, item_type, reason):
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            self.cursor.execute("INSERT INTO blacklist (type, value, reason, date_added) VALUES (?, ?, ?, ?)", 
                               (item_type.upper(), item_value.upper(), reason, date_added))
            self.conn.commit()
            logger.log_info(f"Kara listeye eklendi: {item_value}")
            return True
        except sqlite3.IntegrityError:
            logger.log_warning(f"Kara listede zaten var: {item_value}")
            return False

    def remove_from_blacklist(self, item_value, item_type):
        self.cursor.execute("DELETE FROM blacklist WHERE type = ? AND value = ?", (item_type.upper(), item_value.upper()))
        self.conn.commit()
        logger.log_info(f"Kara listeden kaldırıldı: {item_value}")

    # --- RAPORLAMA İŞLEMLERİ ---
    def get_status_counts(self, year, month):
        query_inside = "SELECT COUNT(*) FROM vehicles WHERE status = 'inside' AND strftime('%Y', entryDate) = ? AND strftime('%m', entryDate) = ?"
        query_checked_out = "SELECT COUNT(*) FROM vehicles WHERE status = 'checked_out' AND strftime('%Y', entryDate) = ? AND strftime('%m', entryDate) = ?"
        params = (str(year), f"{month:02d}")
        
        self.cursor.execute(query_inside, params)
        inside_count = self.cursor.fetchone()[0]
        
        self.cursor.execute(query_checked_out, params)
        checked_out_count = self.cursor.fetchone()[0]
        
        return inside_count, checked_out_count

    def get_entry_data_for_range(self, start_date, end_date):
        query = "SELECT strftime('%Y-%m-%d', entryDate) as day, COUNT(*) FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? GROUP BY day ORDER BY day ASC"
        self.cursor.execute(query, (start_date, end_date))
        return self.cursor.fetchall()

    def get_top_firms(self, start_date, end_date, limit=10):
        query = "SELECT gelinenFirma, COUNT(gelinenFirma) as count FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? AND gelinenFirma != '' GROUP BY gelinenFirma ORDER BY count DESC LIMIT ?"
        self.cursor.execute(query, (start_date, end_date, limit))
        return self.cursor.fetchall()

    def get_top_drivers(self, start_date, end_date, limit=10):
        query = "SELECT surucu, COUNT(surucu) as count FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? AND surucu != '' GROUP BY surucu ORDER BY count DESC LIMIT ?"
        self.cursor.execute(query, (start_date, end_date, limit))
        return self.cursor.fetchall()

    def get_top_vehicles(self, start_date, end_date, limit=10):
        query = "SELECT plaka, COUNT(plaka) as count FROM vehicles WHERE date(entryDate) BETWEEN ? AND ? AND plaka != '' GROUP BY plaka ORDER BY count DESC LIMIT ?"
        self.cursor.execute(query, (start_date, end_date, limit))
        return self.cursor.fetchall()

    # --- YEDEKLEME ve ARŞİV İŞLEMLERİ ---
    def backup_database(self, backup_path):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with sqlite3.connect(backup_path) as bck:
            self.conn.backup(bck)
        logger.log_info(f"Veritabanı yedeklendi: {backup_path}")
        return backup_path
    
    def cleanup_old_backups(self, backup_dir, retention_days, prefix):
        """Belirtilen klasördeki eski yedekleri siler."""
        if retention_days == 0:
            return
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        try:
            for filename in os.listdir(backup_dir):
                if filename.startswith(prefix) and filename.endswith(".db"):
                    try:
                        date_part = filename.split('_')[2]
                        file_date = datetime.strptime(date_part, "%Y-%m-%d")
                        if file_date < cutoff_date:
                            os.remove(os.path.join(backup_dir, filename))
                            logger.log_info(f"Eski yedek silindi: {filename}")
                    except (IndexError, ValueError):
                        continue
        except FileNotFoundError:
            logger.log_warning(f"Yedek klasörü bulunamadı, temizleme atlanıyor: {backup_dir}")
        except Exception as e:
            logger.log_error("Eski yedekleri temizlerken hata oluştu", e)
            
    def close(self):
        self.conn.close()
        logger.log_info("Veritabanı bağlantısı kapatıldı")

    def fetch_custom_report_data(self, start_date, end_date, filters=None):
        query = "SELECT * FROM vehicles WHERE date(entryDate) BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if filters:
            for column, value in filters.items():
                if value:
                    query += f" AND UPPER({column}) LIKE ?"
                    params.append(f"%{value.upper()}%")
                    
        query += " ORDER BY id DESC"
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchall()

    def get_oldest_record_date(self):
        self.cursor.execute("SELECT MIN(entryDate) FROM vehicles")
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else None

    def get_record_count_before_date(self, date_str):
        self.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE entryDate < ?", (date_str,))
        return self.cursor.fetchone()[0]

    def archive_records_before_date(self, archive_db_path, date_str):
        self.cursor.execute("SELECT * FROM vehicles WHERE entryDate < ?", (date_str,))
        records_to_archive = self.cursor.fetchall()
        
        if not records_to_archive:
            return 0
            
        archive_conn = sqlite3.connect(archive_db_path)
        archive_cursor = archive_conn.cursor()
        
        archive_cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER, plaka TEXT, dorsePlaka TEXT, surucu TEXT, telefon TEXT,
            surucuFirma TEXT, gelinenFirma TEXT, entryDate TEXT,
            exitDate TEXT, status TEXT, notes TEXT
        )""")
        
        archive_cursor.executemany("INSERT INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?)", records_to_archive)
        archive_conn.commit()
        archive_conn.close()
        
        self.cursor.execute("DELETE FROM vehicles WHERE entryDate < ?", (date_str,))
        self.conn.commit()
        
        logger.log_info(f"Arşivleme tamamlandı: {len(records_to_archive)} kayıt")
        return len(records_to_archive)

    def get_record_count(self):
        """Toplam kayıt sayısını döndür"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM vehicles")
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.log_error("Kayıt sayısı getirme hatası", e)
            return 0