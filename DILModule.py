import tkinter as tk
from tkinter import filedialog, messagebox

import AppModule as app
import BackendModule as backend


class DILManager(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.title("Generate DIL Report")
        app.set_centre_geometry(self, 960, 640)
        app.root.grab_release()
        self.grab_set()
        self.focus()
        self.resizable(False, False)

        self.bind("<F8>", self.output_dils)
        self.bind('<Escape>', lambda e: self.destroy())

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.target_manifest = backend.get_manifest_from_id(backend.selected_manifest)
        self.target_manifest.last_modified = backend.current_milli_time()

        self.control_panel = self.SettingsFrame(self)
        self.control_panel.grid(column=0, row=0, padx=10, pady=8, sticky="ew", columnspan=2)

        self.sscc_frame = self.SSCCFrame(self)
        self.sscc_frame.grid(column=0, row=1, padx=8, pady=(0, 8), sticky="nsew")

        self.article_frame = self.ArticleFrame(self)
        self.article_frame.grid(column=1, row=1, padx=8, pady=(0, 8), sticky="nsew")
        self.article_frame.set_list_state("disabled")

        self.article_list = []

    def change_dil_folder(self):
        request = tk.filedialog.askdirectory(parent=self)
        if not len(request) < 1:
            backend.user_settings["DIL folder"] = request
            self.control_panel.label_dil_dir.config(text=("DIL Location: " + str(backend.user_settings["DIL folder"])))

    def dil_mgr_sscc_update(self, *args):  # CALL ON SSCC LIST CHANGE
        if len(self.sscc_frame.sscc_listbox.curselection()) > 0:  # CHECK IF AN SSCC IS SELECTED

            self.sscc_frame.set_state()  # ENABLE SSCC SETTINGS

            # POPULATE AND ENABLE ARTICLE LIST IF SSCC PICKED + SET SSCC SETTINGS
            target_sscc = self.target_manifest.get_sscc(
                (self.sscc_frame.sscc_listbox.get(self.sscc_frame.sscc_listbox.curselection())).replace(" ", "").replace("*", ""))  # GET SSCC OBJ FROM MANIFEST
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
        self.article_frame.desired_qty.configure(text="Desired Qty: 0")

        if len(self.article_frame.article_listbox.curselection()) > 0:
            target_sscc = self.target_manifest.get_sscc(
                (self.sscc_frame.sscc_listbox.get(self.sscc_frame.sscc_listbox.curselection())).replace(" ", "").replace("*", ""))  # GET SSCC OBJ FROM MANIFEST

            selected_article = target_sscc.get_article(
                self.article_frame.article_listbox.get(self.article_frame.article_listbox.curselection()).replace("*", ""))

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

            selected_article = []

            backend.update_manifest_timestamp(backend.selected_manifest)

            if len(self.article_frame.article_listbox.curselection()) > 0:
                selected_article = self.article_frame.article_listbox.get(
                    self.article_frame.article_listbox.curselection()).replace("*", "")

            for sscc in backend.get_manifest_from_id(backend.selected_manifest).ssccs:
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
            for article in backend.get_manifest_from_id(backend.selected_manifest).get_sscc(selected_sscc).articles:
                if article.dil_status == "":
                    self.article_list.append(article.code)
                else:
                    self.article_list.append("*" + article.code)
            self.article_frame.listbox_content.set(sorted(self.article_list, key=lambda a: a.replace("*", "")))

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
            tk.messagebox.showinfo("Success", "DILs successfully generated!")
            self.destroy()
        else:
            tk.messagebox.showerror("Can i get uhhhh...",
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

            tk.Label(self, text=("Manifest: " + str(backend.get_manifest_from_id(backend.selected_manifest)))) \
                .grid(column=0, row=0, padx=10, pady=4)

            self.label_dil_dir = tk.Label(self, text=("DIL Location: " + str(backend.user_settings["DIL folder"])))
            self.label_dil_dir.grid(column=1, row=0, padx=10, pady=4)

            self.label_dil_count = tk.Label(self, text="DILs to generate: ")
            self.label_dil_count.grid(column=2, row=0, padx=10, pady=4)

            self.button_reset = tk.Button(self, text="Reset", command=parent.reset_all)
            self.button_reset.grid(column=10, row=0, padx=4, pady=4, sticky="e")
            self.button_reset["state"] = "disabled"

            self.button_dil_folder = tk.Button(self, text="Change DIL Folder", command=parent.change_dil_folder)
            self.button_dil_folder.grid(column=11, row=0, padx=4, pady=4, sticky="e")

            self.button_output_dil = tk.Button(self, text="Generate (F8)", command=parent.output_dils)
            self.button_output_dil.grid(column=12, row=0, padx=4, pady=4, sticky="e")

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
            for sscc in backend.get_manifest_from_id(backend.selected_manifest).ssccs:
                if not sscc.check_dil():
                    self.sscc_list.append(sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))
                else:
                    self.sscc_list.append("*" + sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))

            self.listbox_content = tk.StringVar()
            self.sscc_listbox = tk.Listbox(self, width=32, height=32, listvariable=self.listbox_content,
                                           selectmode="single", exportselection=False)
            self.sscc_listbox.grid(column=0, row=0, padx=4, pady=4, rowspan=7)
            self.sscc_listbox.configure(justify=tk.RIGHT)
            self.listbox_content.set(sorted(self.sscc_list, key=backend.last_four))
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
