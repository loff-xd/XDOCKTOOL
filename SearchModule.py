import tkinter as tk
import time

import BackendModule as backend


class SearchWindow(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.app_parent = parent

        self.title("Search")
        set_centre_geometry(self, 960, 640)
        self.grab_set()
        self.focus()
        self.resizable(False, False)
        self.iconbitmap("XDMGR.ico")

        self.bind("<Return>", self.search)
        self.bind("<F8>", self.send_to_application)
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Left>', self.previous)
        self.bind('<Right>', self.next)
        self.bind('<Up>', self.prev_manifest)
        self.bind('<Down>', self.next_manifest)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.settings_frame = self.SettingsFrame(self)
        self.settings_frame.grid(column=0, row=0, padx=10, pady=8, sticky="nsew")

        self.results_frame = self.ResultsFrame(self)
        self.results_frame.grid(column=0, row=1, padx=10, pady=8, sticky="nsew")

        self.match_list = []
        self.match_list_pos = 0

    def next(self, *args):
        if len(self.match_list) > 1:
            self.results_frame.article_output['state'] = 'normal'
            self.results_frame.article_output.tag_remove("selection", self.match_list[self.match_list_pos][0],
                                                         self.match_list[self.match_list_pos][1])
            self.results_frame.article_output.tag_add("match", self.match_list[self.match_list_pos][0],
                                                      self.match_list[self.match_list_pos][1])

            if self.match_list_pos + 1 < len(self.match_list):
                self.match_list_pos += 1
            else:
                self.match_list_pos = 0

            self.results_frame.article_output.tag_remove("match", self.match_list[self.match_list_pos][0],
                                                         self.match_list[self.match_list_pos][1])
            self.results_frame.article_output.tag_add("selection", self.match_list[self.match_list_pos][0],
                                                      self.match_list[self.match_list_pos][1])
            self.results_frame.article_output.see(self.match_list[self.match_list_pos][0])
            self.results_frame.article_output['state'] = 'disabled'
            self.settings_frame.pos_label["text"] = "[" + str(self.match_list_pos + 1) + "/" + str(
                len(self.match_list)) + "]"

    def previous(self, *args):
        if len(self.match_list) > 1:
            self.results_frame.article_output['state'] = 'normal'
            self.results_frame.article_output.tag_remove("selection", self.match_list[self.match_list_pos][0],
                                                         self.match_list[self.match_list_pos][1])
            self.results_frame.article_output.tag_add("match", self.match_list[self.match_list_pos][0],
                                                      self.match_list[self.match_list_pos][1])

            if self.match_list_pos - 1 >= 0:
                self.match_list_pos -= 1
            else:
                self.match_list_pos = len(self.match_list) - 1

            self.results_frame.article_output.tag_remove("match", self.match_list[self.match_list_pos][0],
                                                         self.match_list[self.match_list_pos][1])
            self.results_frame.article_output.tag_add("selection", self.match_list[self.match_list_pos][0],
                                                      self.match_list[self.match_list_pos][1])
            self.results_frame.article_output.see(self.match_list[self.match_list_pos][0])
            self.results_frame.article_output['state'] = 'disabled'
            self.settings_frame.pos_label["text"] = "[" + str(self.match_list_pos + 1) + "/" + str(
                len(self.match_list)) + "]"

    def next_manifest(self, *args):
        list_len = self.results_frame.manifest_listbox.size()
        if list_len > 0:
            pos = self.results_frame.manifest_listbox.curselection()[0]
            new_pos = 0
            if not pos == list_len - 1:
                new_pos = pos + 1
            self.results_frame.manifest_listbox.selection_clear(0, tk.END)
            self.results_frame.manifest_listbox.see(new_pos)
            self.results_frame.manifest_listbox.selection_set(new_pos)
            self.results_frame.manifest_listbox.index(new_pos)
            self.results_frame.manifest_listbox_callback()

    def prev_manifest(self, *args):
        list_len = self.results_frame.manifest_listbox.size()
        if list_len > 0:
            pos = self.results_frame.manifest_listbox.curselection()[0]
            new_pos = pos - 1
            if new_pos < 0:
                new_pos = list_len - 1
            self.results_frame.manifest_listbox.selection_clear(0, tk.END)
            self.results_frame.manifest_listbox.see(new_pos)
            self.results_frame.manifest_listbox.selection_set(new_pos)
            self.results_frame.manifest_listbox.index(new_pos)
            self.results_frame.manifest_listbox_callback()

    class SettingsFrame(tk.LabelFrame):
        def __init__(self, parent, *args, **kwargs):
            tk.LabelFrame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            self["text"] = "Query:"
            self.columnconfigure(7, weight=1)

            tk.Label(self, text="Search Term:").grid(column=0, row=0, padx=(12, 0), pady=4, sticky="w")

            self.search_query_entry = tk.Entry(self, width=32)
            self.search_query_entry.grid(column=1, row=0, padx=4, pady=4, sticky="w")
            self.search_query_entry.focus_set()

            self.button_clear = tk.Button(self, text="X", command=self.clear_results)
            self.button_clear.grid(column=2, row=0, padx=(0, 4), pady=4)

            self.button_search_image = tk.PhotoImage(file=backend.SEARCHICON)
            self.button_search = tk.Button(self, image=self.button_search_image, command=parent.search,
                                           height=20, width=20)
            self.button_search.grid(column=3, row=0, padx=(4, 4), pady=4)

            self.button_prev = tk.Button(self, text="< PREV", command=self.parent.previous)
            self.button_prev.grid(column=4, row=0, padx=(64, 4), pady=4)

            self.pos_label = tk.Label(self, text="[0/0]")
            self.pos_label.grid(column=5, row=0, padx=(2, 2), pady=4)

            self.button_next = tk.Button(self, text="NEXT >", command=self.parent.next)
            self.button_next.grid(column=6, row=0, padx=(2, 4), pady=4)

            self.button_send = tk.Button(self, text="Open Manifest (F8)", command=self.parent.send_to_application)
            self.button_send.grid(column=7, row=0, padx=(2, 4), pady=4, sticky="e")

        def clear_results(self, *args):
            self.search_query_entry.delete(0, tk.END)
            self.parent.results_frame.manifest_listbox_content.set([])
            self.parent.results_frame.text_frame_update("Ready")

            self.parent.results_frame.article_output['state'] = 'normal'
            self.parent.results_frame.article_output.delete('1.0', tk.END)
            self.parent.results_frame.article_output['state'] = 'disabled'
            self.search_query_entry.focus_set()
            self.pos_label["text"] = "[0/0]"

    class ResultsFrame(tk.LabelFrame):
        selected_manifest: backend.Manifest

        def __init__(self, parent, *args, **kwargs):
            tk.LabelFrame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            self["text"] = "Results: (Ready)"

            self.columnconfigure(2, weight=1)
            self.rowconfigure(0, weight=0)
            self.rowconfigure(1, weight=1)

            tk.Label(self, text="Manifest:").grid(column=0, row=0, sticky="w", padx=8)

            self.manifest_listbox_content = tk.StringVar()
            self.manifest_listbox = tk.Listbox(self, width=32, height=32, listvariable=self.manifest_listbox_content,
                                               selectmode="single", exportselection=False)
            self.manifest_listbox.grid(column=0, row=1, padx=4, sticky="ns")
            self.manifest_listbox_scroll = tk.Scrollbar(self, command=self.manifest_listbox.yview)
            self.manifest_listbox_scroll.grid(column=1, row=1, sticky="ns", padx=(0, 12))
            self.manifest_listbox['yscrollcommand'] = self.manifest_listbox_scroll.set
            self.manifest_listbox.bind("<<ListboxSelect>>", self.manifest_listbox_callback)

            self.content_label = tk.Label(self, text="Contents:")
            self.content_label.grid(column=2, row=0, sticky="w", padx=8)

            self.article_output = tk.Text(self, state='disabled')
            self.article_output.grid(column=2, row=1, sticky="nsew", padx=(0, 4))
            self.article_output_scroll = tk.Scrollbar(self, command=self.article_output.yview)
            self.article_output_scroll.grid(column=3, row=1, sticky="ns", padx=(0, 8))
            self.article_output['yscrollcommand'] = self.article_output_scroll.set

            self.article_output.tag_config("selection", background="orange", underline=1)
            self.article_output.tag_config("match", background="yellow", underline=0)

            # noinspection PyTypeChecker
            self.selected_manifest = None
            self.selected_sscc = None

        def text_frame_update(self, text):
            self["text"] = "Results: (" + str(text) + ")"

        def manifest_listbox_callback(self, *args):
            if len(self.manifest_listbox.curselection()) > 0:
                self.selected_manifest = backend.get_manifest_from_id(
                    str(self.manifest_listbox.get(self.manifest_listbox.curselection())))
                self.text_field_update()

        def text_field_update(self):
            field_string = "Manifest: " + self.selected_manifest.manifest_id + ", Imported: " + self.selected_manifest.import_date + "\n\n"
            for sscc in self.selected_manifest.ssccs:
                field_string += "   " + sscc.sscc + ":\n"
                count = 0
                for article in sscc.articles:
                    count += 1
                    field_string += "       " + article.code.ljust(11) + ": [" + article.qty.ljust(2) + "]"
                    if count == 3:
                        field_string += "\n"
                        count = 0
                if count != 0:
                    field_string += "\n"
                field_string += "\n"

            self.article_output['state'] = 'normal'
            self.article_output.delete('1.0', tk.END)
            self.article_output.insert(tk.INSERT, field_string)

            self.parent.match_list_pos = 0
            self.parent.match_list = []

            term = str.upper(self.parent.settings_frame.search_query_entry.get())
            pos_start = self.article_output.search(term, "1.0", tk.END)
            self.article_output.see(pos_start)
            while pos_start:
                pos_end = pos_start + ('+%dc' % len(term))
                self.parent.match_list.append([pos_start, pos_end])
                self.article_output.tag_add("match", pos_start, pos_end)
                pos_start = self.article_output.search(term, pos_end, tk.END)

            self.parent.match_list_pos = 0
            if len(self.parent.match_list) > 0:
                self.article_output.tag_remove("match", self.parent.match_list[self.parent.match_list_pos][0],
                                               self.parent.match_list[self.parent.match_list_pos][1])
                self.article_output.tag_add("selection", self.parent.match_list[self.parent.match_list_pos][0],
                                            self.parent.match_list[self.parent.match_list_pos][1])
            self.article_output['state'] = 'disabled'

            self.parent.settings_frame.pos_label["text"] = "[" + str(self.parent.match_list_pos + 1) + "/" + str(
                len(self.parent.match_list)) + "]"

    def search(self, *args):
        term = str.upper(self.settings_frame.search_query_entry.get())
        if len(term) > 0:
            self.results_frame.manifest_listbox_content.set([])
            self.results_frame.article_output['state'] = 'normal'
            self.results_frame.article_output.delete('1.0', tk.END)
            self.results_frame.article_output['state'] = 'disabled'

            matching_manifests = []
            self.results_frame.text_frame_update("Searching...")
            self.update()
            search_time = time.time()

            # BEGIN SEARCH
            for manifest in backend.manifests:
                if term in manifest.manifest_id:
                    matching_manifests.append(manifest)
                else:
                    for sscc in manifest.ssccs:
                        if term in sscc.sscc and manifest not in matching_manifests:
                            matching_manifests.append(manifest)
                        else:
                            for article in sscc.articles:
                                if term in article.code and manifest not in matching_manifests:
                                    matching_manifests.append(manifest)

            self.results_frame.manifest_listbox_content.set(matching_manifests)
            if len(matching_manifests) > 0:
                self.results_frame.manifest_listbox.selection_set(first=0)
                self.results_frame.manifest_listbox_callback()
            else:
                self.results_frame.article_output['state'] = 'normal'
                self.results_frame.article_output.delete('1.0', tk.END)
                self.results_frame.article_output['state'] = 'disabled'

            search_time = abs(search_time - time.time())
            self.results_frame.text_frame_update(
                str(len(matching_manifests)) + " found in " + str(round(search_time, 4)) + "s")

    def send_to_application(self, *args):
        self.app_parent.parent_XDT_app.select_manifest_in_listbox(self.results_frame.selected_manifest.manifest_id)
        self.app_parent.parent_XDT_app.interface_update()
        self.destroy()


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))
