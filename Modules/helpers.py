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
    "daily_retention": "7 Gün",
    "gunluk_temizleme": "30 Gün",
    "hata_temizleme": "3 Ay",
    "enable_virtualization": True,
    "virtualization_threshold": 1000,
    "page_size": 100
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
        "1 Gün": 1,
        "7 Gün": 7,
        "30 Gün": 30,
        "3 Ay": 90,
        "6 Ay": 180,
        "1 Yıl": 365,
        "Temizleme": 0  # Temizleme yapma
    }
    return temizleme_map.get(ayar, 30)  # Varsayılan 30 gün

def cleanup_logs(settings):
    """Logları ayarlara göre temizler"""
    try:
        log_dir = get_log_dir()
        gunluk_dir = get_gunluk_dir()
        
        gunluk_temizleme = temizleme_ayarini_gune_cevir(settings.get('gunluk_temizleme', '30 Gün'))
        hata_temizleme = temizleme_ayarini_gune_cevir(settings.get('hata_temizleme', '3 Ay'))
        
        # Günlük kayıtlarını temizle
        if gunluk_temizleme > 0:
            gunluk_cutoff = datetime.now() - timedelta(days=gunluk_temizleme)
            for filename in os.listdir(gunluk_dir):
                if filename.startswith("gunluk_") and filename.endswith(".log"):
                    try:
                        file_date_str = filename.replace("gunluk_", "").replace(".log", "")
                        file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                        if file_date < gunluk_cutoff:
                            os.remove(os.path.join(gunluk_dir, filename))
                    except (ValueError, IndexError): 
                        continue
        
        # Hata kayıtlarını temizle
        if hata_temizleme > 0:
            hata_cutoff = datetime.now() - timedelta(days=hata_temizleme)
            for filename in os.listdir(log_dir):
                if filename.endswith("_hatalar.txt"):
                    try:
                        file_date_str = filename.split('_')[0]
                        file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                        if file_date < hata_cutoff:
                            os.remove(os.path.join(log_dir, filename))
                    except (ValueError, IndexError): 
                        continue
                        
    except Exception as e:
        log_error("Log temizleme hatası", e)

def manual_cleanup_logs():
    """Manuel log temizleme - tüm eski logları siler"""
    try:
        log_dir = get_log_dir()
        gunluk_dir = get_gunluk_dir()
        
        deleted_count = 0
        
        # Tüm günlük dosyalarını sil (bugünkü hariç)
        today_file = f"gunluk_{datetime.now().strftime('%Y-%m-%d')}.log"
        for filename in os.listdir(gunluk_dir):
            if filename.startswith("gunluk_") and filename.endswith(".log") and filename != today_file:
                try:
                    os.remove(os.path.join(gunluk_dir, filename))
                    deleted_count += 1
                except:
                    pass
        
        # Tüm hata dosyalarını sil (bugünkü hariç)
        today_error_file = f"{datetime.now().strftime('%Y-%m-%d')}_hatalar.txt"
        for filename in os.listdir(log_dir):
            if filename.endswith("_hatalar.txt") and filename != today_error_file:
                try:
                    os.remove(os.path.join(log_dir, filename))
                    deleted_count += 1
                except:
                    pass
        
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
            f.write(f"\n{'='*50}\n")
            f.write(f"Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Hata: {message}\n")
            
            if exception:
                f.write(f"Exception Türü: {type(exception).__name__}\n")
                f.write(f"Exception Mesajı: {str(exception)}\n")
                f.write(f"Traceback:\n")
                traceback.print_exc(file=f)
                
            f.write(f"{'='*50}\n\n")
            
    except Exception as log_exception:
        # Konsola yazdır ama tekrar hata verme döngüsüne girmeyelim
        print(f"HATA KAYDI OLUŞTURULAMADI: {log_exception}")

def setup_logging(settings):
    """Gelişmiş logging kurulumu - Artık logger.py'de"""
    pass