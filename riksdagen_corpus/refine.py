from lxml import etree
from riksdagen_corpus.segmentation import detect_mp, expression_dicts, detect_introduction

def _iter(root):
    for body in root.findall(".//{http://www.tei-c.org/ns/1.0}body"):
        for div in body.findall("{http://www.tei-c.org/ns/1.0}div"):
            for ix, elem in enumerate(div):
                if elem.tag == "{http://www.tei-c.org/ns/1.0}u":
                    yield "u", elem
                elif elem.tag == "{http://www.tei-c.org/ns/1.0}note":
                    yield "note", elem

def detect_mps(root, mp_db):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
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

    return root

def find_introductions(root, pattern_db, names_ids):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """

    #return root

    current_speaker = None
    expressions, manual = expression_dicts(pattern_db)

    for ix, elem_tuple in enumerate(list(_iter(root))):
        tag, elem = elem_tuple
        if tag == "u":
            u = None
            u_parent = elem.getparent()
            for seg in list(elem):
                introduction = detect_introduction(seg.text, expressions, names_ids)
                if introduction is not None:
                    print("NEW", seg.text)
                    seg.tag = "{http://www.tei-c.org/ns/1.0}note"
                    seg.attrib["type"] = "speaker"

                    u_parent.insert(ix + 1, seg)
                    u = etree.Element("{http://www.tei-c.org/ns/1.0}u")
                    u.attrib["who"] = introduction["who"]
                    u_parent.insert(ix + 2, u)
                elif u is not None:
                    u.append(seg)

        elif tag == "note":
            #if not elem.attrib.get("type", None) == "speaker":
            introduction = detect_introduction(elem.text, expressions, names_ids)
                
            if introduction is not None:
                if not elem.attrib.get("type", None) == "speaker":
                    print("NEW", elem.text)
                    elem.tag = "{http://www.tei-c.org/ns/1.0}note"
                else:
                    print("OLD", elem.text)

    return root