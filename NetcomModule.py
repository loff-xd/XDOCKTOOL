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

        self.qr = pyqrcode.create(host + ";" + str(port))
        self.qrimg = tk.BitmapImage(data=self.qr.xbm(scale=6))

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

        tk.Label(self, text="Scan QR code with mobile app to sync:").grid(column=0, row=0)

        self.qrimage = tk.Canvas(self, width=200, height=200)
        self.qrimage.grid(column=0, row=1)
        self.qrimage.create_image(0, 0, image=self.qrimg, anchor="nw")

        global running
        running = True
        comm_thread = threading.Thread(target=self.start_comm_server)
        comm_thread.start()

    def start_comm_server(self):
        json_out = {}
        manifest_out = []
        for manifest in backend.manifests:
            manifest_out.append(manifest.export())
            json_out["Manifests"] = manifest_out

        data_out = str.encode(json.dumps(json_out) + "\n")

        s.listen(1)
        conn, address = s.accept()
        if running:
            # DATA OUT
            print("Connection from: " + str(address))
            conn.send(str(len(data_out)).encode() + "\n".encode())
            conn.sendall(data_out)
            print("sent: " + str(len(data_out)) + " bytes")

            # DATA IN
            data_in = ""
            while running:
                recv = conn.recv(256)
                if not recv:
                    break
                data_in += bytes.decode(recv)
            print("received: " + str(len(data_in)) + " bytes")

        conn.close()
        print("Transaction completed")
        self.destroy()

    def stop_comm_thread(self):
        print("netcom stopped")
        global running
        running = False
        stop_s = socket.socket()
        stop_s.connect((host, port))
        stop_s.close()
        self.destroy()

    def client(self):
        data = ""
        while True:
            recv = s.recv(8192)
            if not recv:
                break
            data += bytes.decode(recv)

        print("Got: " + str(len(data)) + " chars")
        s.close()


def get_local_wireless_ip_windows():
    import subprocess
    arp = subprocess.check_output('arp -a')
    local_ipv4 = []
    for line in arp.split('\n'.encode()):
        if 'Interface'.encode() in line:
            local_ipv4.append(line.split(':'.encode())[1].split('---'.encode())[0].strip())
    return local_ipv4[-1]


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = get_local_wireless_ip_windows().decode()
port = 7700
running = True
s.bind(("", port))
