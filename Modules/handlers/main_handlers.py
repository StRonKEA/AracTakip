# Modules/handlers/main_handlers.py
from Modules.custom_windows import CustomMessageBox
from Modules.logger import logger

def add_record(app):
    """Yeni kayıt ekler."""
    try:
        data = {key: entry.get().strip() for key, entry in app.entries.items()}
        notes = app.notes_entry.get("1.0", "end-1c").strip()
        
        # Placeholder kontrolü
        if data["Plaka"] == app.placeholder_map["Plaka"] or not data["Plaka"]:
            CustomMessageBox(app.root, "Hata", "Plaka alanı zorunludur!", 'info')
            return
        
        # Diğer placeholder'ları temizle
        for key, placeholder in app.placeholder_map.items():
            if data[key] == placeholder:
                data[key] = ""
                
        success = app.db.add_record(data, notes)
        if success:
            app.clear_form()
            app.check_virtualization_and_populate()
            CustomMessageBox(app.root, "Başarılı", "Yeni araç kaydı eklendi.", 'info')
            
    except Exception as e:
        logger.log_error("Kayıt ekleme hatası", e)
        CustomMessageBox(app.root, "Hata", "Kayıt eklenirken bir hata oluştu!", 'info')

def delete_record(app):
    """Seçili kaydı siler."""
    selected_item = app.tree.focus()
    if selected_item:
        record_id = app.tree.item(selected_item)['values'][0]
        plaka = app.tree.item(selected_item)['values'][3]
        
        dialog = CustomMessageBox(app.root, "Silme Onayı", 
            f"'{plaka}' plakalı kaydı silmek istediğinizden emin misiniz?", 'yesno')
        
        if dialog.result:
            app.db.delete_record(record_id)
            app.check_virtualization_and_populate()

def edit_record(app):
    """Seçili kaydı düzenlemek için pencere açar."""
    selected_item = app.tree.focus()
    if not selected_item:
        return
    
    record_id = app.tree.item(selected_item)['values'][0]
    # Editör penceresi UI'da daha karmaşık, şimdilik basit tutalım veya app içinde bir metod olarak kalsın.
    # Bu fonksiyonu şimdilik app'de bırakmak daha kolay olabilir.
    app.open_editor_window(record_id)


def checkout_selected(app):
    """Seçili araca çıkış verir."""
    selected_item = app.tree.focus()
    if selected_item:
        record_id = app.tree.item(selected_item)['values'][0]
        app.db.checkout_vehicle(record_id)
        app.check_virtualization_and_populate()

def reactivate_record(app):
    """Seçili kaydı tekrar aktif hale getirir."""
    selected_item = app.tree.focus()
    if selected_item:
        record_id = app.tree.item(selected_item)['values'][0]
        app.db.reactivate_vehicle(record_id)
        app.check_virtualization_and_populate()

def apply_filters(app):
    """Filtreleri uygular."""
    app.search_var.set("")
    app.check_virtualization_and_populate()

def filter_by_status(app, status):
    """Duruma göre filtreler."""
    app.search_var.set("")
    app.populate_treeview(status_filter=status)

def on_search(app):
    """Arama kutusuna yazıldığında arama yapar."""
    search_term = app.search_var.get().strip()
    if len(search_term) > 1:
        app.populate_treeview(search_term=search_term)
    elif not search_term:
        apply_filters(app)
