import json
import socket
import threading

import tkinter as tk
from tkinter import messagebox

import BackendModule as backend
import AppModule as app


class NetcomModule(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.parent = parent

        self.title("Mobile Sync")
        app.set_centre_geometry(self, 300, 150)
        app.root.grab_release()
        self.grab_set()
        self.focus()
        self.resizable(False, False)
        self.wm_protocol("WM_DELETE_WINDOW", lambda: self.stop_comm_thread())

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.bind('<Escape>', lambda e: self.destroy())

        self.statuslabel = tk.Label(self, text="Enter Scanner IP:")
        self.statuslabel.grid(column=0, row=0, pady=16)

        self.ip_entry = tk.Entry(self)
        self.ip_entry.grid(column=0, row=1)
        self.ip_entry["text"] = backend.user_settings.get("last_ip")

        self.sync_button = tk.Button(self, text="Sync", command=self.begin_sync)
        self.sync_button.grid(column=0, row=2, pady=16)

    def start_comm_server(self):
        json_out = {}
        manifest_out = []
        for manifest in backend.manifests:
            manifest_out.append(manifest.export())
            json_out["Manifests"] = manifest_out

        data_out = str.encode(json.dumps(json_out) + "\n")
        timestamp_out = "0"
        for manifest in backend.manifests:
            if int(manifest.last_modified) > int(timestamp_out):
                timestamp_out = manifest.last_modified

        try:
            self.s.settimeout(5)
            self.s.connect((host, port))
        except OSError as e:
            tk.messagebox.showerror("Connection Failed", "Connection to scanner was unsuccessful")

        if running:
            # DATA OUT
            print("Connection to: " + host)
            self.s.sendall((str(timestamp_out) + "\n").encode())
            self.s.sendall(data_out)
            print("sent: " + str(len(data_out)) + " bytes")

            # DATA IN
            timestamp_in = "0"

            # DATA IN
            data_in = ""
            while running:
                recv = self.s.recv(256)
                if not recv:
                    break
                data_in += bytes.decode(recv)
            print("received: " + str(len(data_in)) + " bytes")

            data_in = data_in.split('\n')
            print(data_in)

            timestamp_in = data_in[0]

            print(str(timestamp_in) + " > " + str(timestamp_out))

            if int(timestamp_in) > int(timestamp_out):
                print("Doing update")
                backend.json_load(str(data_in[1]))
            else:
                print("Up to date")

        self.s.close()
        print("Transaction completed")
        self.destroy()

    def stop_comm_thread(self):
        print("netcom stopped")
        global running
        running = False
        self.s.close()
        self.destroy()

    def begin_sync(self, *args):
        self.statuslabel["text"] = "Please wait..."
        self.sync_button["state"] = "disabled"
        global host
        host = self.ip_entry.get()
        self.ip_entry["state"] = "disabled"
        backend.user_settings["last_ip"] = host
        backend.json_save()
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


host = ""
port = 7700
running = True
