# Modules/helpers.py
import os
import sys
import json
import traceback
from datetime import datetime, timedelta

# --- AYAR YÖNETİMİ ---
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "theme": "light", 
    "font_size": "Normal", 
    "backup_freq": "Günlük", 
    "backup_path": "Yedekler", 
    "daily_retention": "45 Gün",
    "gunluk_temizleme": "30 Gün",
    "hata_temizleme": "30 Gün",
    "enable_virtualization": True,
    "virtualization_threshold": 100,  # <-- DEĞİŞİKLİK BURADA (150'den 100'e düşürüldü)
    "page_size": 100,
    "enable_backup_compression": True
}

def get_app_path():
    """Ana uygulama dizinini döndürür"""
    if getattr(sys, 'frozen', False): 
        return os.path.dirname(sys.executable)
    else: 
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_path():
    """Veritabanı yolunu döndürür"""
    app_path = get_app_path()
    db_dir = os.path.join(app_path, "Veritabanı")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "arac_veritabani.db")

def get_log_dir():
    """Hata kayıtları dizinini döndürür"""
    app_path = get_app_path()
    log_dir = os.path.join(app_path, "Hata_Kayitlari")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def get_gunluk_dir():
    """Günlük kayıtları dizinini döndürür"""
    app_path = get_app_path()
    gunluk_dir = os.path.join(app_path, "Gunluk")
    os.makedirs(gunluk_dir, exist_ok=True)
    return gunluk_dir

def load_settings():
    """Ayarları settings.json dosyasından yükler."""
    app_path = get_app_path()
    settings_file = os.path.join(app_path, SETTINGS_FILE)
    
    if not os.path.exists(settings_file):
        return DEFAULT_SETTINGS
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            for key, value in DEFAULT_SETTINGS.items():
                settings.setdefault(key, value)
            return settings
    except (json.JSONDecodeError, IOError) as e:
        log_error("Ayarlar yüklenirken hata", e)
        return DEFAULT_SETTINGS

def save_settings(settings):
    """Ayarları settings.json dosyasına kaydeder."""
    app_path = get_app_path()
    settings_file = os.path.join(app_path, SETTINGS_FILE)
    
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except IOError as e:
        log_error("Ayarlar kaydedilirken hata", e)

def temizleme_ayarini_gune_cevir(ayar):
    """Temizleme ayarını gün sayısına çevirir"""
    temizleme_map = {
        "1 Gün": 1, "7 Gün": 7, "30 Gün": 30,
        "3 Ay": 90, "6 Ay": 180, "1 Yıl": 365,
        "Temizleme": 0
    }
    return temizleme_map.get(ayar, 30)

def cleanup_logs(settings):
    """Logları ayarlara göre temizler"""
    try:
        log_dir = get_log_dir()
        gunluk_dir = get_gunluk_dir()
        
        gunluk_temizleme = temizleme_ayarini_gune_cevir(settings.get('gunluk_temizleme', '30 Gün'))
        hata_temizleme = temizleme_ayarini_gune_cevir(settings.get('hata_temizleme', '30 Gün'))
        
        def _clean_directory(directory, prefix, suffix, cutoff_days):
            if cutoff_days <= 0: return
            cutoff_date = datetime.now() - timedelta(days=cutoff_days)
            for filename in os.listdir(directory):
                if filename.startswith(prefix) and filename.endswith(suffix):
                    try:
                        date_str = filename.replace(prefix, "").replace(suffix, "").split('_')[0]
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if file_date < cutoff_date:
                            os.remove(os.path.join(directory, filename))
                    except (ValueError, IndexError):
                        continue
        
        _clean_directory(gunluk_dir, "gunluk_", ".log", gunluk_temizleme)
        _clean_directory(log_dir, "", "_hatalar.txt", hata_temizleme)
                        
    except Exception as e:
        log_error("Log temizleme hatası", e)

def manual_cleanup_logs():
    """Manuel log temizleme - bugünküler hariç tüm logları siler"""
    try:
        deleted_count = 0
        today_str = datetime.now().strftime('%Y-%m-%d')
        def _clean_manual(directory, check_func):
            nonlocal deleted_count
            for filename in os.listdir(directory):
                if check_func(filename, today_str):
                    try: os.remove(os.path.join(directory, filename)); deleted_count += 1
                    except OSError: pass
        
        _clean_manual(get_gunluk_dir(), lambda f, t: f.startswith("gunluk_") and t not in f)
        _clean_manual(get_log_dir(), lambda f, t: f.endswith("_hatalar.txt") and not f.startswith(t))
        return deleted_count
    except Exception as e:
        log_error("Manuel log temizleme hatası", e)
        return 0

def log_error(message, exception=None):
    """Detaylı hata kaydı oluşturur"""
    try:
        log_dir = get_log_dir()
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}_hatalar.txt")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\nZaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nHata: {message}\n")
            if exception:
                f.write(f"Exception Türü: {type(exception).__name__}\nException Mesajı: {str(exception)}\nTraceback:\n")
                traceback.print_exc(file=f)
            f.write(f"{'='*50}\n\n")
    except Exception: pass