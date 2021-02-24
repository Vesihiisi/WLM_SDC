import argparse
import csv
import json
import re
import requests
import mwparserfromhell as mwparser
import pywikibot

COUNTRIES = {"se": "Sweden"}

MONUMENT_PROPERTIES = {"arbetslivsmuseum": "P3426",
                       "bbr": "P1260",
                       "fornminne": "P1260",
                       "k-fartyg": "P2317", }

WD_PROPERTIES = {"commonscat": "P373",
                 "depicts": "P180",
                 "participant": "P1344"}

WD_RESOLVER_URL = "https://hub.toolforge.org/{}:{}?format=json"

CACHE = {
    "arbetslivsmuseum": {},
    "fornminne": {},
    "bbr": {},
    "k-fartyg": {},
    "wlm_edition": {},
}

YEARLY = {"2011": "Q8168264",
          "2012": "Q13390164",
          "2013": "Q14568386",
          "2014": "Q15975254",
          "2015": "Q19833396",
          "2010": "Q20890568",
          "2016": "Q26792317",
          "2017": "Q30015204",
          "2018": "Q56165596",
          "2019": "Q56427997",
          "2020": "Q66975112", }


def read_data(filename):
    datalist = []
    with open(filename, 'r') as data:
        for line in data:
            datalist.append(line.strip())
    print("Loaded {} photo names.".format(len(datalist)))
    return datalist


def get_page_content(commons_name):
    site = pywikibot.Site("commons", "commons")
    return pywikibot.Page(site, commons_name).text


def get_wlm_edition(page_content):
    qid_local = None
    qid_yearly = None
    editions = []
    wikicode = mwparser.parse(page_content)
    templates = wikicode.filter_templates()
    for template in templates:
        if re.search(r'wiki loves monuments \d{4}$', template.name.lower()):
            if "=" in str(template.params[0]):
                country_abbr = str(template.params[0]).split("=")[-1].lower()
            else:
                country_abbr = str(template.params[0]).lower()
            edition = "{} in {}".format(
                template.name, COUNTRIES[country_abbr])
            year = template.name[-4:]
            qid_yearly = YEARLY.get(year)
            qid_local = CACHE["wlm_edition"].get(edition)
            if qid_local is None:
                resolve_url = WD_RESOLVER_URL.format(
                    WD_PROPERTIES["commonscat"], edition)
                r = requests.get(resolve_url).json()
                if r.get("origin"):
                    qid_local = r.get("origin").get("qid")
                    CACHE["wlm_edition"][edition] = qid_local
    editions.append(qid_local)
    editions.append(qid_yearly)
    return list(set(editions))


def resolve_monument(monument_template):
    qid = None
    monument_type = monument_template.name.lower()
    monument_property = MONUMENT_PROPERTIES[monument_type]
    if monument_type == "arbetslivsmuseum":
        monument_id = str(monument_template.params[0])
    elif monument_type == "fornminne":
        monument_id = "raa/fmi/" + str(monument_template.params[0])
    elif monument_type == "k-fartyg":
        monument_id = str(monument_template.params[0])
    elif monument_type == "bbr":
        for param in monument_template.params:
            param = str(param).strip()
            if "=" in param:
                param = param.split("=")[1].strip()
            if param.isdigit():
                monument_id = "raa/bbr/" + param
    qid = CACHE[monument_type].get(monument_id)
    if qid is None:
        resolve_url = WD_RESOLVER_URL.format(monument_property, monument_id)
        r = requests.get(resolve_url).json()
        if r.get("origin"):
            qid = r.get("origin").get("qid")
            CACHE[monument_type][monument_id] = qid
    return qid


def get_monuments(page_content):
    monument_templates = MONUMENT_PROPERTIES.keys()
    monuments = []
    wikicode = mwparser.parse(page_content)
    templates = wikicode.filter_templates()
    for template in templates:
        if template.name.lower() in monument_templates:
            monument_q = resolve_monument(template)
            if monument_q:
                monuments.append(monument_q)
    return list(set(monuments))


def make_csv(filename, photos):
    lines = []
    max_number_depicts = max(
        len(photo.get(WD_PROPERTIES["depicts"])) for photo in photos)
    max_number_participant = max(
        len(photo.get(WD_PROPERTIES["participant"])) for photo in photos)
    depicts_headers = [WD_PROPERTIES["depicts"]] * max_number_depicts
    participant_headers = [
        WD_PROPERTIES["participant"]] * max_number_participant
    header_line = ["Filename"]
    lines.append(header_line + participant_headers + depicts_headers)
    for photo in photos:
        line = [photo.get("Filename")]
        line.extend(photo.get(WD_PROPERTIES["participant"]))
        line.extend(photo.get(WD_PROPERTIES["depicts"]))
        lines.append(line)

    with open(filename, mode='w') as f:
        csv_writer = csv.writer(
            f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in lines:
            csv_writer.writerow(line)


def main(arguments):
    data = read_data(arguments.get("data"))
    output_file = "{}.csv".format(arguments.get("data").split(".")[0])
    processed_monuments = []
    for commons_name in data:
        page_content = get_page_content(commons_name)
        photo_object = {"Filename": commons_name[5:]}
        photo_object[WD_PROPERTIES["participant"]
                     ] = get_wlm_edition(page_content)
        photo_object[WD_PROPERTIES["depicts"]] = get_monuments(page_content)
        processed_monuments.append(photo_object)
        print("{}/{} -- {}".format(len(processed_monuments),
                                   len(data), commons_name[5:]))
    csv_data = make_csv(output_file, processed_monuments)
    print("Saved {} to {}.".format(len(processed_monuments), output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()
    main(vars(args))
