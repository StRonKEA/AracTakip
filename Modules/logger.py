# Modules/logger.py
import logging
import os
import sys
from datetime import datetime

class AppLogger:
    """Merkezi logging sınıfı - Tüm uygulama için standart logging"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.setup_logging()
    
    def get_app_path(self):
        """Ana uygulama dizinini döndürür"""
        if getattr(sys, 'frozen', False): 
            return os.path.dirname(sys.executable)
        else: 
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def get_log_dir(self):
        """Hata kayıtları dizinini döndürür"""
        app_path = self.get_app_path()
        log_dir = os.path.join(app_path, "Hata_Kayitlari")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
    def get_gunluk_dir(self):
        """Günlük kayıtları dizinini döndürür"""
        app_path = self.get_app_path()
        gunluk_dir = os.path.join(app_path, "Gunluk")
        os.makedirs(gunluk_dir, exist_ok=True)
        return gunluk_dir
    
    def get_current_time(self):
        """Şu anki zamanı string olarak döndürür"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def setup_logging(self, settings=None):
        """Logging sistemini kur"""
        try:
            log_dir = self.get_log_dir()
            gunluk_dir = self.get_gunluk_dir()
            
            # Klasörleri oluştur
            os.makedirs(log_dir, exist_ok=True)
            os.makedirs(gunluk_dir, exist_ok=True)
            
            # Günlük dosyası yolu
            gunluk_file = os.path.join(gunluk_dir, f"gunluk_{datetime.now().strftime('%Y-%m-%d')}.log")
            
            # Mevcut handler'ları temizle
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            
            # Logging formatı
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # File handler - Günlük kayıtları
            file_handler = logging.FileHandler(
                gunluk_file, 
                mode='a', 
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            
            # Console handler - Sadece hatalar
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            
            # Root logger'ı ayarla
            logging.getLogger().setLevel(logging.DEBUG)
            logging.getLogger().addHandler(file_handler)
            logging.getLogger().addHandler(console_handler)
            
            # Bazı third-party loglarını sustur
            logging.getLogger('sqlite3').setLevel(logging.WARNING)
            logging.getLogger('PIL').setLevel(logging.WARNING)
            
            # İlk mesajı yaz
            self.log_info("=" * 50)
            self.log_info("LOGGING SİSTEMİ BAŞLATILDI")
            self.log_info(f"Tarih: {self.get_current_time()}")
            self.log_info("=" * 50)
            
        except Exception as e:
            # Fallback: basit konsol logging
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
            print(f"Logging kurulumunda hata: {e}")
    
    def log_debug(self, message):
        """Debug seviyesinde log"""
        logging.debug(message)
    
    def log_info(self, message):
        """Info seviyesinde log"""
        logging.info(message)
    
    def log_warning(self, message):
        """Warning seviyesinde log"""
        logging.warning(message)
    
    def log_error(self, message, exception=None):
        """Error seviyesinde log - Detaylı hata kaydı"""
        if exception:
            logging.error(f"{message}: {type(exception).__name__}: {str(exception)}", exc_info=True)
        else:
            logging.error(message)
    
    def log_critical(self, message, exception=None):
        """Critical seviyesinde log"""
        if exception:
            logging.critical(f"{message}: {type(exception).__name__}: {str(exception)}", exc_info=True)
        else:
            logging.critical(message)
    
    def get_logger(self, name):
        """Belirli bir modül için logger döndür"""
        logger = logging.getLogger(name)
        return logger

# Global logger instance - 📌 BURASI EKLENDİ
logger = AppLogger()