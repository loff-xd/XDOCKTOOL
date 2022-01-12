import tkinter as tk
from tkinter import ttk, messagebox

import AppModule as app
import BackendModule as backend


class HighRiskManager(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.title("High Risk Manager")
        app.set_centre_geometry(self, 640, 480)
        app.root.grab_release()
        self.grab_set()
        self.focus()
        self.resizable(False, False)

        self.bind("<F8>", self.close_hr_manager)
        self.bind('<Escape>', lambda e: self.destroy())

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.manifest = backend.get_manifest_from_id(backend.selected_manifest)

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
        backend.user_settings["hr_articles"] = article_listbox_content

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

        backend.manifests.remove(backend.get_manifest_from_id(backend.selected_manifest))
        backend.manifests.append(self.manifest)
        backend.json_save()
        app.main_window.interface_update()
        self.grab_release()
        app.root.grab_set()
        self.destroy()

    def reset_hr_manager(self):
        if tk.messagebox.askyesno("Hol up!",
                                       "This will clear all user-set articles to be automatically marked as high risk! "
                                       "Are you sure you want to do this?", parent=self):
            backend.user_settings["hr_articles"] = []
            self.article_tab.reset()

    class SSCCTab(tk.Frame):
        def __init__(self, parent, manifest, *args, **kwargs):
            tk.Frame.__init__(self, parent, *args, **kwargs)

            # List side
            self.sscc_list = []
            for sscc in manifest.ssccs:
                if not sscc.is_HR:
                    self.sscc_list.append(sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))

            self.listbox_content = tk.StringVar()
            self.sscc_list = sorted(self.sscc_list, key=backend.last_four)
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
                    self.hr_sscc_list.append(sscc.sscc[:-4] + " " + backend.last_four(sscc.sscc))

            self.hr_listbox_content = tk.StringVar()
            self.hr_sscc_list = sorted(self.hr_sscc_list, key=backend.last_four)
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
            self.hr_listbox_content.set(sorted(self.hr_sscc_list, key=backend.last_four))
            self.listbox_content.set(sorted(self.sscc_list, key=backend.last_four))
            self.hr_listbox.selection_clear(0, "end")
            self.sscc_listbox.selection_clear(0, "end")

        def swap_from_hr(self):
            for index in self.hr_listbox.curselection():
                self.sscc_list.append(self.hr_listbox.get(index))
                self.hr_sscc_list.remove(self.hr_listbox.get(index))
            self.hr_listbox_content.set(sorted(self.hr_sscc_list, key=backend.last_four))
            self.listbox_content.set(sorted(self.sscc_list, key=backend.last_four))
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
                        if not article.is_HR and article.code not in backend.user_settings["hr_articles"]:
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
            self.hr_article_list = backend.user_settings["hr_articles"]
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
                            if not article.is_HR and article.code not in backend.user_settings["hr_articles"]:
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
                backend.user_settings["hr_articles"].append(self.article_listbox.get(index))
                self.article_list.remove(self.article_listbox.get(index))
            self.article_listbox_content.set(sorted(self.article_list))
            self.article_listbox.selection_clear(0, "end")
            app.main_window.control_panel.hr_manager.destroy()
            app.main_window.control_panel.launch_high_risk_manager()