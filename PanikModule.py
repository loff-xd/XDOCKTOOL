import os
import sys
import tkinter.messagebox
import traceback
from datetime import datetime
from tkinter import filedialog

APP_DIR = os.getcwd()

if not os.path.isfile(os.path.join(APP_DIR, "bin\\XDOCK_MANAGER\\error.log")):
    errorFile = os.path.join(APP_DIR, "error.log")
else:
    errorFile = os.path.join(APP_DIR, "bin\\XDOCK_MANAGER\\error.log")

try:
    if not os.path.isfile(errorFile):
        os.close(os.open(errorFile, os.O_CREAT))
except Exception as ex:
    tkinter.messagebox.showerror("Error launching application", "Controlled folder access is known to cause this\n" + str(traceback.format_exception(sys.exc_info(), value=ex, tb=ex.__traceback__)))
    sys.exit()


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
        content = ""
        with open(errorFile, "r") as logfile:
            content = logfile.read()

        save_location = filedialog.asksaveasfilename(filetypes=[("Error Report", ".log")],
                                                     initialfile=str("XDMErrors" + ".log"))

        if len(save_location) > 0:
            with open(save_location, "w") as report_file:
                report_file.write(content)

            tkinter.messagebox.showinfo("Report saved", "The error report has been saved. Please send it to the developer")
    except Exception as e:
        log(e)
        tkinter.messagebox.showerror("Couldn't send report", "Something went wrong, how inconvenient!\nPlease contact "
                                                             "the developer for more information")
