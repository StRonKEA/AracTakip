# Modules/blacklist.py
import tkinter as tk
from tkinter import ttk
from Modules.custom_windows import CustomMessageBox
from Modules.logger import logger

class BlacklistManager(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        # 📌 DEĞİŞTİ: db → db.db (wrapper'dan ana database'e)
        self.db = db.db if hasattr(db, 'db') else db
        self.title("Kara Liste Yönetimi")
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill="both")
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        form_frame = ttk.LabelFrame(main_frame, text="Yeni Kara Liste Girişi", padding=10)
        form_frame.grid(row=0, column=0, sticky="ew", pady=(0,10))
        form_frame.columnconfigure(1, weight=1)
        
        ttk.Label(form_frame, text="Tip:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.type_var = tk.StringVar(value="Plaka")
        self.type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, 
                                      values=["Plaka", "Sürücü"], state="readonly")
        self.type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.type_combo.bind("<<ComboboxSelected>>", self._update_value_label)
        
        self.value_label = ttk.Label(form_frame, text="Plaka:")
        self.value_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.value_entry = ttk.Entry(form_frame)
        self.value_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(form_frame, text="Sebep:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.reason_entry = ttk.Entry(form_frame)
        self.reason_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Ekle", command=self._add_to_blacklist, style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="Seçili Kaydı Sil", command=self._remove_from_blacklist).pack(side="left", padx=5)
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        
        self.tree = ttk.Treeview(tree_frame, columns=("tip", "deger", "sebep", "tarih"), show="headings")
        self.tree.heading("tip", text="Tip")
        self.tree.heading("deger", text="Değer (Plaka/Sürücü)")
        self.tree.heading("sebep", text="Sebep")
        self.tree.heading("tarih", text="Eklenme Tarihi")
        self.tree.column("tip", width=80, stretch=tk.NO)
        self.tree.pack(side="left", expand=True, fill="both")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.geometry("800x600")
        self.center_window(parent)
        self._populate_blacklist()
        logger.log_info("Kara liste yöneticisi açıldı")

    def _update_value_label(self, event=None):
        self.value_label.config(text=f"{self.type_var.get()}:")

    def _populate_blacklist(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        # 📌 DEĞİŞTİ: self.db → self.db (artık doğrudan ana database)
        for record in self.db.get_blacklist():
            self.tree.insert("", "end", values=record)

    def _add_to_blacklist(self):
        item_type = self.type_var.get()
        item_value = self.value_entry.get().strip()
        reason = self.reason_entry.get().strip()
        
        if not item_value:
            CustomMessageBox(self, "Hata", "Değer alanı boş bırakılamaz.", "info")
            return
        
        db_type = "PLAKA" if item_type == "Plaka" else "SURUCU"
        
        # 📌 DEĞİŞTİ: self.db → self.db (artık doğrudan ana database)
        if self.db.add_to_blacklist(item_value, db_type, reason):
            CustomMessageBox(self, "Başarılı", f"'{item_value}' kara listeye eklendi.", "info")
            self.value_entry.delete(0, "end")
            self.reason_entry.delete(0, "end")
            self._populate_blacklist()
        else:
            CustomMessageBox(self, "Hata", f"'{item_value}' zaten kara listede.", "info")

    def _remove_from_blacklist(self):
        selected_item = self.tree.focus()
        if not selected_item:
            CustomMessageBox(self, "Uyarı", "Lütfen silinecek bir kayıt seçin.", "info")
            return
        
        item_type_tr, item_value = self.tree.item(selected_item)['values'][:2]
        db_type = "PLAKA" if item_type_tr == "Plaka" else "SURUCU"
        
        dialog = CustomMessageBox(self, "Onay", f"'{item_value}' değerini kara listeden kaldırmak istediğinizden emin misiniz?", "yesno")
        if dialog.result:
            # 📌 DEĞİŞTİ: self.db → self.db (artık doğrudan ana database)
            self.db.remove_from_blacklist(item_value, db_type)
            self._populate_blacklist()

    def center_window(self, parent):
        self.update_idletasks()
        parent_geo = parent.geometry().split('+')
        parent_x, parent_y = int(parent_geo[1]), int(parent_geo[2])
        parent_w, parent_h = [int(i) for i in parent_geo[0].split('x')]
        w, h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')