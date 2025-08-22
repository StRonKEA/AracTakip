# Modules/custom_windows.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from Modules.helpers import get_app_path
from Modules.logger import logger

class CustomMessageBox(tk.Toplevel):
    def __init__(self, parent, title, message, dialog_type='info'):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.result = None
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")
        
        ttk.Label(main_frame, text=message, wraplength=400, justify="center").pack(pady=(0, 20))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        if dialog_type == 'yesno':
            yes_button = ttk.Button(button_frame, text="Evet", command=self._on_yes, style="Accent.TButton")
            yes_button.pack(side="left", padx=5)
            ttk.Button(button_frame, text="Hayır", command=self._on_no).pack(side="left", padx=5)
            yes_button.focus_set()
            self.bind("<Return>", lambda e: self._on_yes())
            self.bind("<Escape>", lambda e: self._on_no())
        else:
            ok_button = ttk.Button(button_frame, text="Tamam", command=self._on_ok, style="Accent.TButton")
            ok_button.pack()
            ok_button.focus_set()
            self.bind("<Return>", lambda e: self._on_ok())
            self.bind("<Escape>", lambda e: self._on_ok())
        
        self.center_window(parent)
        self.wait_window(self)
        logger.log_info(f"Dialog gösterildi: {title} - {message}")

    def _on_yes(self): 
        self.result = True
        self.destroy()

    def _on_no(self): 
        self.result = False
        self.destroy()

    def _on_ok(self): 
        self.destroy()

    def center_window(self, parent):
        self.update_idletasks()
        parent_geo = parent.geometry().split('+')
        parent_x, parent_y = int(parent_geo[1]), int(parent_geo[2])
        parent_w, parent_h = [int(i) for i in parent_geo[0].split('x')]
        w, h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

class FlashingMessageBox(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.configure(background='red')
        
        main_frame = ttk.Frame(self, padding="20", style="Card.TFrame")
        main_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        ttk.Label(main_frame, text=message, wraplength=400, justify="center", 
                 font=("Helvetica", 12, "bold"), foreground="red").pack(pady=(0, 20))
        
        ok_button = ttk.Button(main_frame, text="ANLAŞILDI", command=self.destroy, style="Accent.TButton")
        ok_button.pack()
        ok_button.focus_set()
        
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.flash_count = 0
        self.flash()
        self.center_window(parent)
        logger.log_info(f"Flashing dialog gösterildi: {title}")

    def flash(self):
        if self.flash_count < 10:
            current_color = self.cget("background")
            next_color = "white" if current_color == "red" else "red"
            self.configure(background=next_color)
            self.bell()
            self.flash_count += 1
            self.after(200, self.flash)

    def center_window(self, parent):
        self.update_idletasks()
        parent_geo = parent.geometry().split('+')
        parent_x, parent_y = int(parent_geo[1]), int(parent_geo[2])
        parent_w, parent_h = [int(i) for i in parent_geo[0].split('x')]
        w, h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

class AboutWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Program Hakkında")
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")
        
        ttk.Label(main_frame, text="Araç Takip Programı v1.3", font=("Helvetica", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(main_frame, text="Bu program sizin için geliştirildi.").pack(pady=5)
        ttk.Label(main_frame, text="Tüm hakları saklıdır.").pack(pady=5)
        ttk.Label(main_frame, text="🐈", font=("Segoe UI Emoji", 48)).pack(pady=(10, 10))
        
        ok_button = ttk.Button(main_frame, text="Kapat", command=self.destroy, style="Accent.TButton")
        ok_button.pack(pady=(10, 0))
        ok_button.focus_set()
        
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.center_window(parent)
        self.wait_window(self)
        logger.log_info("Hakkında penceresi gösterildi")

    def center_window(self, parent):
        self.update_idletasks()
        parent_geo = parent.geometry().split('+')
        parent_x, parent_y = int(parent_geo[1]), int(parent_geo[2])
        parent_w, parent_h = [int(i) for i in parent_geo[0].split('x')]
        w, h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

class BackupNotificationWindow(tk.Toplevel):
    def __init__(self, parent, title="Yedekleme", message="İşlem yapılıyor, lütfen bekleyin..."):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")
        
        self.label = ttk.Label(main_frame, text=message, font=("Segoe UI", 10), justify="center")
        self.label.pack(pady=(0, 15))
        
        self.ok_button = ttk.Button(main_frame, text="Tamam", state="disabled", command=self.destroy, style="Accent.TButton")
        self.ok_button.pack()
        
        self.center_window(parent)
        logger.log_info(f"Yedekleme bildirimi: {title}")

    def on_complete(self, message):
        self.label.config(text=message)
        self.ok_button.config(state="normal")
        self.ok_button.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        logger.log_info(f"Yedekleme tamamlandı: {message}")

    def center_window(self, parent):
        self.update_idletasks()
        w, h = 450, 150
        parent_geo = parent.geometry().split('+')
        parent_x, parent_y = int(parent_geo[1]), int(parent_geo[2])
        parent_w, parent_h = [int(i) for i in parent_geo[0].split('x')]
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')