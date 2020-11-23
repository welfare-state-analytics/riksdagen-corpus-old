import xml.etree.ElementTree as et
import sys
import re

def clean_html(raw_html):
    raw_html = raw_html.replace("\n", " NEWLINE ")
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace(" NEWLINE ", "\n")
    return cleantext


xml_path = sys.argv[1]
xml = open(xml_path).read()
s = clean_html(xml)

print(s)

from bs4 import BeautifulSoup

f = open(xml_path)
soup = BeautifulSoup(f)
f.close()
g = open('a.xml', 'w')
g.write(soup.prettify())
g.close()