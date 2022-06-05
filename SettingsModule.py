import tkinter as tk
from tkinter import ttk

import BackendModule as backend


class SettingsModule(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, **kwargs)

        self.title("Settings")
        set_centre_geometry(self, 300, 150)
        self.grab_set()
        self.focus()
        self.resizable(False, False)
        self.wm_protocol("WM_DELETE_WINDOW", lambda: self.destroy())
        self.iconbitmap("XDMGR.ico")
        self.bind('<Escape>', lambda e: self.destroy())
        self.columnconfigure(0, weight=1)
        self.rowconfigure(8, weight=1)

        self.var_open_on_save = tk.IntVar()
        self.check_open_on_save = tk.Checkbutton(self, text="Switch to PDF on save", variable=self.var_open_on_save,
                                                 command=self.interface_update)
        self.check_open_on_save.grid(column=0, row=0, padx=4, pady=10, columnspan=2)

        tk.Label(self, text="Retention Policy (Days): ").grid(column=0, row=1)
        self.var_retention_policy = tk.StringVar()
        self.retention_policy_menu = ttk.Combobox(self, textvariable=self.var_retention_policy, state="readonly", width=14)
        self.retention_policy_menu.grid(column=1, row=1, padx=(2, 4), pady=4, sticky="w")
        self.retention_policy_menu.bind("<<ComboboxSelected>>", self.interface_update)
        self.retention_policy_menu["values"] = ("Keep All", "30", "60", "120")

        self.close_button = tk.Button(self, text="Close", command=self.close)
        self.close_button.grid(column=0, row=8, pady=(16, 4), sticky="s", columnspan=2)

        # SETTINGS PRESELECTION
        if backend.user_settings["open_on_save"]:
            self.check_open_on_save.select()
        else:
            self.check_open_on_save.deselect()
        self.retention_policy_menu.set(backend.user_settings["retention_policy"])

    def interface_update(self, *args):
        backend.user_settings["open_on_save"] = bool(self.var_open_on_save.get())
        backend.user_settings["retention_policy"] = self.var_retention_policy.get()

    def close(self):
        self.interface_update()
        self.destroy()


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))
