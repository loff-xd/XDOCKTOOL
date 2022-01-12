"""XDTFRONTEND.py: The pants-wearing part of XDOCKTOOL which tells backend what to do"""

__author__ = "Lachlan Angus"
__copyright__ = "Copyright 2021, Lachlan Angus"

import os
import tkinter as tk
import tkinter.messagebox
from tkinter import ttk, filedialog
import sys as system
import datetime

import XDTBACKEND
import XDTBACKEND as backend

# Application setup
import panik

selected_manifest = ""
backend.json_load()
user_settings = backend.user_settings

application_version = "1.1.1.3"

x_mgr_ascii = "@@(//@@@@@@@@@@@@@@@@@@(/////////////////(@@@@@@@@@@@@@@@@@&///@@@@@@(///%@@@@@%/////(@@@@@@@@@(////#@@@@@@@@@@@&/////#@\n\
@@@@///@@@@@@@@@@@@@@@@@#///////////////&@@@@@@@@@@@@@@@@@#////@@@@@@@///@@@@@@%///#@@@@@&&&@@@@@(//#@@@@&&&&@@@@@////#@\n\
@@@@@#//&@@@@@@@@@@@@@@@@@////////////(@@@@@@@@@@@@@@@@@%//////@@@@%@@%/@@@(@@@%//%@@@@(////////////#@@@@@@@@@@@@%////#@\n\
@@@@@@@(//@@@@@@@@@@@@@@@@@&/////////%@@@@@@@@@@@@@@@@@////////@@@@/@@@(@@@/@@@%//%@@@@(//&@@@@@@%//#@@@@@@@@@@#//////#@\n\
@@@@@@@@&//%@@@@@@@@@@@@@@@@@///////@@@@@@@@@@@@@@@@@(/////////@@@@//@@@@%//@@@%///@@@@@&///@@@@@%//#@@@@#//@@@@@/////#@\n\
@@@@@@@@@@#//&@@@@@@@@@@@@@@@@@///%@@@@@@@@@@@@@@@@@///////////@@@@///@@@///@@@%/////@@@@@@@@@@@////#@@@@#///@@@@@#///#@\n\
@@@@@@@@@@@@//#@@@@@@@@@@@@@@@@@(@@@@@@@@@@@@@@@@@///////////////////////////////////////////////////////////////////(@@\n\
@@@@@@@@@@@@@%//%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&//////////////////////////////////////////////////////////////////%@@@@\n\
@@@@@@@@@@@@@@@%/(@@@@@@@@@@@@@@@@@@@@@@@@@@@@@/////////////////////////////////////////////////////////////////(@@@@@@@\n\
@@@@@@@@@@@@@@@@@//(@@@@@@@@@@@@@@@@@@@@@@@@@%////////////////////////////////////////////////////////////////&@@@@@@@@@\n\
@@@@@@@@@@@@@@@@@@///@@@@@@@@@@@@@@@@@@@@@@@////////////////////////////////////////////////////////////////@@@@@@@@@@@@\n\
@@@@@@@@@@@@@@@@@&//@@@@@@@@@@@@@@@@@@@@@@@@&////////////////////////////////////////////////////////////&@@@@@@@@@@@@@@\n\
@@@@@@@@@@@@@@@@//(@@@@@@@@@@@@@@@@@@@@@@@@@@@////////////////////////////////////////////////////////(@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@@@@@@%/(@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@////////////////////////////////////////////////////%@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@@@@%//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%///////////////////////////////////////////////(@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@@@//#@@@@@@@@@@@@@@@@@&(@@@@@@@@@@@@@@@@@@(///////////////////////////////////////////&@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@#/(@@@@@@@@@@@@@@@@@@(///&@@@@@@@@@@@@@@@@@@///////////////////////////////////////(@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@#//&@@@@@@@@@@@@@@@@@%//////(@@@@@@@@@@@@@@@@@@(///////////////////////////////////&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@//#@@@@@@@@@@@@@@@@@&//////////%@@@@@@@@@@@@@@@@@@////////////////////////////////@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@#//&@@@@@@@@@@@@@@@@@#////////////(@@@@@@@@@@@@@@@@@@#///////////////////////////%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@//%@@@@@@@@@@@@@@@@@#////////////////%@@@@@@@@@@@@@@@@@@#//////////////////////(@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@(//@@@@@@@@@@@@@@@@@@///////////////////(@@@@@@@@@@@@@@@@@@@///////////////////&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"


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
        global selected_manifest
        selected_manifest = self.control_panel.combo_select_manifest.get()
        self.control_panel.combo_select_manifest["values"] = sorted(backend.manifests)

        user_settings["hr_disp_mode"] = str(self.control_panel.var_display_mode.get())
        user_settings["open_on_save"] = bool(self.control_panel.var_open_on_save.get())
        backend.user_settings = user_settings

        if len(selected_manifest) > 0:
            self.preview_frame.text_preview['state'] = 'normal'
            self.preview_frame.text_preview.delete(1.0, tk.END)
            self.preview_frame.text_preview.insert(tk.INSERT, backend.format_preview(selected_manifest))
            self.preview_frame.text_preview['state'] = 'disabled'

            self.preview_frame.configure(text="Manifest " + selected_manifest + " preview:")

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

        # Set user settings
        try:
            self.display_mode_menu.set(user_settings["hr_disp_mode"])
        except Exception:
            self.display_mode_menu.set("Expand None")

        if user_settings["open_on_save"]:
            self.check_open_on_save.select()
        else:
            self.check_open_on_save.deselect()

    # noinspection PyBroadException
    def load_recent(self, *args):
        try:
            # Most recent
            recent = XDTBACKEND.manifests[0]
            for manifest in XDTBACKEND.manifests:
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
        manifest = backend.get_manifest_from_id(selected_manifest)
        save_location = filedialog.asksaveasfilename(filetypes=[("PDF Document", ".pdf")],
                                                     initialfile=str(manifest.manifest_id + ".pdf"))
        if len(save_location) > 0:
            backend.generate_pdf(manifest, save_location)
            if user_settings["open_on_save"]:
                root.destroy()
                system.exit()

    def launch_high_risk_manager(self, *args):
        if len(selected_manifest) > 0:
            root.title(base_title + "Launch HR Manager")
            self.hr_manager = HighRiskManager(self, padx=4, pady=4)

    def launch_dil_manager(self, *args):
        if len(selected_manifest) > 0:
            root.title(base_title + "Launch DIL Manager")
            if len(backend.user_settings["DIL folder"]) < 1:
                tkinter.messagebox.showinfo("No DIL folder set!",
                                            "Please set a folder for X-Dock Manager to output all DIL reports.")
                backend.user_settings["DIL folder"] = tkinter.filedialog.askdirectory()
                if not len(backend.user_settings["DIL folder"]) < 1:
                    self.dil_manager = DILManager(self)
            else:
                self.dil_manager = DILManager(self)

    @staticmethod
    def get_help(*args):
        tkinter.messagebox.showinfo("Assistance with X-Dock Manager",
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
        start_page = x_mgr_ascii

        try:
            # Most recent
            recent = XDTBACKEND.manifests[0]
            for manifest in XDTBACKEND.manifests:
                if manifest.import_date > recent.import_date:
                    recent = manifest
            start_page += "\n Most recent manifest: " + recent.manifest_id + " (" + recent.import_date + ")\n"

            # DILs raised
            dil_count = 0
            date_today = datetime.date.today()
            date_prior = date_today - datetime.timedelta(days=2)

            for manifest in XDTBACKEND.manifests:
                if str(date_prior) < manifest.import_date:
                    for sscc in manifest.ssccs:
                        if sscc.dil_status != "":
                            dil_count += 1
            start_page += "\n DILs created (Last 48hrs): " + str(dil_count)
        except Exception as e:
            pass

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


class HighRiskManager(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.title("High Risk Manager")
        set_centre_geometry(self, 640, 480)
        root.grab_release()
        self.grab_set()
        self.focus()
        self.resizable(False, False)

        self.bind("<F8>", self.close_hr_manager)
        self.bind('<Escape>', lambda e: self.destroy())

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.manifest = backend.get_manifest_from_id(selected_manifest)

        self.tab_selector = ttk.Notebook(self)
        self.tab_selector.grid(column=0, row=0)

        self.sscc_tab = self.SSCCTab(self.tab_selector, self.manifest)
        self.article_tab = self.ArticleTab(self.tab_selector)
        self.suggestions_tab = self.SuggestionsTab(self.tab_selector)
        self.sscc_tab.pack(fill='both', expand=True)
        self.article_tab.pack(fill='both', expand=True)
        self.suggestions_tab.pack(fill='both', expand=True)

        self.tab_selector.add(self.sscc_tab, text="By This SSCC")
        self.tab_selector.add(self.article_tab, text="By All Articles")
        self.tab_selector.add(self.suggestions_tab, text="Suggestions")

        dialog_reset = tk.Button(self, text="Reset Articles", command=self.reset_hr_manager)
        dialog_reset.grid(column=0, row=1, sticky="sw", padx=35)

        dialog_close_button = tk.Button(self, text="Finished (F8)", command=self.close_hr_manager)
        dialog_close_button.grid(column=0, row=1, sticky="se", padx=35)

    def close_hr_manager(self, *args):
        # Get selection from HR SSCCs
        sscc_listbox_content = []
        for index in self.sscc_tab.hr_sscc_list:
            sscc_listbox_content.append(str(index).replace(" ", ""))

        # Get selection from HR articles
        article_listbox_content = []
        for index in self.article_tab.hr_article_list:
            article_listbox_content.append(str(index))
        user_settings["hr_articles"] = article_listbox_content

        # Reset HR tags
        for sscc in self.manifest.ssccs:
            sscc.is_HR = False
            for article in sscc.articles:
                article.is_HR = False

        # Set new HR tags
        for selection in article_listbox_content:
            for manifest in backend.manifests:
                for sscc in manifest.ssccs:
                    for article in sscc.articles:
                        if article.code == selection:
                            article.is_HR = True

        for selection in sscc_listbox_content:
            for sscc in self.manifest.ssccs:
                if sscc.sscc == selection:
                    sscc.is_HR = True

        backend.manifests.remove(backend.get_manifest_from_id(selected_manifest))
        backend.manifests.append(self.manifest)
        backend.json_save()
        main_window.interface_update()
        self.grab_release()
        root.grab_set()
        self.destroy()

    def reset_hr_manager(self):
        if tkinter.messagebox.askyesno("Hol up!",
                                       "This will clear all user-set articles to be automatically marked as high risk! "
                                       "Are you sure you want to do this?", parent=self):
            user_settings["hr_articles"] = []
            self.article_tab.reset()

    class SSCCTab(tk.Frame):
        def __init__(self, parent, manifest, *args, **kwargs):
            tk.Frame.__init__(self, parent, *args, **kwargs)

            # List side
            self.sscc_list = []
            for sscc in manifest.ssccs:
                if not sscc.is_HR:
                    self.sscc_list.append(sscc.sscc[:-4] + " " + last_four(sscc.sscc))

            self.listbox_content = tk.StringVar()
            self.sscc_list = sorted(self.sscc_list, key=last_four)
            self.sscc_listbox = tk.Listbox(self, height=24, width=35, listvariable=self.listbox_content,
                                           selectmode="multiple")
            self.sscc_listbox.grid(column=0, row=1)
            self.sscc_listbox.configure(justify=tk.RIGHT)
            self.listbox_content.set(self.sscc_list)

            self.listbox_scroll = tk.Scrollbar(self, command=self.sscc_listbox.yview)
            self.listbox_scroll.grid(column=1, row=1, sticky="ns")
            self.sscc_listbox['yscrollcommand'] = self.listbox_scroll.set
            tk.Label(self, text="Ignore:").grid(column=0, row=0, sticky="w")

            # HR side
            self.hr_sscc_list = []
            for sscc in manifest.ssccs:
                if sscc.is_HR:
                    self.hr_sscc_list.append(sscc.sscc[:-4] + " " + last_four(sscc.sscc))

            self.hr_listbox_content = tk.StringVar()
            self.hr_sscc_list = sorted(self.hr_sscc_list, key=last_four)
            self.hr_listbox = tk.Listbox(self, height=24, width=35, listvariable=self.hr_listbox_content,
                                         selectmode="multiple")
            self.hr_listbox.grid(column=3, row=1)
            self.hr_listbox.configure(justify=tk.RIGHT)
            self.hr_listbox_content.set(self.hr_sscc_list)

            self.listbox_scroll = tk.Scrollbar(self, command=self.hr_listbox.yview)
            self.listbox_scroll.grid(column=4, row=1, sticky="ns")
            self.hr_listbox['yscrollcommand'] = self.listbox_scroll.set
            tk.Label(self, text="High Risk:").grid(column=3, row=0, sticky="w")

            # Swap buttons
            self.button_add_hr = tk.Button(self, text=" >> ", command=self.swap_to_hr)
            self.button_add_hr.grid(column=2, row=1, sticky="n", padx=10, pady=45)

            self.button_rem_hr = tk.Button(self, text=" << ", command=self.swap_from_hr)
            self.button_rem_hr.grid(column=2, row=1, sticky="s", padx=10, pady=45)

        def swap_to_hr(self):
            for index in self.sscc_listbox.curselection():
                self.hr_sscc_list.append(self.sscc_listbox.get(index))
                self.sscc_list.remove(self.sscc_listbox.get(index))
            self.hr_listbox_content.set(sorted(self.hr_sscc_list, key=last_four))
            self.listbox_content.set(sorted(self.sscc_list, key=last_four))
            self.hr_listbox.selection_clear(0, "end")
            self.sscc_listbox.selection_clear(0, "end")

        def swap_from_hr(self):
            for index in self.hr_listbox.curselection():
                self.sscc_list.append(self.hr_listbox.get(index))
                self.hr_sscc_list.remove(self.hr_listbox.get(index))
            self.hr_listbox_content.set(sorted(self.hr_sscc_list, key=last_four))
            self.listbox_content.set(sorted(self.sscc_list, key=last_four))
            self.hr_listbox.selection_clear(0, "end")
            self.sscc_listbox.selection_clear(0, "end")

    class ArticleTab(tk.Frame):
        def __init__(self, parent, *args, **kwargs):
            tk.Frame.__init__(self, parent, *args, **kwargs)

            # List side
            self.article_list = []
            for mani in backend.manifests:
                for sscc in mani.ssccs:
                    for article in sscc.articles:
                        if not article.is_HR and article.code not in user_settings["hr_articles"]:
                            self.article_list.append(article.code)
            self.article_list = list(dict.fromkeys(self.article_list))  # REMOVE DUPLICATES

            self.article_listbox_content = tk.StringVar()
            self.article_list = sorted(self.article_list)
            self.article_listbox = tk.Listbox(self, height=22, width=35, listvariable=self.article_listbox_content,
                                              selectmode="multiple")
            self.article_listbox.grid(column=0, row=1, sticky="n")
            self.article_listbox.configure(justify=tk.LEFT)
            self.article_listbox_content.set(self.article_list)

            self.listbox_scroll = tk.Scrollbar(self, command=self.article_listbox.yview)
            self.listbox_scroll.grid(column=1, row=1, sticky="ns")
            self.article_listbox['yscrollcommand'] = self.listbox_scroll.set
            tk.Label(self, text="Ignore:").grid(column=0, row=0, sticky="w")

            self.article_search_text = tk.StringVar()
            self.article_search_text.trace_add("write", self.search)
            self.article_search_box = tk.Entry(self, justify=tk.LEFT, textvariable=self.article_search_text)
            self.article_search_box.grid(column=0, row=1, sticky="se", pady=4, padx=10)
            self.article_search_box.bind("<Return>", self.search)
            tk.Label(self, text="Filter:").grid(column=0, row=1, sticky="sw", pady=4, padx=10)

            # HR side
            self.hr_article_list = user_settings["hr_articles"]
            self.hr_article_list = list(dict.fromkeys(self.hr_article_list))  # REMOVE DUPLICATES

            self.hr_listbox_content = tk.StringVar()
            self.hr_article_list = sorted(self.hr_article_list)
            self.hr_listbox = tk.Listbox(self, height=24, width=35, listvariable=self.hr_listbox_content,
                                         selectmode="multiple")
            self.hr_listbox.grid(column=3, row=1)
            self.hr_listbox.configure(justify=tk.LEFT)
            self.hr_listbox_content.set(self.hr_article_list)

            self.listbox_scroll = tk.Scrollbar(self, command=self.hr_listbox.yview)
            self.listbox_scroll.grid(column=4, row=1, sticky="ns")
            self.hr_listbox['yscrollcommand'] = self.listbox_scroll.set
            tk.Label(self, text="Flag as High Risk:").grid(column=3, row=0, sticky="w")

            # Swap buttons
            self.button_add_hr = tk.Button(self, text=" >> ", command=self.swap_to_hr)
            self.button_add_hr.grid(column=2, row=1, sticky="n", padx=10, pady=45)

            self.button_rem_hr = tk.Button(self, text=" << ", command=self.swap_from_hr)
            self.button_rem_hr.grid(column=2, row=1, sticky="s", padx=10, pady=45)

        def swap_to_hr(self):
            for index in self.article_listbox.curselection():
                self.hr_article_list.append(self.article_listbox.get(index))
                self.article_list.remove(self.article_listbox.get(index))
            self.hr_listbox_content.set(sorted(self.hr_article_list))
            self.article_listbox_content.set(sorted(self.article_list))
            self.hr_listbox.selection_clear(0, "end")
            self.article_listbox.selection_clear(0, "end")
            self.search()

        def swap_from_hr(self):
            for index in self.hr_listbox.curselection():
                self.article_list.append(self.hr_listbox.get(index))
                self.hr_article_list.remove(self.hr_listbox.get(index))
            self.hr_listbox_content.set(sorted(self.hr_article_list))
            self.article_listbox_content.set(sorted(self.article_list))
            self.hr_listbox.selection_clear(0, "end")
            self.article_listbox.selection_clear(0, "end")
            self.search()

        def search(self, *args):
            search_text = self.article_search_text.get().lower()
            self.article_listbox_content.set([])
            results = []
            for article in self.article_list:
                if search_text in str(article).lower():
                    results.append(article)
            self.article_listbox_content.set(results)

        def reset(self):
            self.article_list = []
            for mani in backend.manifests:
                for sscc in mani.ssccs:
                    for article in sscc.articles:
                        article.is_HR = False
                        self.article_list.append(article.code)
            self.article_list = list(dict.fromkeys(self.article_list))  # Remove duplicates
            self.article_listbox_content.set(sorted(self.article_list))
            self.hr_listbox_content.set([])

    class SuggestionsTab(tk.Frame):
        def __init__(self, parent, *args, **kwargs):
            tk.Frame.__init__(self, parent, *args, **kwargs)

            self.article_list = []
            for mani in backend.manifests:
                for sscc in mani.ssccs:
                    if sscc.is_HR:
                        for article in sscc.articles:
                            if not article.is_HR and article.code not in user_settings["hr_articles"]:
                                self.article_list.append(article.code)  # Add to possibilities if has been in a HR box

            for mani in backend.manifests:
                for sscc in mani.ssccs:
                    if not sscc.is_HR:
                        for article in sscc.articles:
                            while article.code in self.article_list:
                                self.article_list.remove(
                                    article.code)  # Remove from possibilities if article has been in a non-HR box

            self.article_list = [i for i in self.article_list if
                                 self.article_list.count(i) > 1]  # Remove all unique entries
            self.article_list = list(dict.fromkeys(self.article_list))  # Remove duplicates

            self.article_listbox_content = tk.StringVar()
            self.article_list = sorted(self.article_list)
            self.article_listbox = tk.Listbox(self, height=20, width=35, listvariable=self.article_listbox_content,
                                              selectmode="multiple")
            self.article_listbox.grid(column=1, row=1, sticky="ne")
            self.article_listbox.configure(justify=tk.LEFT)
            self.article_listbox_content.set(self.article_list)

            self.listbox_scroll = tk.Scrollbar(self, command=self.article_listbox.yview)
            self.listbox_scroll.grid(column=2, row=1, sticky="nse")
            self.article_listbox['yscrollcommand'] = self.listbox_scroll.set
            tk.Label(self, text="Article Suggestions:").grid(column=1, row=0, sticky="w", pady=4)

            self.button_add_suggestions = tk.Button(self, text="Add suggestions", command=self.add_suggestions)
            self.button_add_suggestions.grid(column=1, row=2, pady=4)

            self.columnconfigure(1, weight=1)
            self.columnconfigure(0, weight=10)

            if len(backend.manifests) < 6:
                suggestions_tip_text = "Check in later, this won't be accurate\n with only " + str(
                    len(backend.manifests)) + " manifests stored. (Need 6)"
                self.button_add_suggestions["state"] = "disabled"
            else:
                suggestions_tip_text = "This will be more accurate with more data.\n You currently have " + str(
                    len(backend.manifests)) + " manifests stored."

            tk.Label(self,
                     text="These articles have always been in\nhigh-risk SSCCs but the articles were\n"
                          "never flagged as high risk themselves\n\n"
                          "Here you can add them to automatically flag\nthe carton containing them as high-risk\n\n"
                          + suggestions_tip_text).grid(column=0, row=1)

        def add_suggestions(self):
            for index in self.article_listbox.curselection():
                user_settings["hr_articles"].append(self.article_listbox.get(index))
                self.article_list.remove(self.article_listbox.get(index))
            self.article_listbox_content.set(sorted(self.article_list))
            self.article_listbox.selection_clear(0, "end")
            main_window.control_panel.hr_manager.destroy()
            main_window.control_panel.launch_high_risk_manager()


class DILManager(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.title("Generate DIL Report")
        set_centre_geometry(self, 960, 640)
        root.grab_release()
        self.grab_set()
        self.focus()
        self.resizable(False, False)

        self.bind("<F8>", self.output_dils)
        self.bind('<Escape>', lambda e: self.destroy())

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.target_manifest = backend.get_manifest_from_id(selected_manifest)

        self.control_panel = self.SettingsFrame(self)
        self.control_panel.grid(column=0, row=0, padx=10, pady=8, sticky="ew", columnspan=2)

        self.sscc_frame = self.SSCCFrame(self)
        self.sscc_frame.grid(column=0, row=1, padx=8, pady=(0, 8), sticky="nsew")

        self.article_frame = self.ArticleFrame(self)
        self.article_frame.grid(column=1, row=1, padx=8, pady=(0, 8), sticky="nsew")
        self.article_frame.set_list_state("disabled")

    def change_dil_folder(self):
        request = tkinter.filedialog.askdirectory(parent=self)
        if not len(request) < 1:
            backend.user_settings["DIL folder"] = request
            self.control_panel.label_dil_dir.config(text=("DIL Location: " + str(backend.user_settings["DIL folder"])))

    def dil_mgr_sscc_update(self, *args):  # CALL ON SSCC LIST CHANGE
        if len(self.sscc_frame.sscc_listbox.curselection()) > 0:  # CHECK IF AN SSCC IS SELECTED

            self.sscc_frame.set_state()  # ENABLE SSCC SETTINGS

            # POPULATE AND ENABLE ARTICLE LIST IF SSCC PICKED + SET SSCC SETTINGS
            target_sscc = self.target_manifest.get_sscc(
                (self.sscc_frame.sscc_listbox.get(self.sscc_frame.sscc_listbox.curselection())) \
                    .replace(" ", "").replace("*", ""))  # GET SSCC OBJ FROM MANIFEST
            if target_sscc is not None:
                if target_sscc.dil_status == "missing":
                    self.sscc_frame.rb_missing.select()
                    self.sscc_frame.text_comment.delete(1.0, tk.END)
                    self.sscc_frame.text_comment.insert(1.0, target_sscc.dil_comment)
                else:
                    self.sscc_frame.rb_normal.select()
                    self.sscc_frame.text_comment.delete(1.0, tk.END)

            # POPULATE AND ENABLE ARTICLE SETTINGS
            self.article_list = []
            for article in target_sscc.articles:
                if article.dil_status == "":
                    self.article_list.append(article.code)
                else:
                    self.article_list.append("*" + article.code)
            self.article_frame.listbox_content.set(sorted(self.article_list, key=lambda a: a.replace("*", "")))
            self.article_frame.set_list_state()

            if self.sscc_frame.rb_variable.get() == "normal":  # DISABLE ARTICLE SIDE IF NORMAL ISN'T PICKED
                self.article_frame.set_list_state()
            else:
                self.article_frame.set_list_state("disabled")

        else:
            self.article_frame.set_list_state("disabled")  # DISABLE ARTICLE SIDE
            self.sscc_frame.set_state("disabled")  # DISABLE SSCC SETTINGS

        self.control_panel.update_dil_count()

    def dil_mgr_article_update(self, *args):  # CALL ON ARTICLE LIST CHANGE
        self.article_frame.rb_normal.select()
        self.article_frame.sb_qty.delete(0, tk.END)
        self.article_frame.text_comment.delete(1.0, tk.END)
        self.article_frame.desired_qty.configure(text=("Desired Qty: 0"))

        if len(self.article_frame.article_listbox.curselection()) > 0:
            target_sscc = self.target_manifest.get_sscc(
                (self.sscc_frame.sscc_listbox.get(self.sscc_frame.sscc_listbox.curselection())) \
                    .replace(" ", "").replace("*", ""))  # GET SSCC OBJ FROM MANIFEST

            selected_article = target_sscc.get_article(
                self.article_frame.article_listbox.get(self.article_frame.article_listbox.curselection()) \
                    .replace("*", ""))

            self.article_frame.set_state()
            self.article_frame.sb_qty.insert(0, selected_article.dil_qty)
            self.article_frame.text_comment.insert(1.0, selected_article.dil_comment)
            if selected_article.dil_status == "under":
                self.article_frame.rb_undersupply.select()
            elif selected_article.dil_status == "over":
                self.article_frame.rb_oversupply.select()
            elif selected_article.dil_status == "damaged":
                self.article_frame.rb_damaged.select()

            self.article_frame.desired_qty.configure(text=("Desired Qty: " + str(selected_article.qty)))
        else:
            self.article_frame.set_state("disabled")

        self.control_panel.update_dil_count()

    def write_to_manifest(self, *args):
        if len(self.sscc_frame.sscc_listbox.curselection()) > 0:
            selected_sscc = (self.sscc_frame.sscc_listbox.get(self.sscc_frame.sscc_listbox.curselection())) \
                .replace(" ", "").replace("*", "")

            if len(self.article_frame.article_listbox.curselection()) > 0:
                selected_article = self.article_frame.article_listbox.get(
                    self.article_frame.article_listbox.curselection()).replace("*", "")

            for sscc in backend.get_manifest_from_id(selected_manifest).ssccs:
                if sscc.sscc == selected_sscc:
                    if self.sscc_frame.rb_variable.get() != "normal":
                        sscc.dil_status = self.sscc_frame.rb_variable.get()
                        sscc.dil_comment = str(self.sscc_frame.text_comment.get(1.0, "end-1c"))
                    else:
                        if len(self.article_frame.article_listbox.curselection()) > 0:
                            for article in sscc.articles:
                                if article.code == selected_article:
                                    if (self.article_frame.rb_variable.get() != "normal") and (
                                            int(self.article_frame.sb_qty.get()) != 0):
                                        article.dil_status = self.article_frame.rb_variable.get()
                                        article.dil_qty = int(self.article_frame.sb_qty.get())
                                        article.dil_comment = str(self.article_frame.text_comment.get(1.0, "end-1c"))
                                    else:
                                        sscc.dil_status = ""
                                        article.dil_status = ""
                                        article.dil_qty = 0
                                        article.dil_comment = ""
                                        sscc.dil_comment = ""
                        else:
                            sscc.dil_status = ""
                            sscc.dil_comment = ""

            self.article_frame.set_list_state()

            # WRITE NEW ARTICLE LIST
            self.article_list = []
            for article in backend.get_manifest_from_id(selected_manifest).get_sscc(selected_sscc).articles:
                if article.dil_status == "":
                    self.article_list.append(article.code)
                else:
                    self.article_list.append("*" + article.code)
            self.article_frame.listbox_content.set(sorted(self.article_list, key=lambda a: a.replace("*", "")))

        # WRITE A NEW SSCC LIST
        sscc_list = []
        for sscc in backend.get_manifest_from_id(selected_manifest).ssccs:
            if not sscc.check_dil():
                sscc_list.append(sscc.sscc[:-4] + " " + last_four(sscc.sscc))
            else:
                sscc_list.append("*" + sscc.sscc[:-4] + " " + last_four(sscc.sscc))
        self.sscc_frame.listbox_content.set(sorted(sscc_list, key=last_four))

    def output_dils(self, *args):
        self.write_to_manifest()
        if self.control_panel.update_dil_count() != 0:
            backend.generate_DIL(selected_manifest)
            tkinter.messagebox.showinfo("Success", "DILs successfully generated!")
            self.destroy()
        else:
            tkinter.messagebox.showerror("Can i get uhhhh...",
                                         "There are no DILs to generate!", parent=self)

    def reset_all(self):
        if tkinter.messagebox.askyesno("Hol up!",
                                       "This will clear all delivery issues for this manifest!\n"
                                       "Are you sure you want to do this?", parent=self):
            for sscc in self.target_manifest.ssccs:
                sscc.dil_status = ""
                sscc.dil_comment = ""
                for article in sscc.articles:
                    article.dil_status = ""
                    article.dil_comment = ""
                    article.dil_qty = 0
            self.article_frame.article_listbox.selection_clear(0, tk.END)
            self.sscc_frame.sscc_listbox.selection_clear(0, tk.END)

            self.dil_mgr_sscc_update()
            self.dil_mgr_article_update()
            self.write_to_manifest()

    class SettingsFrame(tk.LabelFrame):
        def __init__(self, parent, *args, **kwargs):
            tk.LabelFrame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            self["text"] = "Settings"
            self.columnconfigure(9, weight=1)

            tk.Label(self, text=("Manifest: " + str(backend.get_manifest_from_id(selected_manifest)))) \
                .grid(column=0, row=0, padx=10, pady=4)

            self.label_dil_dir = tk.Label(self, text=("DIL Location: " + str(backend.user_settings["DIL folder"])))
            self.label_dil_dir.grid(column=1, row=0, padx=10, pady=4)

            self.label_dil_count = tk.Label(self, text=("DILs to generate: "))
            self.label_dil_count.grid(column=2, row=0, padx=10, pady=4)

            self.button_reset = tk.Button(self, text="Reset", command=parent.reset_all)
            self.button_reset.grid(column=10, row=0, padx=4, pady=4, sticky="e")
            self.button_reset["state"] = "disabled"

            self.button_dil_folder = tk.Button(self, text="Change DIL Folder", command=parent.change_dil_folder)
            self.button_dil_folder.grid(column=11, row=0, padx=4, pady=4, sticky="e")

            self.button_output_dil = tk.Button(self, text="Generate (F8)", command=parent.output_dils)
            self.button_output_dil.grid(column=12, row=0, padx=4, pady=4, sticky="e")

            self.update_dil_count()

        def update_dil_count(self):
            self.dil_count = 0
            for sscc in backend.get_manifest_from_id(selected_manifest).ssccs:
                if sscc.dil_status == "":
                    for article in sscc.articles:
                        if article.dil_status != "":
                            self.dil_count += 1
                            break
                else:
                    self.dil_count += 1
            self.label_dil_count.config(text=("DILs to generate: " + str(self.dil_count)))
            if self.dil_count > 0:
                self.button_reset["state"] = "normal"
            else:
                self.button_reset["state"] = "disabled"
            return self.dil_count

    class SSCCFrame(tk.LabelFrame):
        def __init__(self, parent, *args, **kwargs):
            tk.LabelFrame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            self["text"] = "SSCCs"

            self.sscc_list = []
            for sscc in backend.get_manifest_from_id(selected_manifest).ssccs:
                if not sscc.check_dil():
                    self.sscc_list.append(sscc.sscc[:-4] + " " + last_four(sscc.sscc))
                else:
                    self.sscc_list.append("*" + sscc.sscc[:-4] + " " + last_four(sscc.sscc))

            self.listbox_content = tk.StringVar()
            self.sscc_listbox = tk.Listbox(self, width=32, height=32, listvariable=self.listbox_content,
                                           selectmode="single", exportselection=False)
            self.sscc_listbox.grid(column=0, row=0, padx=4, pady=4, rowspan=7)
            self.sscc_listbox.configure(justify=tk.RIGHT)
            self.listbox_content.set(sorted(self.sscc_list, key=last_four))
            self.listbox_scroll = tk.Scrollbar(self, command=self.sscc_listbox.yview)
            self.listbox_scroll.grid(column=1, row=0, sticky="ns", rowspan=7)
            self.sscc_listbox['yscrollcommand'] = self.listbox_scroll.set
            self.sscc_listbox.bind("<<ListboxSelect>>", self.sscc_list_callback)

            tk.Label(self, text="Whole Carton Status:").grid(column=2, row=0, padx=8, pady=4, sticky="sw")

            self.rb_variable = tk.StringVar()
            self.rb_normal = tk.Radiobutton(self, text="Normal", variable=self.rb_variable, value="normal",
                                            command=self.rb_callback, state="disabled")
            self.rb_normal.grid(column=2, row=1, padx=8, pady=4, sticky="w")
            self.rb_missing = tk.Radiobutton(self, text="Missing", variable=self.rb_variable, value="missing",
                                             command=self.rb_callback, state="disabled")
            self.rb_missing.grid(column=2, row=2, padx=8, pady=4, sticky="w")
            self.rb_normal.select()

            tk.Label(self, text="Comments:").grid(column=2, row=3, padx=8, pady=4, sticky="sw")

            self.text_comment = tk.Text(self, width=26, height=12)
            self.text_comment.grid(column=2, row=4, padx=8, pady=4, sticky="nw")
            self.text_comment.bind("<KeyRelease>", self.rb_callback)

            self.rowconfigure(5, weight=2)

        def set_state(self, state="normal"):
            self.rb_normal["state"] = state
            self.rb_missing["state"] = state
            self.text_comment["state"] = state

        def sscc_list_callback(self, *args):  # ON LISTBOX SELECTION
            self.parent.dil_mgr_sscc_update()

        def rb_callback(self, *args):
            self.parent.write_to_manifest()
            self.parent.dil_mgr_sscc_update()

    class ArticleFrame(tk.LabelFrame):
        def __init__(self, parent, *args, **kwargs):
            tk.LabelFrame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            self["text"] = "Articles"

            self.listbox_content = tk.StringVar()
            self.article_listbox = tk.Listbox(self, width=32, height=32, listvariable=self.listbox_content,
                                              selectmode="single", exportselection=False)
            self.article_listbox.grid(column=0, row=0, padx=4, pady=4, rowspan=11)
            self.article_listbox.configure(justify=tk.RIGHT)
            self.listbox_scroll = tk.Scrollbar(self, command=self.article_listbox.yview)
            self.listbox_scroll.grid(column=1, row=0, sticky="ns", rowspan=11)
            self.article_listbox['yscrollcommand'] = self.listbox_scroll.set
            self.article_listbox.bind("<<ListboxSelect>>", self.article_list_callback)

            tk.Label(self, text="Article Status:").grid(column=2, row=0, padx=8, pady=4, sticky="sw")

            self.rb_variable = tk.StringVar()
            self.rb_normal = tk.Radiobutton(self, text="Normal", variable=self.rb_variable, value="normal",
                                            command=self.other_callback)
            self.rb_normal.grid(column=2, row=1, padx=8, pady=4, sticky="w")
            self.rb_undersupply = tk.Radiobutton(self, text="Undersupply", variable=self.rb_variable, value="under",
                                                 command=self.other_callback)
            self.rb_undersupply.grid(column=2, row=2, padx=8, pady=4, sticky="w")
            self.rb_oversupply = tk.Radiobutton(self, text="Oversupply", variable=self.rb_variable,
                                                value="over", command=self.other_callback)
            self.rb_oversupply.grid(column=2, row=3, padx=8, pady=4, sticky="w")
            self.rb_damaged = tk.Radiobutton(self, text="Damaged", variable=self.rb_variable,
                                             value="damaged", command=self.other_callback)
            self.rb_damaged.grid(column=2, row=4, padx=8, pady=4, sticky="w")
            self.rb_normal.select()

            self.desired_qty = tk.Label(self, text="Desired Qty:")
            self.desired_qty.grid(column=2, row=5, padx=8, pady=4, sticky="sw")

            tk.Label(self, text="Problem Qty:").grid(column=2, row=6, padx=8, pady=4, sticky="sw")

            self.sb_qty = tk.Spinbox(self, from_=0, to=9999, command=self.other_callback)
            self.sb_qty.grid(column=2, row=7, padx=8, pady=4, sticky="w")
            self.sb_qty.bind("<KeyRelease>", self.other_callback)

            tk.Label(self, text="Comments:").grid(column=2, row=8, padx=8, pady=4, sticky="sw")

            self.text_comment = tk.Text(self, width=26, height=12)
            self.text_comment.grid(column=2, row=9, padx=8, pady=4, sticky="nw")
            self.text_comment.bind("<KeyRelease>", self.other_callback)

            self.rowconfigure(10, weight=2)

            self.set_state("disabled")
            self.set_list_state("disabled")

        def set_list_state(self, state="normal"):
            self.article_listbox["state"] = state

        def set_state(self, state="normal"):
            self.rb_normal["state"] = state
            self.rb_undersupply["state"] = state
            self.rb_oversupply["state"] = state
            self.rb_damaged["state"] = state
            self.text_comment["state"] = state
            self.sb_qty["state"] = state

        def article_list_callback(self, *args):  # ON LISTBOX SELECTION
            self.parent.dil_mgr_article_update()

        def other_callback(self, *args):
            self.parent.write_to_manifest()


# noinspection PyBroadException
def do_argv_check():
    if len(system.argv) > 1:
        try:
            imported_manifest_id = backend.mhtml_importer(system.argv[1])
            main_window.interface_update()

            main_window.control_panel.combo_select_manifest.set(imported_manifest_id)
            main_window.interface_update()
        except Exception as e:
            pass


def exit_app():
    backend.json_save()
    root.destroy()
    system.exit()


def last_four(string):
    return str(string)[-4:]


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))


if __name__ == "__main__":
    root = tk.Tk()
    base_title = "X-Dock Manager - " + application_version + " - "
    root.title(base_title + "Ready")
    root.iconbitmap("XDMGR.ico")
    set_centre_geometry(root, 1024, 768)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.wm_protocol("WM_DELETE_WINDOW", lambda: exit_app())
    root.minsize(1024, 768)

    main_window = XDTApplication(root)
    main_window.grid(column=0, row=0, sticky="nsew")

    root.after(150, do_argv_check)
    root.mainloop()
