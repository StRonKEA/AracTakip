# Modules/ui/menu.py
import tkinter as tk
from Modules.logger import logger

def create_main_menu(root, commands):
    """Ana menü çubuğu oluşturur."""
    try:
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)
        
        # Dosya menüsü
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Ayarlar...", command=commands['settings'])
        file_menu.add_separator()
        file_menu.add_command(label="Excel'e Aktar", command=commands['export_excel'])
        file_menu.add_command(label="Özel Rapor Oluştur...", command=commands['custom_report'])
        file_menu.add_separator()
        file_menu.add_command(label="Kara Liste Yönetimi", command=commands['blacklist'])
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=commands['exit'])
        
        # Yedek menüsü
        backup_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Yedek", menu=backup_menu)
        backup_menu.add_command(label="Şimdi Yedek Al", command=commands['backup_now'])
        backup_menu.add_command(label="Yedekten Geri Yükle", command=commands['restore_backup'])
        
        # Hakkında menüsü
        about_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Hakkında", menu=about_menu)
        about_menu.add_command(label="Hata Kayıtlarını Göster", command=commands['show_errors'])
        about_menu.add_command(label="Program Hakkında", command=commands['about'])
        
        logger.log_info("Ana menü oluşturuldu")
        return menu_bar
        
    except Exception as e:
        logger.log_error("Ana menü oluşturma hatası", e)
        raise
