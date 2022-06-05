"""BackendModule.py: The workhorse of XDOCKTOOL which is incapable of doing things by itself."""

__author__ = "Lachlan Angus"
__copyright__ = "Copyright 2021, Lachlan Angus"

import datetime
import email
import json
import os
import threading
import time
import sys
import tkinter.messagebox
from tkinter import messagebox
import traceback

import xlsxwriter as xlsxwriter
from bs4 import BeautifulSoup
from fpdf import FPDF
from tabulate import tabulate

import PanikModule as panik

# CONFIG
manifests = []
article_lookup_db = []
selected_manifest = ""
xdt_userdata_file = "xdt_userdata.json"
xdt_mobile_scanner_filename = "xdt_mobile.json"
APP_DIR = os.getcwd()
io_thread = None
io_lock = False

try:
    if not os.path.isfile(os.path.join(APP_DIR, "bin\\XDOCK_MANAGER\\application.version")):
        VERSION = os.path.join(APP_DIR, "application.version")
        SEARCHICON = os.path.join(APP_DIR, "search.png")
    else:
        VERSION = os.path.join(APP_DIR, "bin\\XDOCK_MANAGER\\application.version")
        SEARCHICON = os.path.join(APP_DIR, "bin\\XDOCK_MANAGER\\search.png")

    with open(VERSION) as version_file:
        application_version = version_file.read()
except Exception as ex:
    panik.log(ex)
    application_version = "Unknown Version"
print(application_version)

try:
    if not os.path.isfile(xdt_userdata_file):
        os.close(os.open(xdt_userdata_file, os.O_CREAT))
        with open(xdt_userdata_file, "a+") as newfile:
            json.dump({}, newfile)
except Exception as ex:
    messagebox.showerror("Error launching application", "Controlled folder access is known to cause this\n" +
                         str(traceback.format_exception(sys.exc_info(), value=ex, tb=ex.__traceback__)))
    sys.exit()

# USER SETTING DEFAULTS
user_settings = {
    "hr_disp_mode": "Expand None",
    "open_on_save": True,
    "hr_articles": [],
    "DIL folder": "",
    "last_ip": "",
    "retention_policy": "0"
}

x_mgr_ascii = "@@(//@@@@@@@@@@@@@@@@@@(/////////////////(@@@@@@@@@@@@@@@@@&///@@@@@@(///%@@@@@%/////(@@@@@@@@@(////#@@@@@@@@@@@&/////#@\n\
@@@@///@@@@@@@@@@@@@@@@@#///////////////&@@@@@@@@@@@@@@@@@#////@@@@@@@///@@@@@@%///#@@@@@&&&@@@@@(//#@@@@&&&&@@@@@////#@\n\
@@@@@#//&@@@@@@@@@@@@@@@@@////////////(@@@@@@@@@@@@@@@@@%//////@@@@%@@%/@@@(@@@%//%@@@@(////////////#@@@@@@@@@@@@%////#@\n\
@@@@@@@(//@@@@@@@@@@@@@@@@@&/////////%@@@@@@@@@@@@@@@@@////////@@@@/@@@(@@@/@@@%//%@@@@(//&@@@@@@%//#@@@@@@@@@@#//////#@\n\
@@@@@@@@&//%@@@@@@@@@@@@@@@@@///////@@@@@@@@@@@@@@@@@(/////////@@@@//@@@@%//@@@%///@@@@@&///@@@@@%//#@@@@#//@@@@@/////#@\n\
@@@@@@@@@@#//&@@@@@@@@@@@@@@@@@///%@@@@@@@@@@@@@@@@@///////////@@@@///@@@///@@@%/////@@@@@@@@@@@////#@@@@#///@@@@@#///#@\n\
@@@@@@@@@@@@//#@@@@@@@@@@@@@@@@@(@@@@@@@@@@@@@@@@@///////////////////////////////////////////////////////////////////(@@\n\
@@@@@@@@@@@@@%//%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&//////////////////////////////////////////////////////////////////%@@@@\n\
@@@@@@@@@@@@@@@%/(@@@@@@@@@@@@@@@@@@@@@@@@@@@@@/////////////////////////////////////////////////////////////////(@@@@@@@\n\
@@@@@@@@@@@@@@@@@//(@@@@@@@@@@@@@@@@@@@@@@@@@%////////////////////////////////////////////////////////////////&@@@@@@@@@\n\
@@@@@@@@@@@@@@@@@@///@@@@@@@@@@@@@@@@@@@@@@@////////////////////////////////////////////////////////////////@@@@@@@@@@@@\n\
@@@@@@@@@@@@@@@@@&//@@@@@@@@@@@@@@@@@@@@@@@@&////////////////////////////////////////////////////////////&@@@@@@@@@@@@@@\n\
@@@@@@@@@@@@@@@@//(@@@@@@@@@@@@@@@@@@@@@@@@@@@////////////////////////////////////////////////////////(@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@@@@@@%/(@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@////////////////////////////////////////////////////%@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@@@@%//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%///////////////////////////////////////////////(@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@@@//#@@@@@@@@@@@@@@@@@&(@@@@@@@@@@@@@@@@@@(///////////////////////////////////////////&@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@@@#/(@@@@@@@@@@@@@@@@@@(///&@@@@@@@@@@@@@@@@@@///////////////////////////////////////(@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@@#//&@@@@@@@@@@@@@@@@@%//////(@@@@@@@@@@@@@@@@@@(///////////////////////////////////&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@@@//#@@@@@@@@@@@@@@@@@&//////////%@@@@@@@@@@@@@@@@@@////////////////////////////////@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@@#//&@@@@@@@@@@@@@@@@@#////////////(@@@@@@@@@@@@@@@@@@#///////////////////////////%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@@@//%@@@@@@@@@@@@@@@@@#////////////////%@@@@@@@@@@@@@@@@@@#//////////////////////(@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\
@(//@@@@@@@@@@@@@@@@@@///////////////////(@@@@@@@@@@@@@@@@@@@///////////////////&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"


class Manifest:
    def __init__(self, manifest_id):
        self.manifest_id = manifest_id
        self.ssccs = []
        self.import_date = ""
        self.last_modified = ""

    def __repr__(self):
        return self.manifest_id

    def export(self):
        sscc_list = []
        for sscc in self.ssccs:
            sscc_list.append(sscc.export())
        return {"Manifest ID": self.manifest_id, "Import Date": self.import_date, "Last Modified": self.last_modified,
                "SSCCs": sscc_list}

    def __eq__(self, other):
        return int(self.manifest_id) == int(other.manifest_id)

    def __lt__(self, other):
        return int(self.manifest_id) > int(other.manifest_id)

    def get_sscc(self, sscc_id):
        for sscc in self.ssccs:
            if sscc.sscc == sscc_id:
                return sscc
        return None


class SSCC:
    def __init__(self, sscc):
        self.sscc = sscc
        self.articles = []
        self.short_sscc = sscc[-4:]
        self.is_HR = False
        self.dil_status = ""
        self.dil_comment = ""
        self.isUnknown = False
        self.isScanned = False
        self.scannedManifest = ""

    def __eq__(self, other):
        return self.short_sscc == other.short_sscc

    def __lt__(self, other):
        return self.short_sscc < other.short_sscc

    def __repr__(self):
        return str(self.sscc)

    def export(self):
        article_list = []
        for article in self.articles:
            article_list.append(article.export())
        return {"SSCC": self.sscc, "is_HR": self.is_HR, "DIL Status": self.dil_status, "DIL Comment": self.dil_comment,
                "Articles": article_list, "Scanned": self.isScanned, "Unknown": self.isUnknown,
                "ScannedInManifest": self.scannedManifest}

    def hr_repr(self):
        if self.is_HR:
            return ":BOX"
        else:
            for article in self.articles:
                if article.is_HR:
                    return ":ART"
            return "    "

    def article_repr(self):
        if not self.isUnknown:
            if len(self.articles) > 1:
                return "Multiple"
            else:
                return self.articles[0].code
        else:
            return "[UNKNOWN]"

    def desc_repr(self):
        if user_settings["hr_disp_mode"] == "Expand All":
            if len(self.articles) > 1:
                string = ""
                for article in self.articles:
                    string += article.code + "\n"
                return string
            else:
                return self.articles[0].desc
        else:
            if len(self.articles) > 1:
                if user_settings["hr_disp_mode"] == "Expand HR" and self.is_HR:
                    string = ""
                    for article in self.articles:
                        string += article.code + "\n"
                    return string
                else:
                    return "Lines contained in SSCC:"
            else:
                return self.articles[0].desc

    def qty_repr(self):
        if user_settings["hr_disp_mode"] == "Expand All":
            if len(self.articles) > 1:
                string = ""
                for article in self.articles:
                    string += article.qty + "\n"
                return string
            else:
                return self.articles[0].qty
        else:
            if len(self.articles) > 1:
                if user_settings["hr_disp_mode"] == "Expand HR" and self.is_HR:
                    string = ""
                    for article in self.articles:
                        string += article.qty + "\n"
                    return string
                else:
                    return len(self.articles)
            else:
                return self.articles[0].qty

    def get_article(self, article_code):
        for article in self.articles:
            if article.code == article_code:
                return article
        return None

    def check_dil(self):
        if self.dil_status != "":
            return True
        for article in self.articles:
            if article.dil_status != "":
                return True
        return False


class Article:
    def __init__(self, code, desc, gtin, qty, is_HR):
        self.code = code
        self.desc = desc
        self.gtin = gtin
        self.qty = str(qty)
        self.is_HR = is_HR
        self.dil_status = ""
        self.dil_qty = 0
        self.dil_comment = ""

    def __repr__(self):
        return self.code

    def export(self):
        return {"Code": self.code, "Desc": self.desc, "GTIN": self.gtin, "QTY": self.qty, "is_HR": self.is_HR,
                "DIL Status": self.dil_status, "DIL Qty": self.dil_qty, "DIL Comment": self.dil_comment}

    def do_HR_check(self):
        if self.code in user_settings["hr_articles"]:
            self.is_HR = True


# noinspection PyBroadException
def junk_check(var):
    try:
        if len(var[1][0]) > 4:
            int(var[1][0])
            return True
    except Exception:
        return False


# MHTML SUPPORT
def mhtml_importer(file_path):
    with open(file_path, 'r') as source:
        content = email.message_from_file(source)
        for unit in content.walk():
            if unit.get_content_type() == "text/html":
                raw_file = BeautifulSoup(unit.get_payload(decode=False), 'html.parser')

    # Populate variables
    new_manifest = Manifest("000000")
    for row in raw_file.findAll('tr'):
        new_entry = []
        for element in row.findAll('td'):
            new_entry.append(element.contents)

        if junk_check(new_entry):  # This is the gatekeeper of junk entries
            # manifest[0], sscc[1], count[2], article[3], desc[4], handling_unit_uom[5], gtin[6], qty[7] -> Order
            # of information
            entry_placed = False
            new_article = Article(new_entry[3][0], new_entry[4][0], new_entry[6][0], new_entry[7][0], False)

            # Check if sscc already exists, add if not
            for exist_sscc in new_manifest.ssccs:
                if exist_sscc.sscc == new_entry[1][0]:
                    exist_sscc.articles.append(new_article)
                    entry_placed = True

            # if sscc exists, add article to it
            if not entry_placed:
                new_sscc = SSCC(new_entry[1][0])
                new_sscc.articles.append(new_article)
                new_manifest.ssccs.append(new_sscc)

            if new_manifest.manifest_id == "000000":
                new_manifest.manifest_id = new_entry[0][0]

    for sscc in new_manifest.ssccs:
        for article in sscc.articles:
            article.do_HR_check()

    if "000000" in new_manifest.manifest_id:
        return "000000"

    if new_manifest.manifest_id in [manifest.manifest_id for manifest in manifests]:
        result = tkinter.messagebox.askyesnocancel("Duplicate manifest",
                                                   "Manifest " + new_manifest.manifest_id + " already exits, would you like to replace it?")
        if result:
            manifests.remove(get_manifest_from_id(new_manifest.manifest_id))
            new_manifest.import_date = str(datetime.date.today())
            new_manifest.last_modified = str(current_milli_time())
            manifests.append(new_manifest)
            json_threaded_save()
        else:
            pass
    else:
        new_manifest.import_date = str(datetime.date.today())
        new_manifest.last_modified = str(current_milli_time())
        manifests.append(new_manifest)
        json_threaded_save()

    return new_manifest.manifest_id


# HTM SUPPORT
def htm_importer(file_path):

    with open(file_path, 'r') as source:
        raw_file = BeautifulSoup(source, 'html.parser')

    new_manifest = Manifest("000000")
    for row in raw_file.findAll('tr'):
        new_entry = []
        for element in row.findAll('td'):
            element_text = element.text
            new_entry.append([element_text.strip()])

        if junk_check(new_entry):  # This is the gatekeeper of junk entries
            # manifest[0], sscc[1], count[2], article[3], desc[4], handling_unit_uom[5], gtin[6], qty[7] -> Order
            # of information
            entry_placed = False
            # DESC NEEDS TRAILING SPACES REMOVED
            new_article = Article(new_entry[3][0].replace(u'\xa0', ''), new_entry[4][0].replace(u'\xa0', ' '), new_entry[6][0].replace(u'\xa0', ''), new_entry[7][0].replace(u'\xa0', ''), False)

            # Check if sscc already exists, add if not
            for exist_sscc in new_manifest.ssccs:
                if exist_sscc.sscc == new_entry[1][0].replace(u'\xa0', ''):
                    exist_sscc.articles.append(new_article)
                    entry_placed = True

            # if sscc exists, add article to it
            if not entry_placed:
                new_sscc = SSCC(new_entry[1][0].replace(u'\xa0', ''))
                new_sscc.articles.append(new_article)
                new_manifest.ssccs.append(new_sscc)

            if new_manifest.manifest_id == "000000":
                new_manifest.manifest_id = new_entry[0][0].replace(u'\xa0', '')

    if "000000" in new_manifest.manifest_id:
        return "000000"

    if new_manifest.manifest_id in [manifest.manifest_id for manifest in manifests]:
        result = tkinter.messagebox.askyesnocancel("Duplicate manifest",
                                                   "Manifest " + new_manifest.manifest_id + " already exits, would you like to replace it?")
        if result:
            manifests.remove(get_manifest_from_id(new_manifest.manifest_id))
            new_manifest.import_date = str(datetime.date.today())
            new_manifest.last_modified = str(current_milli_time())
            manifests.append(new_manifest)
            json_threaded_save()
        else:
            pass
    else:
        new_manifest.import_date = str(datetime.date.today())
        new_manifest.last_modified = str(current_milli_time())
        manifests.append(new_manifest)
        json_threaded_save()

    return new_manifest.manifest_id


def json_load(*from_string):
    # Load the JSON
    global manifests, io_lock
    manifests.clear()

    if len(from_string) == 0:
        with open(xdt_userdata_file, "r") as file:
            xdt_userdata = json.load(file)
    else:
        xdt_userdata = json.loads(from_string[0])

    # Convert JSON back into manifest array
    if xdt_userdata.get("Manifests") is not None:
        try:
            for entry in xdt_userdata.get("Manifests"):
                new_manifest = Manifest(entry.get("Manifest ID", "000000"))
                new_manifest.import_date = entry.get("Import Date", str(datetime.date.today()))
                new_manifest.last_modified = entry.get("Last Modified", str(current_milli_time()))
                for sscc in entry.get("SSCCs", []):
                    new_sscc = SSCC(sscc["SSCC"])
                    new_sscc.is_HR = sscc["is_HR"]
                    new_sscc.dil_status = sscc.get("DIL Status", "")
                    new_sscc.dil_comment = sscc.get("DIL Comment", "")
                    new_sscc.isScanned = sscc.get("Scanned", False)
                    new_sscc.isUnknown = sscc.get("Unknown", False)
                    new_sscc.scannedManifest = sscc.get("ScannedInManifest", new_manifest.manifest_id)
                    for article in sscc.get("Articles", []):
                        new_article = Article(article["Code"], article["Desc"], article["GTIN"], article["QTY"],
                                              article["is_HR"])
                        new_article.dil_status = article.get("DIL Status", "")
                        new_article.dil_qty = article.get("DIL Qty", 0)
                        new_article.dil_comment = article.get("DIL Comment", "")
                        new_sscc.articles.append(new_article)
                    new_manifest.ssccs.append(new_sscc)
                manifests.append(new_manifest)

            global user_settings
            user_settings.update(xdt_userdata.get("userdata", user_settings))

            io_lock = False

        except Exception as e:
            panik.log(e)
            io_lock = False


def json_threaded_save():
    global io_thread
    io_thread = threading.Thread(target=json_save)
    io_thread.start()


def json_save():
    # Save manifests array to JSON
    json_out = {}
    manifest_out = []
    for manifest in manifests:
        manifest_out.append(manifest.export())
        json_out["Manifests"] = manifest_out
    json_out["userdata"] = user_settings
    os.rename(xdt_userdata_file, (xdt_userdata_file + ".bak"))
    with open(xdt_userdata_file, "a+") as file:
        json.dump(json_out, file, indent=4)
    os.remove(xdt_userdata_file + ".bak")


def generate_pdf(manifest, pdf_location):
    try:
        # Create file and header
        pdf_file = FPDF("P", "mm", "A4")
        pdf_file.add_page()
        pdf_file.set_font('Courier', '', 14)
        pdf_file.set_title(manifest.manifest_id)
        title_text = "Manifest: " + manifest.manifest_id + " - Processed on: " + manifest.import_date
        pdf_file.cell(w=200, h=12, txt=title_text, ln=1, align="L")

        # Make the table for the PDF
        pdf_file.set_font('Courier', '', 9)
        pdf_file.set_fill_color(220)
        tb_content = [["Article", "Description".ljust(30), "Qty", "SSCC", "HR?", "Short", "C"]]

        for sscc in sorted(manifest.ssccs):
            tb_content.append([sscc.article_repr(), sscc.desc_repr(), sscc.qty_repr(), sscc.sscc, sscc.hr_repr(),
                               sscc.short_sscc, "[    ]"])

        cell_text = (tabulate(tb_content, headers="firstrow", tablefmt="simple")).split("\n")

        # Darken for HR items
        for row in cell_text:
            if ":BOX" in row or ":ART" in row:
                pdf_file.cell(w=0, h=5, txt=row, ln=1, align="L", fill=True, border=1)
            else:
                pdf_file.cell(w=0, h=5, txt=row, ln=1, align="L", border=1)

        # Actually save the pdf
        pdf_file.output(pdf_location, 'F')

        # Open the pdf if user has requested
        if user_settings['open_on_save']:
            open_saved_file(pdf_location)

    except Exception as e:
        panik.log(e)


class OpenFailedException(Exception):
    def __init__(self, message="Failed to open the saved file"):
        self.message = message
        super().__init__(self.message)


# noinspection PyBroadException
def open_saved_file(file_loc):
    if os.path.isfile(file_loc):
        try:
            os.startfile(file_loc)
        except:
            panik.log(OpenFailedException)
            messagebox.showerror("Error opening file", "Unable to auto-open the saved file. Network drives are known to cause this.")


def generate_DIL(manifest_id):
    manifest = get_manifest_from_id(manifest_id)
    update_manifest_timestamp(manifest_id)

    filepath = os.path.join(user_settings.get("DIL folder"), str(manifest_id))
    if not os.path.isdir(filepath):
        os.mkdir(filepath)

    for sscc in manifest.ssccs:
        if sscc.dil_status != "":

            filename = os.path.join(filepath, str(sscc.sscc) + ".xlsx")

            # MAKE FILE
            excel_file = xlsxwriter.Workbook(filename)
            dil_sheet = excel_file.add_worksheet()

            datarow = 4
            datacol = 0

            dil_sheet.set_column(datacol, datacol, 12)
            dil_sheet.set_column(datacol + 2, datacol + 2, 30)
            dil_sheet.set_column(datacol + 1, datacol + 1, 8)

            dil_sheet.merge_range(0, 0, 0, 2, sscc.sscc)
            dil_sheet.merge_range(1, 0, 1, 2, "Issue: " + sscc.dil_status)
            dil_sheet.merge_range(2, 0, 2, 2, "Comments: " + sscc.dil_comment)

            dil_sheet.write(3, datacol, "Article:")
            dil_sheet.write(3, datacol + 2, "Description:")
            dil_sheet.write(3, datacol + 1, "Qty:")

            for article in sscc.articles:
                dil_sheet.write(datarow, datacol, article.code)
                dil_sheet.write(datarow, datacol + 2, article.desc)
                dil_sheet.write(datarow, datacol + 1, str(article.qty))
                datarow += 1

            # Actually save the file
            excel_file.close()


def format_preview(s_manifest):
    manifest = get_manifest_from_id(s_manifest)
    tb_content = [["Article", "Description".ljust(30), "Qty", "SSCC", "HR?", "Short", "C"]]
    for sscc in sorted(manifest.ssccs):
        if sscc.isScanned:
            tb_content.append(
                [sscc.article_repr(), sscc.desc_repr(), sscc.qty_repr(), sscc.sscc, sscc.hr_repr(), sscc.short_sscc,
                 "[██]"])
        else:
            tb_content.append(
                [sscc.article_repr(), sscc.desc_repr(), sscc.qty_repr(), sscc.sscc, sscc.hr_repr(), sscc.short_sscc,
                 "[  ]"])
    return tabulate(tb_content, headers="firstrow", tablefmt="fancy_grid")


def get_manifest_from_id(manifest_id):
    for manifest in manifests:
        if manifest.manifest_id == manifest_id:
            return manifest
    return "000000"


def update_manifest_timestamp(manifest_id):
    for manifest in manifests:
        if manifest.manifest_id == manifest_id:
            manifest.last_modified = str(current_milli_time())


def article_db_refresh():
    global article_lookup_db
    article_lookup_db = []
    for manifest in manifests:
        for sscc in manifest.ssccs:
            for article in sscc.articles:
                for existing_article in article_lookup_db:
                    if existing_article.gtin == article.gtin:
                        article_lookup_db.remove(existing_article)
                article_lookup_db.append(article)


def check_lost_ssccs():
    lost_ssccs = []
    found_ssccs = ""

    for manifest in manifests:
        for sscc in manifest.ssccs:
            # ADD TO LOST LIST
            if sscc.isUnknown:
                lost_ssccs.append(sscc)

    for lost_sscc in lost_ssccs:
        for manifest in manifests:
            for sscc in manifest.ssccs:
                if (lost_sscc.sscc == sscc.sscc) and (lost_sscc.scannedManifest != manifest.manifest_id):
                    lost_ssccs.remove(lost_sscc)
                    sscc.isScanned = True
                    sscc.isUnknown = False
                    found_ssccs += "SSCC: " + sscc.sscc + " found in: " + sscc.scannedManifest + " instead of: " + manifest.manifest_id + "\n"

    return found_ssccs


def last_four(string):
    return str(string)[-4:]


def current_milli_time():
    return round(time.time() * 1000)
