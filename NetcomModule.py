import json
import socket
import threading

import pyqrcode
import tkinter as tk

import BackendModule as backend
import AppModule as app


class NetcomModule(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.parent = parent

        self.title("Mobile Sync")
        app.set_centre_geometry(self, 300, 500)
        app.root.grab_release()
        self.grab_set()
        self.focus()
        self.resizable(False, False)
        self.wm_protocol("WM_DELETE_WINDOW", lambda: self.stop_comm_thread())

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.bind('<Escape>', lambda e: self.destroy())

        tk.Label(self, text="Enter scanner IP:").grid(column=0, row=0)

        self.ip_entry = tk.Entry(self)
        self.ip_entry.grid(column=0, row=1)

        dialog_close_button = tk.Button(self, text="Sync", command=self.begin_sync)
        dialog_close_button.grid(column=0, row=2)


    def start_comm_server(self):
        json_out = {}
        manifest_out = []
        for manifest in backend.manifests:
            manifest_out.append(manifest.export())
            json_out["Manifests"] = manifest_out

        data_out = str.encode(json.dumps(json_out) + "\n")

        self.s.connect((host, port))
        if running:
            # DATA OUT
            print("Connection to: " + str("10.203.1.223"))
            self.s.send(str(len(data_out)).encode() + "\n".encode())
            self.s.sendall(data_out)
            print("sent: " + str(len(data_out)) + " bytes")

            # DATA IN
            data_in = ""
            while running:
                recv = self.s.recv(256)
                if not recv:
                    break
                data_in += bytes.decode(recv)
            print("received: " + str(len(data_in)) + " bytes")

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
        global host
        host = self.ip_entry.get()
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
