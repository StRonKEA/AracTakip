import tkinter as tk
from tkinter import messagebox
import logging
import traceback
import sys
from datetime import datetime  # Tekrar import edilmişti, biri kaldırıldı
from Modules.helpers import load_settings
from Modules.logger import logger

def setup_basic_logging():
    """Temel logging kurulumu (ana logging çalışmazsa)"""
    try:
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    except:
        pass

def main():
    """Ana uygulama fonksiyonu"""
    try:
        # Önce ayarları yükle
        app_settings = load_settings()
        
        # Logging'i ayarlara göre kur
        logger.setup_logging(app_settings)
        logger.log_info("=" * 50)
        logger.log_info("UYGULAMA BAŞLATILIYOR")
        logger.log_info(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.log_info("=" * 50)
        
        from main_app import VehicleApp
        
        root = tk.Tk()
        logger.log_info("Tkinter penceresi oluşturuldu")
        
        app = VehicleApp(root, app_settings)
        logger.log_info("VehicleApp başlatıldı")
        
        root.mainloop()
        logger.log_info("Uygulama normal şekilde sonlandı")
        
    except Exception as e:
        error_msg = f"Uygulama başlatılamadı: {type(e).__name__}: {str(e)}"
        
        # Konsola mutlaka yazdır
        print(f"KRİTİK HATA: {error_msg}")
        traceback.print_exc()
        
        # Hata dosyasına da yazmayı dene
        try:
            from Modules.helpers import log_error
            log_error("Uygulama başlatma hatası", e)
        except:
            print("Hata kaydı da oluşturulamadı!")
        
        # Kullanıcıya göster
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Kritik Hata", 
                f"{error_msg}\n\nLütfen 'Hata_Kayitlari' klasörünü kontrol edin.")
            root.destroy()
        except:
            print("GUI de çalışmıyor!")
        
        sys.exit(1)

if __name__ == "__main__":
    # Temel loggingi kur
    setup_basic_logging()
    main()
