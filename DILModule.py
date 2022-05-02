import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

import BackendModule as backend


class DILManager(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, **kwargs)
        self.app_parent = parent

        self.title("Generate DIL Report")
        set_centre_geometry(self, 720, 600)
        self.grab_set()
        self.focus()
        self.resizable(False, False)
        self.iconbitmap("XDMGR.ico")

        self.bind("<F8>", self.output_dils)
        self.bind('<Escape>', lambda e: self.close_no_save())
        self.wm_protocol("WM_DELETE_WINDOW", lambda: self.close_no_save())

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.target_manifest = backend.get_manifest_from_id(backend.selected_manifest)
        self.target_manifest.last_modified = backend.current_milli_time()

        self.control_panel = self.SettingsFrame(self)
        self.control_panel.grid(column=0, row=0, padx=8, pady=8, sticky="ew")

        self.sscc_frame = self.SSCCFrame(self)
        self.sscc_frame.grid(column=0, row=1, padx=8, pady=(0, 8), sticky="nsew")

    def change_dil_folder(self):
        request = tk.filedialog.askdirectory(parent=self)
        if not len(request) < 1:
            backend.user_settings["DIL folder"] = request
            self.control_panel.label_dil_dir.config(text=("DIL Location: " + str(backend.user_settings["DIL folder"])))

    def dil_mgr_sscc_update(self, *args):  # CALL ON SSCC LIST CHANGE
        if len(self.sscc_frame.sscc_listbox.curselection()) > 0:  # CHECK IF AN SSCC IS SELECTED

            self.sscc_frame.set_state()  # ENABLE SSCC SETTINGS

            # SET SSCC SETTINGS
            target_sscc = self.target_manifest.get_sscc(
                (self.sscc_frame.sscc_listbox.get(self.sscc_frame.sscc_listbox.curselection())).replace(" ",
                                                                                                        "").replace("*",
                                                                                                                    ""))
            if target_sscc is not None:
                if target_sscc.dil_status == "missing":
                    self.sscc_frame.rb_missing.select()
                    self.sscc_frame.text_comment.delete(1.0, tk.END)
                    self.sscc_frame.text_comment.insert(1.0, target_sscc.dil_comment)
                else:
                    self.sscc_frame.rb_normal.select()
                    self.sscc_frame.text_comment.delete(1.0, tk.END)

                # POPULATE ARTICLE LIST
                article_text = ""
                for article in target_sscc.articles:
                    article_text += str(article.code) + "  x " + str(article.qty) + "\n"

                self.sscc_frame.article_text_field.config(state="normal")
                self.sscc_frame.article_text_field.delete(1.0, tk.END)
                self.sscc_frame.article_text_field.insert(1.0, article_text)
                self.sscc_frame.article_text_field.config(state="disabled")

        else:
            self.sscc_frame.set_state("disabled")  # DISABLE SSCC SETTINGS

            self.sscc_frame.article_text_field.config(state="normal")
            self.sscc_frame.article_text_field.delete(1.0, tk.END)
            self.sscc_frame.article_text_field.config(state="disabled")

        self.control_panel.update_dil_count()

    def write_to_manifest(self, *args):
        if len(self.sscc_frame.sscc_listbox.curselection()) > 0:
            selected_sscc = (self.sscc_frame.sscc_listbox.get(self.sscc_frame.sscc_listbox.curselection())) \
                .replace(" ", "").replace("*", "")

            selected_article = []

            backend.update_manifest_timestamp(backend.selected_manifest)

            for sscc in backend.get_manifest_from_id(backend.selected_manifest).ssccs:
                if sscc.sscc == selected_sscc:
                    if self.sscc_frame.rb_variable.get() != "normal":
                        sscc.dil_status = self.sscc_frame.rb_variable.get()
                        sscc.dil_comment = str(self.sscc_frame.text_comment.get(1.0, "end-1c"))
                    else:
                        sscc.dil_status = ""
                        sscc.dil_comment = ""

        # WRITE A NEW SSCC LIST
        sscc_list = []
        for sscc in backend.get_manifest_from_id(backend.selected_manifest).ssccs:
            if not sscc.check_dil():
                sscc_list.append(sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))
            else:
                sscc_list.append("*" + sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))
        self.sscc_frame.listbox_content.set(sorted(sscc_list, key=backend.last_four))

    def output_dils(self, *args):
        self.write_to_manifest()
        if self.control_panel.update_dil_count() != 0:
            backend.generate_DIL(backend.selected_manifest)
            tk.messagebox.showinfo("Success", "DILs successfully generated!", parent=self)
            self.app_parent.parent_XDT_app.interface_update()
        else:
            tk.messagebox.showerror("Hol up!",
                                    "There are no DILs to generate!", parent=self)

    def reset_all(self):
        if tk.messagebox.askyesno("Hol up!",
                                  "This will clear all delivery issues for this manifest!\n"
                                  "Are you sure you want to do this?", parent=self):
            for sscc in self.target_manifest.ssccs:
                sscc.dil_status = ""
                sscc.dil_comment = ""
                for article in sscc.articles:
                    article.dil_status = ""
                    article.dil_comment = ""
                    article.dil_qty = 0
            self.sscc_frame.sscc_listbox.selection_clear(0, tk.END)

            self.dil_mgr_sscc_update()
            self.write_to_manifest()

    def close_no_save(self):
        self.app_parent.parent_XDT_app.interface_update()
        self.destroy()

    class SettingsFrame(tk.LabelFrame):
        def __init__(self, parent, *args, **kwargs):
            super().__init__(parent, **kwargs)
            self.parent = parent
            self["text"] = "Settings"
            self.columnconfigure(9, weight=1)

            tk.Label(self, text=("Manifest: " + str(backend.get_manifest_from_id(backend.selected_manifest)))) \
                .grid(column=0, row=0, padx=10, pady=4, sticky='w')

            self.label_dil_dir = tk.Label(self, text=("DIL Location: " + str(backend.user_settings["DIL folder"])))
            self.label_dil_dir.grid(column=0, row=1, padx=10, pady=4, sticky='w', columnspan=2)

            self.label_dil_count = tk.Label(self, text="Issues in Manifest: ")
            self.label_dil_count.grid(column=1, row=0, padx=10, pady=4, sticky='w')

            self.button_reset = tk.Button(self, text="Reset", command=parent.reset_all)
            self.button_reset.grid(column=10, row=0, padx=4, pady=4, sticky="e")
            self.button_reset["state"] = "disabled"

            self.button_dil_folder = tk.Button(self, text="Change DIL Folder", command=parent.change_dil_folder)
            self.button_dil_folder.grid(column=11, row=0, padx=4, pady=4, sticky="e")

            self.button_dil_folder = tk.Button(self, text="Open DIL Folder", command=self.open_dil_folder)
            self.button_dil_folder.grid(column=12, row=0, padx=4, pady=4, sticky="e")

            self.button_output_dil = tk.Button(self, text="Generate (F8)", command=parent.output_dils)
            self.button_output_dil.grid(column=13, row=0, padx=4, pady=4, sticky="e")

            self.update_dil_count()

            self.dil_count = 0

        def update_dil_count(self):
            self.dil_count = 0
            for sscc in backend.get_manifest_from_id(backend.selected_manifest).ssccs:
                if sscc.dil_status == "":
                    for article in sscc.articles:
                        if article.dil_status != "":
                            self.dil_count += 1
                            break
                else:
                    self.dil_count += 1
            self.label_dil_count.config(text=("Issues in Manifest: " + str(self.dil_count)))
            if self.dil_count > 0:
                self.button_reset["state"] = "normal"
            else:
                self.button_reset["state"] = "disabled"
            return self.dil_count

        @staticmethod
        def open_dil_folder():
            explorer_path = os.path.join(os.getenv("WINDIR"), "explorer.exe")
            dil_path = os.path.normpath(backend.user_settings.get("DIL folder"))
            if os.path.isdir(dil_path):
                subprocess.run([explorer_path, dil_path])

    class SSCCFrame(tk.LabelFrame):
        def __init__(self, parent, *args, **kwargs):
            super().__init__(parent, **kwargs)
            self.parent = parent
            self["text"] = "SSCCs"

            self.sscc_list = []
            for sscc in backend.get_manifest_from_id(backend.selected_manifest).ssccs:
                if not sscc.check_dil():
                    self.sscc_list.append(sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))
                else:
                    self.sscc_list.append("*" + sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))

            # SSCC BOX SELECTION (COL 0+1)
            self.listbox_content = tk.StringVar()
            self.sscc_listbox = tk.Listbox(self, width=32, listvariable=self.listbox_content,
                                           selectmode="single", exportselection=False)
            self.sscc_listbox.grid(column=0, row=0, padx=4, pady=8, rowspan=5, sticky='ns')
            self.sscc_listbox.configure(justify=tk.RIGHT)
            self.listbox_content.set(sorted(self.sscc_list, key=backend.last_four))

            self.listbox_scroll = tk.Scrollbar(self, command=self.sscc_listbox.yview)
            self.listbox_scroll.grid(column=1, row=0, pady=8, sticky="ns", rowspan=5)
            self.sscc_listbox['yscrollcommand'] = self.listbox_scroll.set
            self.sscc_listbox.bind("<<ListboxSelect>>", self.sscc_list_callback)

            # SSCC BOX CONTENT (COL 2+3)
            self.article_text_field = tk.Text(self, width=26, state="disabled")
            self.article_text_field.grid(column=2, row=0, sticky="ns", rowspan=5, padx=8, pady=8)

            self.article_list_scroll = tk.Scrollbar(self, command=self.sscc_listbox.yview)
            self.article_list_scroll.grid(column=3, row=0, pady=8, sticky="ns", rowspan=5)
            self.article_text_field['yscrollcommand'] = self.article_list_scroll.set

            # SSCC BOX STATUS (COL 4+5)
            tk.Label(self, text="Carton Status:").grid(column=4, row=1, padx=8, pady=8, sticky="w", columnspan=2)

            self.rb_variable = tk.StringVar()
            self.rb_normal = tk.Radiobutton(self, text="Normal", variable=self.rb_variable, value="normal",
                                            command=self.rb_callback, state="disabled")
            self.rb_normal.grid(column=4, row=2, padx=8, pady=4, sticky="w")
            self.rb_missing = tk.Radiobutton(self, text="Missing", variable=self.rb_variable, value="missing",
                                             command=self.rb_callback, state="disabled")
            self.rb_missing.grid(column=5, row=2, padx=8, pady=4, sticky="w")
            self.rb_normal.select()

            tk.Label(self, text="Comments:").grid(column=4, row=3, padx=8, pady=(16, 4), sticky="sw")

            self.text_comment = tk.Text(self, width=26)
            self.text_comment.grid(column=4, row=4, padx=8, pady=4, sticky="nws", columnspan=2)
            self.text_comment.bind("<KeyRelease>", self.rb_callback)

            self.rowconfigure(2, weight=1)
            self.rowconfigure(3, weight=1)
            self.rowconfigure(4, weight=1)

        def set_state(self, state="normal"):
            self.rb_normal["state"] = state
            self.rb_missing["state"] = state
            self.text_comment["state"] = state

        def sscc_list_callback(self, *args):  # ON LISTBOX SELECTION
            self.parent.dil_mgr_sscc_update()

        def rb_callback(self, *args):
            self.parent.write_to_manifest()
            self.parent.dil_mgr_sscc_update()


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))
