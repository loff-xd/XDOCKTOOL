import tkinter as tk

import AppModule as app
import BackendModule
import BackendModule as backend
from tkinter import messagebox


class ReportModule(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.title("Reports")  # TODO MANI EDITING IN NEXT VERSION
        app.set_centre_geometry(self, 320, 320)
        app.root.grab_release()
        self.grab_set()
        self.focus()
        self.resizable(False, False)

        # self.bind("<F8>", lambda e: pass)
        self.bind('<Escape>', lambda e: self.destroy())

        # self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        # self.columnconfigure(1, weight=1)

        self.target_manifest = backend.get_manifest_from_id(backend.selected_manifest)

        # UI
        self.cb_gen_unscanned_sscc = tk.Checkbutton(self, text="Unscanned SSCCs")
        self.cb_gen_unscanned_sscc.grid(row=1, column=0)

        self.cb_gen_unknown_sscc = tk.Checkbutton(self, text="Unknown SSCCs")
        self.cb_gen_unknown_sscc.grid(row=2, column=0)

        self.btn_scan_lost_ssccs = tk.Button(self, text="Scan for missing SSCCs", command=self.sscc_scan)
        self.btn_scan_lost_ssccs.grid(row=3, column=0)

    @staticmethod
    def sscc_scan(*args):
        result = BackendModule.check_lost_ssccs()
        if len(result) > 0:
            messagebox.showinfo("Found Cartons:", result)
