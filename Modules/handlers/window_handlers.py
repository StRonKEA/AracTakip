# Modules/handlers/window_handlers.py
from datetime import datetime
from Modules.custom_windows import CustomMessageBox
from Modules.logger import logger
from Modules.ui.reports_tab import update_reports_data_on_ui

def on_tab_change(app, event):
    """Sekme değiştirildiğinde raporlar sekmesini günceller."""
    if app.notebook.index(app.notebook.select()) == 1:
        update_reports_data(app)

def update_reports_data(app):
    """Rapor verilerini alır ve UI'da günceller."""
    try:
        start_date = datetime.strptime(app.start_date_var.get(), "%d.%m.%Y").strftime("%Y-%m-%d")
        end_date = datetime.strptime(app.end_date_var.get(), "%d.%m.%Y").strftime("%Y-%m-%d")
        
        report_data = app.db.get_report_data(start_date, end_date)
        update_reports_data_on_ui(app.report_widgets, report_data) # UI fonksiyonunu çağır
        
    except ValueError:
        CustomMessageBox(app.root, "Hata", "Lütfen tarihleri GG.AA.YYYY formatında girin.", "info")
    except Exception as e:
        logger.log_error("Rapor güncelleme hatası", e)
