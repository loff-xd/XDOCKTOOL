"""XDTBACKEND.py: The workhorse of XDOCKTOOL which is incapable of doing things by itself."""

__author__ = "Lachlan Angus"
__copyright__ = "Copyright 2021, Lachlan Angus"

import datetime
import email
import json
import os
import platform
import subprocess

from bs4 import BeautifulSoup
from fpdf import FPDF
from tabulate import tabulate

manifests = []
xdt_userdata_file = "xdt_userdata.json"

# USER SETTING DEFAULTS
user_settings = {
    "show_all_articles": False,
    "open_on_save": True,
    "hr_articles": []
}


class Manifest:
    def __init__(self, manifest_id):
        self.manifest_id = manifest_id
        self.ssccs = []

    def __repr__(self):
        return self.manifest_id

    def export(self):
        sscc_list = []
        for sscc in self.ssccs:
            sscc_list.append(sscc.export())
        return {"Manifest ID": self.manifest_id, "SSCCs": sscc_list}

    def __eq__(self, other):
        return int(self.manifest_id) == int(other.manifest_id)

    def __lt__(self, other):
        return int(self.manifest_id) < int(other.manifest_id)


class SSCC:
    def __init__(self, sscc):
        self.sscc = sscc
        self.articles = []
        self.short_sscc = sscc[-4:]
        self.is_HR = False

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
        return {"SSCC": self.sscc, "is_HR": self.is_HR, "Articles": article_list}

    def hr_repr(self):
        if self.is_HR:
            return ":BOX"
        else:
            for article in self.articles:
                if article.is_HR:
                    return ":ART"
            return "    "

    def article_repr(self):
        if len(self.articles) > 1:
            return "Multiple"
        else:
            return self.articles[0].code

    def desc_repr(self):
        if user_settings["show_all_articles"]:
            if len(self.articles) > 1:
                string = ""
                for article in self.articles:
                    string += article.code + "\n"
                return string
            else:
                return self.articles[0].desc
        else:
            if len(self.articles) > 1:
                return "Lines contained in SSCC:"
            else:
                return self.articles[0].desc

    def qty_repr(self):
        if user_settings["show_all_articles"]:
            if len(self.articles) > 1:
                string = ""
                for article in self.articles:
                    string += article.qty + "\n"
                return string
            else:
                return self.articles[0].qty
        else:
            if len(self.articles) > 1:
                return len(self.articles)
            else:
                return self.articles[0].qty


class Article:
    def __init__(self, code, desc, gtin, qty, is_HR):
        self.code = code
        self.desc = desc
        self.gtin = gtin
        self.qty = qty
        self.is_HR = is_HR

    def __repr__(self):
        return self.code

    def export(self):
        return {"Code": self.code, "Desc": self.desc, "GTIN": self.gtin, "QTY": self.qty, "is_HR": self.is_HR}

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


# noinspection PyBroadException
def mhtml_importer(file_path):
    # Import mhtml
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

    if new_manifest not in manifests:
        manifests.append(new_manifest)
    return new_manifest.manifest_id


def json_load():
    # Load the JSON
    global manifests
    manifests.clear()
    if not os.path.isfile(xdt_userdata_file):
        with open(xdt_userdata_file, "a+") as file:
            json.dump([], file)
    with open(xdt_userdata_file, "r") as file:
        xdt_userdata = json.load(file)

    # Convert JSON back into manifest array
    for entry in xdt_userdata:
        try:
            new_manifest = Manifest(entry["Manifest ID"])
            for sscc in entry["SSCCs"]:
                new_sscc = SSCC(sscc["SSCC"])
                new_sscc.is_HR = sscc["is_HR"]
                for article in sscc["Articles"]:
                    new_sscc.articles.append(Article(article["Code"], article["Desc"], article["GTIN"], article["QTY"], article["is_HR"]))
                new_manifest.ssccs.append(new_sscc)
            manifests.append(new_manifest)
        except KeyError:
            global user_settings
            user_settings = entry["userdata"]


def json_save():
    # Save manifests array to JSON
    json_out = []
    for manifest in manifests:
        json_out.append(manifest.export())
    json_out.append({"userdata": user_settings})
    os.rename(xdt_userdata_file, (xdt_userdata_file + ".bak"))
    with open(xdt_userdata_file, "a+") as file:
        json.dump(json_out, file, indent=4)
    os.remove(xdt_userdata_file + ".bak")


def generate_pdf(manifest, pdf_location):
    # Create file and header
    pdf_file = FPDF("P", "mm", "A4")
    pdf_file.add_page()
    pdf_file.set_font('Courier', '', 14)
    pdf_file.set_title(manifest.manifest_id)
    title_text = "Manifest: " + manifest.manifest_id + " - Printed on: " + str(datetime.date.today())
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
    if user_settings["open_on_save"]:
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', pdf_location))
        elif platform.system() == 'Windows':  # Windows
            os.startfile(pdf_location)
        else:  # linux variants
            subprocess.call('xdg-open', pdf_location)


def format_preview(selected_manifest):
    manifest = get_manifest_from_id(selected_manifest)
    tb_content = [["Article", "Description".ljust(30), "Qty", "SSCC", "HR?", "Short", "C"]]
    for sscc in sorted(manifest.ssccs):
        tb_content.append(
            [sscc.article_repr(), sscc.desc_repr(), sscc.qty_repr(), sscc.sscc, sscc.hr_repr(), sscc.short_sscc,
             "[  ]"])
    return tabulate(tb_content, headers="firstrow", tablefmt="fancy_grid")


def get_manifest_from_id(manifest_id):
    for manifest in manifests:
        if manifest.manifest_id == manifest_id:
            return manifest
    return "000000"
