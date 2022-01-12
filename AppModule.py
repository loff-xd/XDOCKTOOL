import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys as system
import datetime

import BackendModule as backend
import PanikModule as panik
import DILModule
import HRModule


class XDTApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.control_panel = ControlPanel(self, text="Commands")
        self.control_panel.grid(column=0, row=0, padx=8, sticky="nsew")

        self.preview_frame = PreviewFrame(self, text="No manifest loaded")
        self.preview_frame.grid(column=0, row=1, sticky="nsew", padx=8, pady=4)

        parent.bind("<F1>", self.control_panel.get_help)
        parent.bind("<F2>", self.control_panel.load_recent)
        parent.bind("<Insert>", self.control_panel.open_mhtml)
        parent.bind("<F3>", self.control_panel.launch_high_risk_manager)
        parent.bind("<F4>", self.control_panel.launch_dil_manager)
        parent.bind("<F5>", self.interface_update)
        parent.bind("<F6>", self.control_panel.toggle_display_mode)
        parent.bind("<F8>", self.control_panel.generate_pdf)
        parent.bind("<F12>", panik.report)

    def interface_update(self, *event):
        backend.selected_manifest = self.control_panel.combo_select_manifest.get()
        self.control_panel.combo_select_manifest["values"] = sorted(backend.manifests)

        backend.user_settings["hr_disp_mode"] = str(self.control_panel.var_display_mode.get())
        backend.user_settings["open_on_save"] = bool(self.control_panel.var_open_on_save.get())
        backend.user_settings = backend.user_settings

        if len(backend.selected_manifest) > 0:
            self.preview_frame.text_preview['state'] = 'normal'
            self.preview_frame.text_preview.delete(1.0, tk.END)
            self.preview_frame.text_preview.insert(tk.INSERT, backend.format_preview(backend.selected_manifest))
            self.preview_frame.text_preview['state'] = 'disabled'

            self.preview_frame.configure(text="Manifest " + backend.selected_manifest + " preview:")

            self.control_panel.button_set_hr["state"] = "normal"
            self.control_panel.button_gen_dil["state"] = "normal"
            self.control_panel.button_export_pdf["state"] = "normal"

        else:
            self.control_panel.button_set_hr["state"] = "disabled"
            self.control_panel.button_gen_dil["state"] = "disabled"
            self.control_panel.button_export_pdf["state"] = "disabled"


# noinspection PyBroadException
class ControlPanel(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.combo_select_manifest = ttk.Combobox(self)
        self.combo_select_manifest.grid(column=0, row=0, padx=10, pady=4)
        self.combo_select_manifest["values"] = sorted(backend.manifests)
        self.combo_select_manifest.bind("<<ComboboxSelected>>", self.parent.interface_update)

        self.button_open = tk.Button(self, text="Import SAP MHTML", command=self.open_mhtml)
        self.button_open.grid(column=1, row=0, padx=4, pady=4)

        self.button_set_hr = tk.Button(self, text="High Risk Manager", command=self.launch_high_risk_manager)
        self.button_set_hr.grid(column=2, row=0, padx=4, pady=4)

        self.button_export_pdf = tk.Button(self, text="Save PDF", command=self.generate_pdf)
        self.button_export_pdf.grid(column=3, row=0, padx=4, pady=4)

        self.button_gen_dil = tk.Button(self, text="Generate DIL",
                                        command=self.launch_dil_manager)
        self.button_gen_dil.grid(column=4, row=0, padx=4, pady=4)

        tk.Label(self, text="Display Mode:").grid(column=10, row=0, padx=4, pady=4)

        self.var_display_mode = tk.StringVar()
        self.display_mode_menu = ttk.Combobox(self, textvariable=self.var_display_mode, state="readonly", width=14)
        self.display_mode_menu.grid(column=11, row=0, padx=4, pady=4)
        self.display_mode_menu.bind("<<ComboboxSelected>>", self.parent.interface_update)
        self.display_mode_menu["values"] = ("Expand None", "Expand HR", "Expand All")

        self.var_open_on_save = tk.IntVar()
        self.check_open_on_save = tk.Checkbutton(self, text="Switch to PDF on save", variable=self.var_open_on_save,
                                                 command=self.parent.interface_update)
        self.check_open_on_save.grid(column=12, row=0, padx=4, pady=10)

        self.button_help = tk.Button(self, text="Help", command=self.get_help)
        self.button_help.grid(column=20, row=0, padx=8, pady=4, sticky="e")
        self.columnconfigure(19, weight=1)

        self.button_set_hr["state"] = "disabled"
        self.button_gen_dil["state"] = "disabled"
        self.button_export_pdf["state"] = "disabled"

        self.hr_manager = None
        self.dil_manager = None

        # Set user settings
        try:
            self.display_mode_menu.set(backend.user_settings["hr_disp_mode"])
        except Exception:
            self.display_mode_menu.set("Expand None")

        if backend.user_settings["open_on_save"]:
            self.check_open_on_save.select()
        else:
            self.check_open_on_save.deselect()

    # noinspection PyBroadException
    def load_recent(self, *args):
        try:
            # Most recent
            recent = backend.manifests[0]
            for manifest in backend.manifests:
                if manifest.import_date > recent.import_date:
                    recent = manifest

            self.combo_select_manifest.set(recent.manifest_id)
            self.parent.interface_update()
            root.title(base_title + "Loaded recent")

        except Exception as e:
            panik.log(e)

    def open_mhtml(self, *args):
        try:
            root.title(base_title + "Open MHTML")
            mhtml_location = filedialog.askopenfilename(filetypes=[("SAP Manifest", ".MHTML")])
            imported_manifest_id = backend.mhtml_importer(mhtml_location)
            self.combo_select_manifest.set(imported_manifest_id)
            main_window.interface_update()
        except Exception as e:
            panik.log(e)

    @staticmethod
    def generate_pdf(*args):
        root.title(base_title + "Generate PDF")
        manifest = backend.get_manifest_from_id(backend.selected_manifest)
        save_location = filedialog.asksaveasfilename(filetypes=[("PDF Document", ".pdf")],
                                                     initialfile=str(manifest.manifest_id + ".pdf"))
        if len(save_location) > 0:
            backend.generate_pdf(manifest, save_location)
            if backend.user_settings["open_on_save"]:
                root.destroy()
                system.exit()

    def launch_high_risk_manager(self, *args):
        if len(backend.selected_manifest) > 0:
            root.title(base_title + "Launch HR Manager")
            self.hr_manager = HRModule.HighRiskManager(self, padx=4, pady=4)

    def launch_dil_manager(self, *args):
        if len(backend.selected_manifest) > 0:
            root.title(base_title + "Launch DIL Manager")
            if len(backend.user_settings["DIL folder"]) < 1:
                tk.messagebox.showinfo("No DIL folder set!",
                                       "Please set a folder for X-Dock Manager to output all DIL reports.")
                backend.user_settings["DIL folder"] = tk.filedialog.askdirectory()
                if not len(backend.user_settings["DIL folder"]) < 1:
                    self.dil_manager = DILModule.DILManager(self)
            else:
                self.dil_manager = DILModule.DILManager(self)

    @staticmethod
    def get_help(*args):
        tk.messagebox.showinfo("Assistance with X-Dock Manager",
                               "Hey there,\n\n"
                               "The full documentation for this software can only be distributed internally. "
                               "It may already be in the application folder "
                               "depending how you received this software.\n\n"
                               "The location of this application is currently:\n"
                               + str(os.getcwd()) + "\n\n"
                                                    "Any issues/bugs/suggestions can be logged via GitHub:\n"
                                                    "https://github.com/loff-xd/XDOCKTOOL\n\n"
                                                    "Cheers for taking the X-Dock Manager for a spin!\n\n"
                                                    "Shortcuts:\n"
                                                    "- Load most recent manifest: F2\n"
                                                    "- Import manifest: INSERT\n"
                                                    "- High Risk Manager: F3\n"
                                                    "- DIL Manager: F4\n"
                                                    "- Toggle Display Mode: F6\n"
                                                    "- Save Manifest: F8\n"
                                                    "- Send error report to dev: F12")

    def toggle_display_mode(self, *args):
        root.title(base_title + "Changed Display Mode")
        try:
            self.display_mode_menu.current(newindex=self.display_mode_menu.current() + 1)
        except:
            self.display_mode_menu.current(newindex=0)
        main_window.interface_update()


class PreviewFrame(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.text_preview = tk.Text(self)
        self.text_preview.grid(column=0, row=0, sticky="nsew", padx=(8, 0), pady=(8, 8))

        # Start Page
        start_page = backend.x_mgr_ascii

        try:
            # Most recent
            if len(backend.manifests) > 0:
                recent = backend.manifests[0]
                for manifest in backend.manifests:
                    if manifest.import_date > recent.import_date:
                        recent = manifest
                start_page += "\n Most recent manifest: " + recent.manifest_id + " (" + recent.import_date + ")\n"

                # DILs raised
                dil_count = 0
                date_today = datetime.date.today()
                date_prior = date_today - datetime.timedelta(days=2)

                for manifest in backend.manifests:
                    if str(date_prior) < manifest.import_date:
                        for sscc in manifest.ssccs:
                            if sscc.dil_status != "":
                                dil_count += 1
                start_page += "\n DILs created (Last 48hrs): " + str(dil_count)
        except Exception as e:
            panik.log(e)

        start_page += "\n\n Shortcuts:\n" \
                      " - Load most recent manifest: F2\n" \
                      " - Import Manifest:           INSERT\n" \
                      " - High Risk Manager:         F3\n" \
                      " - DIL Manager:               F4\n" \
                      " - Toggle Display Mode:       F6\n" \
                      " - Save Manifest:             F8"

        self.text_preview.insert(tk.INSERT, start_page)

        self.text_preview['state'] = 'disabled'

        self.preview_scroll = tk.Scrollbar(self, command=self.text_preview.yview)
        self.preview_scroll.grid(column=1, row=0, sticky="ns", padx=(0, 8), pady=(8, 8))
        self.text_preview['yscrollcommand'] = self.preview_scroll.set


# noinspection PyBroadException
def do_argv_check():
    if len(system.argv) > 1:
        try:
            imported_manifest_id = backend.mhtml_importer(system.argv[1])
            main_window.interface_update()

            main_window.control_panel.combo_select_manifest.set(imported_manifest_id)
            main_window.interface_update()
        except Exception as e:
            panik.log(e)


def exit_app():
    backend.json_save()
    root.destroy()
    system.exit()


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))


def run():
    root.after(150, do_argv_check)
    root.mainloop()


backend.json_load()
root = tk.Tk()
base_title = "X-Dock Manager - " + backend.application_version + " - "
root.title(base_title + "Ready")
root.iconbitmap("XDMGR.ico")
set_centre_geometry(root, 1024, 768)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.wm_protocol("WM_DELETE_WINDOW", lambda: exit_app())
root.minsize(1024, 768)

main_window = XDTApplication(root)
main_window.grid(column=0, row=0, sticky="nsew")
