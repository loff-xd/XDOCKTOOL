import traceback
import smtplib
from datetime import datetime
from email.message import EmailMessage

errorFile = "error.log"


def log(exception):
    tb = traceback.format_exception(etype=type(exception), value=exception, tb=exception.__traceback__)
    with open(errorFile, "a") as logfile:
        logfile.write(str(datetime.now()) + " {\n")
        logfile.writelines(tb)
        logfile.write("}\n")


def report(*args):
    msg = EmailMessage()
    msg['From'] = 'errorreporting@xdocktool.app'
    msg['To'] = 'lachixd+xdt@gmail.com'
    msg['Subject'] = 'Error report'

    with open(errorFile, "r") as logfile:
        msg.set_content(logfile.read())

    smtp_server = 'aspmx.l.google.com'
    server = smtplib.SMTP(smtp_server, 25)
    server.ehlo()
    server.starttls()
    server.send_message(msg)
    server.quit()
