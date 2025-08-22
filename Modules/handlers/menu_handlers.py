# Modules/handlers/menu_handlers.py
import os
import sys
import webbrowser
import pandas as pd
from tkinter import filedialog
from Modules.settings import SettingsWindow
from Modules.blacklist import BlacklistManager
from Modules.reporting import CustomReportGenerator
from Modules.custom_windows import CustomMessageBox, AboutWindow
from Modules.helpers import get_db_path, get_log_dir
from Modules.logger import logger

def open_settings_window(app):
    """Ayarlar penceresini açar."""
    SettingsWindow(app.root, app.settings, app)

def export_to_excel(app):
    """Mevcut treeview'daki veriyi Excel'e aktarır."""
    try:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Excel Dosyaları", "*.xlsx")], 
            title="Excel'e Aktar"
        )
        
        if file_path:
            data = [app.tree.item(item)['values'] for item in app.tree.get_children()]
            if not data:
                CustomMessageBox(app.root, "Uyarı", "Aktarılacak veri yok.", 'info')
                return
            
            df = pd.DataFrame(data, columns=app.tree["columns"])
            df.to_excel(file_path, index=False)
            
            CustomMessageBox(app.root, "Başarılı", 
                f"Veriler '{os.path.basename(file_path)}' dosyasına aktarıldı.", 'info')
            logger.log_info(f"Excel'e aktarıldı: {file_path}")
            
    except Exception as e:
        logger.log_error("Excel aktarım hatası", e)
        CustomMessageBox(app.root, "Hata", f"Excel'e aktarım sırasında hata oluştu: {e}", 'info')

def open_custom_report_generator(app):
    """Özel rapor oluşturucu penceresini açar."""
    CustomReportGenerator(app.root, app.db)

def open_blacklist_manager(app):
    """Kara liste yöneticisi penceresini açar."""
    BlacklistManager(app.root, app.db)

def manual_backup(app):
    """Manuel yedekleme işlemini tetikler."""
    app.backup_manager.perform_backup(manual=True)

def restore_from_backup(app):
    """Yedekten geri yükleme işlemini yönetir."""
    try:
        file_path = filedialog.askopenfilename(
            initialdir=app.settings['backup_path'], 
            title="Yedek Seçin", 
            filetypes=[("Veritabanı Dosyaları", "*.db")]
        )
        
        if file_path:
            confirm_dialog = CustomMessageBox(app.root, "Onay", 
                "Mevcut veritabanı seçilenle değiştirilecek. Bu işlem geri alınamaz. Emin misiniz?", 'yesno')
            
            if confirm_dialog.result:
                app.db.db.close()
                import shutil
                shutil.copyfile(file_path, get_db_path())
                
                CustomMessageBox(app.root, "Başarılı", 
                    "Veritabanı geri yüklendi. Programın doğru çalışması için yeniden başlatılacak.", 'info')
                logger.log_info(f"Veritabanı geri yüklendi: {file_path}")
                
                app.root.destroy()
                os.execl(sys.executable, sys.executable, *sys.argv)

    except Exception as e:
        logger.log_error("Geri yükleme hatası", e)
        CustomMessageBox(app.root, "Hata", f"Geri yükleme sırasında hata: {e}", 'info')

def show_error_logs(app):
    """Hata kayıtları klasörünü açar."""
    log_dir = get_log_dir()
    
    if os.path.exists(log_dir) and os.listdir(log_dir):
        try:
            os.startfile(log_dir)
        except AttributeError:
            webbrowser.open(log_dir)
    else:
        CustomMessageBox(app.root, "Bilgi", "Henüz kaydedilmiş bir hata bulunmuyor.", 'info')

def show_about(app):
    """Hakkında penceresini gösterir."""
    AboutWindow(app.root)
