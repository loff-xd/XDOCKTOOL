import cProfile
import datetime
import os
import sys as system
import threading
import tkinter as tk
from time import sleep
from tkinter import ttk, filedialog, messagebox

import BackendModule as backend
import DILModule
import HRModule
import NetcomModule
import PanikModule as panik
import SearchModule

APP_DIR = os.getcwd()
profiling = False

if not os.path.isfile(os.path.join(APP_DIR, "bin\\XDOCK_MANAGER\\search.png")):
    SEARCHICON = os.path.join(APP_DIR, "search.png")
else:
    SEARCHICON = os.path.join(APP_DIR, "bin\\XDOCK_MANAGER\\search.png")


class XDTApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        # tk.Frame.__init__(self, parent, *args, **kwargs)
        super().__init__(parent, **kwargs)
        self.parent = parent

        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)

        self.control_panel = ControlPanel(self, text="Commands")
        self.control_panel.grid(column=2, row=0, padx=8, sticky="nsew")

        self.preview_frame = PreviewFrame(self, text="No manifest loaded")
        self.preview_frame.grid(column=2, row=1, sticky="nsew", padx=8, pady=4)

        self.manifest_frame = tk.LabelFrame(self, text="Manifests:")
        self.manifest_frame.grid(row=0, column=0, sticky="nsew", rowspan=2, padx=4, pady=4)
        self.manifest_frame.rowconfigure(0, weight=1)

        self.combo_content = tk.StringVar()
        self.combo_content.set(sorted(backend.manifests))
        self.combo_select_manifest = tk.Listbox(self.manifest_frame, selectmode="single",
                                                listvariable=self.combo_content, exportselection=False)
        self.combo_select_manifest.grid(column=0, row=0, padx=(10, 4), pady=4, sticky="ns")
        self.combo_select_manifest.bind("<<ListboxSelect>>", self.interface_update)

        self.listbox_scroll = tk.Scrollbar(self.manifest_frame, command=self.combo_select_manifest.yview)
        self.listbox_scroll.grid(column=1, row=0, pady=4, sticky="ns")
        self.combo_select_manifest['yscrollcommand'] = self.listbox_scroll.set

        self.status_label = tk.Label(self, text="Reading application data...")
        self.status_label.grid(column=0, row=3, columnspan=3, sticky="w", padx=8)

        root.bind("<F1>", self.control_panel.get_help)
        root.bind("<F2>", self.control_panel.load_recent)
        root.bind("<Insert>", self.control_panel.open_mhtml)
        root.bind("<F3>", self.control_panel.launch_high_risk_manager)
        root.bind("<F4>", self.control_panel.launch_dil_manager)
        root.bind("<F5>", self.interface_update)
        root.bind("<F6>", self.control_panel.toggle_display_mode)
        root.bind("<F8>", self.control_panel.generate_pdf)
        root.bind("<F12>", panik.report)

    def select_manifest_in_listbox(self, manifest_id):
        self.combo_select_manifest.selection_clear(0, tk.END)
        for i in range(0, self.combo_select_manifest.size()):
            if self.combo_select_manifest.get(i) == manifest_id:
                self.combo_select_manifest.select_set(i)
                self.combo_select_manifest.activate(i)
                break

    def interface_update(self, *event):
        if len(self.combo_select_manifest.curselection()) > 0:
            backend.selected_manifest = self.combo_select_manifest.get(self.combo_select_manifest.curselection())
        self.combo_content.set(sorted(backend.manifests))

        backend.user_settings["hr_disp_mode"] = str(self.control_panel.var_display_mode.get())
        backend.user_settings["open_on_save"] = bool(self.control_panel.var_open_on_save.get())
        backend.user_settings = backend.user_settings

        main_window.set_status("Ready.", False)

        if len(backend.selected_manifest) > 0 and len(
                [x for x in backend.manifests if x.manifest_id == backend.selected_manifest]) > 0:
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
            self.preview_frame.start_page()
            self.preview_frame['text'] = "No manifest loaded"

    def set_status(self, text, progress):
        if progress:
            self.status_label["text"] = text
        else:
            self.status_label["text"] = text


# noinspection PyBroadException
class ControlPanel(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        # tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        super().__init__(parent, **kwargs)
        self.parent = parent

        self.button_search_image = tk.PhotoImage(file=SEARCHICON)
        self.button_search = tk.Button(self, image=self.button_search_image, command=self.launch_search_module,
                                       height=20, width=20)
        self.button_search.grid(column=1, row=0, padx=(8, 4), pady=4)

        self.button_open = tk.Button(self, text="Import SAP MHTML", command=self.open_mhtml)
        self.button_open.grid(column=2, row=0, padx=(4, 2), pady=4)

        self.button_set_hr = tk.Button(self, text="High Risk Manager", command=self.launch_high_risk_manager)
        self.button_set_hr.grid(column=3, row=0, padx=2, pady=4)

        self.button_export_pdf = tk.Button(self, text="Save PDF", command=self.generate_pdf)
        self.button_export_pdf.grid(column=4, row=0, padx=2, pady=4)

        self.button_gen_dil = tk.Button(self, text="Generate DIL",
                                        command=self.launch_dil_manager)
        self.button_gen_dil.grid(column=5, row=0, padx=(2, 4), pady=4)

        tk.Label(self, text="Display Mode:").grid(column=10, row=0, padx=(4, 0), pady=4)

        self.var_display_mode = tk.StringVar()
        self.display_mode_menu = ttk.Combobox(self, textvariable=self.var_display_mode, state="readonly", width=14)
        self.display_mode_menu.grid(column=11, row=0, padx=(2, 4), pady=4)
        self.display_mode_menu.bind("<<ComboboxSelected>>", self.parent.interface_update)
        self.display_mode_menu["values"] = ("Expand None", "Expand HR", "Expand All")

        self.var_open_on_save = tk.IntVar()
        self.check_open_on_save = tk.Checkbutton(self, text="Switch to PDF on save", variable=self.var_open_on_save,
                                                 command=self.parent.interface_update)
        self.check_open_on_save.grid(column=12, row=0, padx=4, pady=10)

        self.button_reports = tk.Button(self, text="Mobile Sync", command=self.open_sync)
        self.button_reports.grid(column=20, row=0, padx=8, pady=4, sticky="e")
        self.columnconfigure(19, weight=1)

        self.button_set_hr["state"] = "disabled"
        self.button_gen_dil["state"] = "disabled"
        self.button_export_pdf["state"] = "disabled"

        self.hr_manager = None
        self.dil_manager = None
        self.search_module = None
        self.reportModule = None

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
        if len(backend.manifests) > 0:
            try:
                # Most recent
                recent = backend.manifests[0]
                for manifest in backend.manifests:
                    if int(manifest.manifest_id) > int(recent.manifest_id):
                        recent = manifest

                self.parent.combo_content.set(sorted(backend.manifests))
                self.parent.select_manifest_in_listbox(recent.manifest_id)
                self.parent.interface_update()

            except Exception as e:
                panik.log(e)

    def open_mhtml(self, *args):
        try:
            main_window.set_status("Open MHTML...", False)
            mhtml_location = filedialog.askopenfilename(filetypes=[("SAP Manifest", ".MHTML")])
            if len(mhtml_location) > 0:
                imported_manifest_id = backend.mhtml_importer(mhtml_location)
                self.parent.combo_content.set(sorted(backend.manifests))
                self.parent.select_manifest_in_listbox(imported_manifest_id)
            main_window.interface_update()
        except Exception as e:
            panik.log(e)

    @staticmethod
    def generate_pdf(*args):
        if backend.selected_manifest != "":
            main_window.set_status("Generate PDF...", False)
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
            main_window.set_status("Open HR Manager...", False)
            self.hr_manager = HRModule.HighRiskManager(self, padx=4, pady=4)

    def launch_dil_manager(self, *args):
        if len(backend.selected_manifest) > 0:
            main_window.set_status("Open DIL Manager...", False)
            if len(backend.user_settings["DIL folder"]) < 1:
                tk.messagebox.showinfo("No DIL folder set!",
                                       "Please set a folder for X-Dock Manager to output all DIL reports.")
                backend.user_settings["DIL folder"] = tk.filedialog.askdirectory()
                if len(backend.user_settings["DIL folder"]) > 0:
                    self.dil_manager = DILModule.DILManager(self)
            else:
                self.dil_manager = DILModule.DILManager(self)

    def launch_search_module(self, *args):
        self.search_module = SearchModule.SearchWindow(self)

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
        try:
            self.display_mode_menu.current(newindex=self.display_mode_menu.current() + 1)
        except:
            self.display_mode_menu.current(newindex=0)
        main_window.interface_update()

    def open_sync(self, *args):
        main_window.set_status("Open Mobile Sync...", False)
        self.reportModule = NetcomModule.NetcomModule(self)


class PreviewFrame(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        # tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        super().__init__(parent, **kwargs)
        self.parent = parent

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.text_preview = tk.Text(self)
        self.text_preview.grid(column=0, row=0, sticky="nsew", padx=(8, 0), pady=(8, 8))

        self.preview_scroll = tk.Scrollbar(self, command=self.text_preview.yview)
        self.preview_scroll.grid(column=1, row=0, sticky="ns", padx=(0, 8), pady=(8, 8))
        self.text_preview['yscrollcommand'] = self.preview_scroll.set

        self.start_page()

    def start_page(self):
        start_page = backend.x_mgr_ascii
        self.text_preview['state'] = 'normal'
        self.text_preview.delete('1.0', tk.END)

        try:
            # Most recent
            if len(backend.manifests) > 0:
                recent = backend.manifests[0]
                for manifest in backend.manifests:
                    if int(manifest.manifest_id) > int(recent.manifest_id):
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


# noinspection PyBroadException
def do_argv_check():
    if len(system.argv) > 1:
        try:
            imported_manifest_id = backend.mhtml_importer(system.argv[1])
            main_window.interface_update()

            main_window.select_manifest_in_listbox(imported_manifest_id)
            main_window.interface_update()
        except Exception as e:
            panik.log(e)


def exit_app():
    root.destroy()
    backend.json_save()
    if profiler is not None:
        profiler.disable()
        profiler.print_stats(sort="cumtime")
    system.exit()


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))


def io_lock_callback():
    while backend.io_lock:
        sleep(0.25)
    main_window.interface_update()
    main_window.set_status("Ready.", False)


def run():
    global root, main_window
    backend.io_lock = True
    threading.Thread(target=backend.json_load).start()
    root = tk.Tk()
    root.title("X-Dock Manager")

    set_centre_geometry(root, 1200, 660)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.wm_protocol("WM_DELETE_WINDOW", lambda: exit_app())
    root.minsize(1200, 660)

    main_window = XDTApplication(root)
    main_window.grid(column=0, row=0, sticky="nsew")
    threading.Thread(target=io_lock_callback).start()

    root.iconbitmap("XDMGR.ico")
    root.after(150, do_argv_check)
    root.mainloop()


global root, main_window
profiler = None
if profiling:
    profiler = cProfile.Profile()
    profiler.enable()
    run()
else:
    run()
