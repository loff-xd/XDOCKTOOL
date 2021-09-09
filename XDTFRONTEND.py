"""XDTFRONTEND.py: The pants-wearing part of XDOCKTOOL which tells backend what to do"""

__author__ = "Lachlan Angus"
__copyright__ = "Copyright 2021, Lachlan Angus"

from tkinter import *
from tkinter import ttk, filedialog
import sys as system

import XDTBACKEND as backend

selected_manifest = ""
backend.json_load()
user_settings = backend.user_settings


# noinspection PyBroadException
def open_mhtml():
    try:
        mhtml_location = filedialog.askopenfilename(filetypes=[("SAP Manifest", ".MHTML")])
        imported_manifest_id = backend.mhtml_importer(mhtml_location)
        interface_update()

        combo_select_manifest.set(imported_manifest_id)
        interface_update()
    except:
        pass


def generate_pdf():
    manifest = backend.get_manifest_from_id(selected_manifest)
    save_location = filedialog.asksaveasfilename(filetypes=[("PDF Document", ".pdf")],
                                                 initialfile=str(manifest.manifest_id + ".pdf"))
    if len(save_location) > 0:
        backend.generate_pdf(manifest, save_location)


def interface_update(*event):
    global selected_manifest
    selected_manifest = combo_select_manifest.get()
    combo_select_manifest["values"] = sorted(backend.manifests)

    user_settings["show_all_articles"] = bool(var_show_all_articles.get())
    user_settings["open_on_save"] = bool(var_open_on_save.get())
    backend.user_settings = user_settings

    if len(selected_manifest) > 0:
        text_preview['state'] = 'normal'
        text_preview.delete(1.0, END)
        text_preview.insert(INSERT, backend.format_preview(selected_manifest))
        text_preview['state'] = 'disabled'

        preview_text.configure(text="Manifest " + selected_manifest + " preview:")


def HR_manager():
    if len(selected_manifest) > 0:

        manifest = backend.get_manifest_from_id(selected_manifest)

        hr_manager_window = Toplevel(root)
        hr_manager_window.wait_visibility()
        hr_manager_window.grab_set()
        hr_manager_window.title("Select HR entries")
        hr_manager_window.geometry("300x600")
        hr_manager_window.rowconfigure(0, weight=1)
        hr_manager_window.columnconfigure(0, weight=1)

        dialog_frame = ttk.Frame(hr_manager_window)
        dialog_frame.grid(sticky=(N, S, E, W))
        dialog_frame.rowconfigure(0, weight=1)
        dialog_frame.columnconfigure(0, weight=1)

        # Populate list
        def last_four(string):
            return str(string)[-4:]

        hr_sscc_list = []
        for sscc in manifest.ssccs:
            hr_sscc_list.append(sscc.sscc[:-4] + " " + last_four(sscc.sscc))

        hr_listbox_content = StringVar()
        hr_sscc_list = sorted(list(dict.fromkeys(hr_sscc_list)), key=last_four)
        hr_listbox = Listbox(dialog_frame, height=36, width=30, listvariable=hr_listbox_content, selectmode="multiple")
        hr_listbox.grid(column=0, row=0)
        hr_listbox.configure(justify=RIGHT)
        hr_listbox_content.set(hr_sscc_list)

        listbox_scroll = Scrollbar(dialog_frame, command=hr_listbox.yview)
        listbox_scroll.grid(column=1, row=0, sticky=(N, S))
        hr_listbox['yscrollcommand'] = listbox_scroll.set

        # Select lines already marked as HR
        # TODO this.
        for sscc in manifest.ssccs:
            if sscc.is_HR:
                # thing
                pass

        # Close HR manager and save changes to array
        def save_hr():
            for config_sscc in manifest.ssccs:
                config_sscc.is_HR = False
                # TODO can add article checks here

            # Get selection
            listbox_selected = []
            for index in hr_listbox.curselection():
                listbox_selected.append(str(hr_listbox.get(index)).replace(" ", ""))

            # Apply HR tags
            for selection in listbox_selected:
                for config_sscc in manifest.ssccs:
                    if config_sscc.sscc == selection:
                        config_sscc.is_HR = True

            backend.manifests.remove(backend.get_manifest_from_id(selected_manifest))
            backend.manifests.append(manifest)
            backend.json_save()
            interface_update()
            hr_manager_window.grab_release()
            hr_manager_window.destroy()

        dialog_close_button = Button(dialog_frame, text="Finished", command=save_hr)
        dialog_close_button.grid(column=0, row=1)


def exit_app():
    backend.json_save()
    root.destroy()
    system.exit()


# Root Window
root = Tk()
root.title("X-Dock Manager")
root.iconbitmap("XDMGR.ico")
w = 1024
h = 768
ws = root.winfo_screenwidth()
hs = root.winfo_screenheight()
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)
root.geometry('%dx%d+%d+%d' % (w, h, x, y))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.wm_protocol("WM_DELETE_WINDOW", lambda: exit_app())

# Main widget container
main_container = ttk.Frame(root)
main_container.grid(column=0, row=0, sticky=(N, S, E, W))
main_container.columnconfigure(0, weight=1)
main_container.rowconfigure(2, weight=1)

# Control Panel frame
control_panel = ttk.Frame(main_container)
control_panel.grid(column=0, row=0, sticky=(N, W, E, S))

combo_select_manifest = ttk.Combobox(control_panel, )
combo_select_manifest.grid(column=0, row=0)
combo_select_manifest["values"] = sorted(backend.manifests)
combo_select_manifest.bind("<<ComboboxSelected>>", interface_update)
combo_select_manifest.grid_configure(padx=10, pady=5)

button_open = Button(control_panel, text="Import MHTML", command=open_mhtml)
button_open.grid(column=1, row=0)

button_set_hr = Button(control_panel, text="HR Config", command=HR_manager)
button_set_hr.grid(column=2, row=0)

button_export_pdf = Button(control_panel, text="Save PDF", command=generate_pdf)
button_export_pdf.grid(column=3, row=0)

var_show_all_articles = IntVar()
check_show_all_articles = Checkbutton(control_panel, text="Show all articles", variable=var_show_all_articles,
                                      command=interface_update)
check_show_all_articles.grid(column=10, row=0)
check_show_all_articles.deselect()

var_open_on_save = IntVar()
check_open_on_save = Checkbutton(control_panel, text="Open on save", variable=var_open_on_save,
                                 command=interface_update)
check_open_on_save.grid(column=11, row=0)
check_open_on_save.select()

# Preview title
preview_text = Label(main_container, text="Manifest preview:")
preview_text.grid(column=0, row=1)

# Manifest Preview
preview_frame = ttk.Frame(main_container)
preview_frame.grid(column=0, row=2, sticky=(N, W, E, S))
preview_frame.columnconfigure(0, weight=1)
preview_frame.rowconfigure(0, weight=1)

text_preview = Text(preview_frame)
text_preview.grid(column=0, row=0, sticky=(N, W, E, S))
text_preview.insert(INSERT, "No manifest loaded.")
text_preview['state'] = 'disabled'

preview_scroll = Scrollbar(preview_frame, command=text_preview.yview)
preview_scroll.grid(column=1, row=0, sticky=(N, S))
text_preview['yscrollcommand'] = preview_scroll.set

for child in main_container.winfo_children():
    child.grid_configure(padx=5, pady=5)


root.mainloop()
