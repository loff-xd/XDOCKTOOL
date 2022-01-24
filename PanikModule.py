import os
import sys
import tkinter.messagebox
import traceback
import smtplib
from datetime import datetime
from email.message import EmailMessage

APP_DIR = os.getcwd()

if not os.path.isfile(os.path.join(APP_DIR, "bin/XDOCK_MANAGER/error.log")):
    errorFile = os.path.join(APP_DIR, "error.log")
else:
    errorFile = os.path.join(APP_DIR, "bin/XDOCK_MANAGER/error.log")

if not os.path.isfile(errorFile):
    with open(errorFile, "w+"):
        pass


def log(exception):
    tb = traceback.format_exception(sys.exc_info(), value=exception, tb=exception.__traceback__)
    with open(errorFile, "a") as logfile:
        logfile.write(str(datetime.now()) + " {\n")
        logfile.writelines(tb)
        logfile.write("}\n")


# noinspection PyBroadException
def report(*args):
    print("Error report requested")
    try:
        msg = EmailMessage()
        msg['From'] = 'errorreporting@loff.duckdns.org'
        msg['To'] = 'lachixd+xdt@gmail.com'
        msg['Subject'] = 'Error Report' + str(datetime.now())

        with open(errorFile, "r") as logfile:
            msg.set_content(logfile.read())

        smtp_server = 'aspmx.l.google.com'
        server = smtplib.SMTP(smtp_server, 25)
        server.ehlo()
        server.starttls()
        server.send_message(msg)
        server.quit()

        with open(errorFile, "a") as logfile:
            logfile.write("\n==REPORT SENT==\n")

        tkinter.messagebox.showinfo("Report sent", "The error report has been sent to the developer")
    except Exception as e:
        log(e)
        tkinter.messagebox.showerror("Couldn't send report", "Something went wrong, how inconvenient!\nPlease contact "
                                                             "the developer for more information")
