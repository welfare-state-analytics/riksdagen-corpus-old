from lxml import etree
from riksdagen_corpus.segmentation import detect_mp, expression_dicts, detect_introduction
import re
import datetime

def _iter(root):
    for body in root.findall(".//{http://www.tei-c.org/ns/1.0}body"):
        for div in body.findall("{http://www.tei-c.org/ns/1.0}div"):
            for ix, elem in enumerate(div):
                if elem.tag == "{http://www.tei-c.org/ns/1.0}u":
                    yield "u", elem
                elif elem.tag == "{http://www.tei-c.org/ns/1.0}note":
                    yield "note", elem
                else:
                    yield None

def detect_mps(root, mp_db):
    """
    Re-detect MPs in a parla clarin protocol, based on the (updated)
    MP database.
    """
    current_speaker = None

    for tag, elem in _iter(root):
        if tag == "u":
            if current_speaker is not None:
                elem.attrib["who"] = current_speaker
            else:
                elem.attrib["who"] = "unknown"
        elif tag == "note":
            if elem.attrib.get("type", None) == "speaker":
                current_speaker = detect_mp(elem.text, mp_db)
                print(elem.text, "SPEAKER", current_speaker)

    return etree.fromstring(etree.tostring(root))

def find_introductions(root, pattern_db, names_ids):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """

    #return root
    root.text = None
    current_speaker = None
    expressions, manual = expression_dicts(pattern_db)

    for ix, elem_tuple in enumerate(list(_iter(root))):
        tag, elem = elem_tuple
        if tag == "u":
            u = None
            u_parent = elem.getparent()
            u_parent.text = None
            for seg in list(elem):
                introduction = detect_introduction(seg.text, expressions, names_ids)
                if introduction is not None:
                    print("NEW", seg.text)
                    seg.tag = "{http://www.tei-c.org/ns/1.0}note"
                    seg.attrib["type"] = "speaker"
                    if u is not None:
                        u.addnext(seg)
                    else:
                        elem.addnext(seg)

                    u = etree.Element("{http://www.tei-c.org/ns/1.0}u")
                    #u.text = None
                    if introduction["who"] is not None:
                        u.attrib["who"] = introduction["who"]
                    else:
                        u.attrib["who"] = "unknown"

                    seg.addnext(u)
                    if seg.text[-1] != ":":
                        ix = seg.text.index(":")
                        rest = seg.text[ix+1:]
                        seg.text = seg.text[:ix+1]
                        new_seg = etree.SubElement(u, "{http://www.tei-c.org/ns/1.0}seg")
                        new_seg.text = rest

                    
                elif u is not None:
                    u.append(seg)
                    u.text = None

        elif tag == "note":
            parent = elem.getparent()
            parent.text = None
            #if not elem.attrib.get("type", None) == "speaker":
            introduction = detect_introduction(elem.text, expressions, names_ids)
                
            if introduction is not None:
                if not elem.attrib.get("type", None) == "speaker":
                    print("NEW note", elem.text)
                else:
                    print("OLD", elem.text)

    return root

def format_paragraph(paragraph, spaces = 12):
    words = paragraph.strip().split()
    s = "\n" + " " * spaces
    row = ""

    for word in words:
        if len(row) > 50:
            s += row.strip() + "\n" + " " * spaces
            row = ""
        else:
            row += " " + word

    s += row.strip() + "\n" + " " * (spaces - 2)
    if s.strip() == "":
        return None
    return s

def format_texts(root):
    for tag, elem in _iter(root):

        if type(elem.text) == str:
            elem.text = format_paragraph(elem.text)
        elif tag == "u":
            for seg in elem:
                if type(seg.text) == str:
                    seg.text = format_paragraph(seg.text, spaces=14)
                else:
                    seg.text = None
            elem.text = None

    return root

def detect_date(root, protocol_year):
    month_numbers = dict(
        januari=1,
        februari=2,
        mars=3,
        april=4,
        maj=5,
        juni=6,
        juli=7,
        augusti=8,
        september=9,
        oktober=10,
        november=11,
        december=12,
        )

    dates = set()
    expression = "\\w{3,5}dagen den (\\d{1,2})\\.? (\\w{3,9}) (\\d{4})"
    expression2 = "\\w{3,5}dagen den (\\d{1,2})\\.? (\\w{3,9})"
    for ix, elem_tuple in enumerate(list(_iter(root))):
        tag, elem = elem_tuple
        if tag == "note" and type(elem.text) == str and len(elem.text) < 50:
            matches = re.search(expression, elem.text)
            matches2 = re.search(expression2, elem.text)
            if matches is not None:
                day = int(matches.group(1).replace(".", ""))
                month = matches.group(2).lower()
                month = month_numbers.get(month)
                year = int(matches.group(3))

                if month is None and year > 1800:
                    print("Could not parse:", matches.group(0))
                else:
                    elem.attrib["type"] = "date"
                    date = None
                    try:
                        date = datetime.datetime(year, month, day)
                        dates.add(date)
                    except ValueError:
                        print("Whoopsie!")
            elif matches2 is not None:
                day = int(matches2.group(1).replace(".", ""))
                month = matches2.group(2).lower()
                month = month_numbers.get(month)

                if month is None:
                    print("Could not parse:", matches2.group(0))
                else:
                    date = None
                    elem.attrib["type"] = "date"
                    try:
                        date = datetime.datetime(protocol_year, month, day)
                        dates.add(date)
                    except ValueError:
                        print("Whoopsie!")

    dates = sorted(list(dates))
    for text in root.findall(".//{http://www.tei-c.org/ns/1.0}text"):
        for front in text.findall("{http://www.tei-c.org/ns/1.0}front"):
            if len(dates) > 0:
                for docDate in front.findall("{http://www.tei-c.org/ns/1.0}docDate"):
                    docDate.getparent().remove(docDate)

                for div in front.findall("{http://www.tei-c.org/ns/1.0}div"):
                    if div.attrib.get("type") == "preface":
                        for docDate in div.findall("{http://www.tei-c.org/ns/1.0}docDate"):
                            docDate.getparent().remove(docDate)
                        for date in dates:
                            formatted = date.strftime("%Y-%m-%d")
                            docDate = etree.SubElement(div, "docDate")
                            docDate.text = formatted
                            docDate.attrib["when"] = formatted


    return root, dates

