import json
import socket
import threading

import tkinter as tk
from tkinter import messagebox

import BackendModule as backend

host = ""
port = 7700
running = True
sync_version = "v2"


class NetcomModule(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, **kwargs)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.title("Mobile Sync (BETA)")
        set_centre_geometry(self, 300, 150)
        self.grab_set()
        self.focus()
        self.resizable(False, False)
        self.wm_protocol("WM_DELETE_WINDOW", lambda: self.stop_comm_thread())
        self.iconbitmap("XDMGR.ico")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.bind('<Escape>', lambda e: self.destroy())

        self.status_label = tk.Label(self, text="Sending Manifest: " + backend.selected_manifest + "\n\nEnter Scanner IP:")
        self.status_label.grid(column=0, row=0, pady=(16, 0))

        self.ip_entry = tk.Entry(self)
        self.ip_entry.grid(column=0, row=1)
        self.ip_entry.insert(0, backend.user_settings.get("last_ip"))

        self.sync_button = tk.Button(self, text="Sync", command=self.begin_sync)
        self.sync_button.grid(column=0, row=2, pady=16)

    def start_comm_server(self):
        json_out = {"Manifests": [backend.get_manifest_from_id(backend.selected_manifest).export()]}
        data_out = str.encode(json.dumps(json_out) + "\n")

        try:
            self.s.settimeout(5)
            self.s.connect((host, port))

            if running:
                # DATA OUT
                print("Connection to: " + host)
                self.status_label["text"] = "Syncing data [=--]"

                self.s.sendall((str(sync_version) + "\n").encode())

                self.s.sendall(data_out)
                print("sent: " + str(len(data_out)) + " bytes")
                self.status_label["text"] = "Syncing data [==-]"

                # DATA IN
                data_in = ""
                while running:
                    recv = self.s.recv(256)
                    if not recv:
                        break
                    data_in += bytes.decode(recv)
                print("received: " + str(len(data_in)) + " bytes")
                self.status_label["text"] = "Syncing data [===]"

                data_in = data_in.split('\n')

                self.status_label["text"] = "Transaction Finished."

                for data in data_in:
                    if "Manifests" in data:
                        sync_manifest = "000000"
                        manifest_in = json.loads(data)

                        for entry in manifest_in.get("Manifests"):
                            sync_manifest = backend.Manifest(entry.get("Manifest ID", "000000"))
                            for target_sscc in entry.get("SSCCs", []):
                                sync_sscc = backend.SSCC(target_sscc["SSCC"])
                                sync_sscc.isScanned = target_sscc.get("Scanned", False)
                                sync_manifest.ssccs.append(sync_sscc)

                            target_manifest = backend.get_manifest_from_id(sync_manifest.manifest_id)
                            for target_sscc in target_manifest.ssccs:
                                sync_sscc = sync_manifest.get_sscc(target_sscc.sscc)
                                target_sscc.isScanned = sync_sscc.isScanned

                self.stop_comm_thread()

        except OSError as e:
            tk.messagebox.showerror("Connection Failed", "Connection to scanner was unsuccessful.")
            self.s.close()
            self.destroy()

    def stop_comm_thread(self):
        print("netcom stopped")
        global running
        running = False
        self.s.close()
        self.destroy()

    def begin_sync(self, *args):
        self.status_label["text"] = "Saving current state..."
        self.sync_button["state"] = "disabled"
        global host
        host = self.ip_entry.get()
        self.ip_entry["state"] = "disabled"
        backend.user_settings["last_ip"] = host
        backend.json_save()
        self.status_label["text"] = "Starting sync [---]"
        global running
        running = True
        comm_thread = threading.Thread(target=self.start_comm_server)
        comm_thread.start()


def get_local_wireless_ip_windows():
    import subprocess
    arp = subprocess.check_output('arp -a')
    local_ipv4 = []
    for line in arp.split('\n'.encode()):
        if 'Interface'.encode() in line:
            local_ipv4.append(line.split(':'.encode())[1].split('---'.encode())[0].strip())
    return local_ipv4[-1]


def set_centre_geometry(target, w, h):
    ws = target.winfo_screenwidth()
    hs = target.winfo_screenheight()
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    target.geometry('%dx%d+%d+%d' % (w, h, x, y))
