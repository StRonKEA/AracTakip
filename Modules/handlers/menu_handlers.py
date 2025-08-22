# Modules/handlers/menu_handlers.py
import os
import sys
import webbrowser
import pandas as pd
import zipfile
import tempfile
from tkinter import filedialog
from Modules.settings import SettingsWindow
from Modules.blacklist import BlacklistManager
from Modules.reporting import CustomReportGenerator
from Modules.custom_windows import CustomMessageBox, AboutWindow
from Modules.helpers import get_db_path, get_log_dir
from Modules.logger import logger

def open_settings_window(app):
    SettingsWindow(app.root, app.settings, app)

def export_to_excel(app):
    try:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Excel Dosyaları", "*.xlsx")], 
            title="Excel'e Aktar"
        )
        if not file_path: return
        
        records = app.db.get_filtered_records(app.year_var, app.month_var, search_term=app.search_var.get())
        if not records:
            CustomMessageBox(app.root, "Uyarı", "Aktarılacak veri yok.", 'info')
            return
        
        columns = ["ID", "Plaka", "Dorse Plaka", "Sürücü", "Telefon", "Sürücü Firması", "Gelinen Firma", "Giriş Zamanı", "Çıkış Zamanı", "Durum", "Notlar"]
        df = pd.DataFrame(records, columns=columns)
        df.to_excel(file_path, index=False)
        
        CustomMessageBox(app.root, "Başarılı", f"Veriler başarıyla aktarıldı.", 'info')
    except Exception as e:
        logger.log_error("Excel aktarım hatası", e)
        CustomMessageBox(app.root, "Hata", f"Excel'e aktarım sırasında hata oluştu: {e}", 'info')

def open_custom_report_generator(app):
    CustomReportGenerator(app.root, app.db)

def open_blacklist_manager(app):
    BlacklistManager(app.root, app.db)

def manual_backup(app):
    app.backup_manager.perform_backup(manual=True)

def restore_from_backup(app):
    """Sıkıştırılmış veya normal yedekten geri yükleme yapar."""
    try:
        file_path = filedialog.askopenfilename(
            initialdir=app.settings.get('backup_path', 'Yedekler'), 
            title="Yedek Seçin", 
            filetypes=[("Yedek Dosyaları", "*.zip *.db")]
        )
        if not file_path: return

        if not CustomMessageBox(app.root, "Onay", "Mevcut veritabanı seçilenle değiştirilecek. Bu işlem geri alınamaz. Emin misiniz?", 'yesno').result:
            return

        app.db.db.close() # Mevcut veritabanı bağlantısını kapat
        
        db_to_restore = file_path
        temp_dir = None

        # Eğer dosya sıkıştırılmışsa, önce geçici bir dizine aç
        if file_path.endswith(".zip"):
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Zip içindeki ilk .db dosyasını bul ve aç
                db_filename = next((f for f in zip_ref.namelist() if f.endswith('.db')), None)
                if not db_filename:
                    raise Exception(".zip arşivi içinde .db dosyası bulunamadı.")
                zip_ref.extract(db_filename, temp_dir)
                db_to_restore = os.path.join(temp_dir, db_filename)

        # Geri yükleme işlemini yap
        import shutil
        shutil.copyfile(db_to_restore, get_db_path())

        # Geçici dosyaları temizle
        if temp_dir:
            shutil.rmtree(temp_dir)

        CustomMessageBox(app.root, "Başarılı", "Veritabanı geri yüklendi. Program yeniden başlatılacak.", 'info')
        logger.log_info(f"Veritabanı geri yüklendi: {file_path}")
        
        app.root.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)

    except Exception as e:
        logger.log_error("Geri yükleme hatası", e)
        CustomMessageBox(app.root, "Hata", f"Geri yükleme sırasında hata: {e}", 'info')
        # Hata durumunda programı yeniden başlat ki eski veritabanı açılsın
        app.root.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)


def show_error_logs(app):
    log_dir = get_log_dir()
    if os.path.exists(log_dir) and os.listdir(log_dir):
        try: os.startfile(log_dir)
        except AttributeError: webbrowser.open(f'file://{os.path.realpath(log_dir)}')
    else: CustomMessageBox(app.root, "Bilgi", "Henüz kaydedilmiş bir hata bulunmuyor.", 'info')

def show_about(app):
    AboutWindow(app.root)