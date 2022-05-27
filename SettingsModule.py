import tkinter as tk
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

        self.sync_button = tk.Button(self, text="Close", command=self.close)
        self.sync_button.grid(column=0, row=2, pady=16, sticky='e')

    def close(self):
        pass


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))
