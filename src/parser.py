import re
from bs4 import BeautifulSoup

HIDDEN_RE = re.compile(r"display\s*:\s*none", re.I)
PART_RE = re.compile(r"")




def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

# ------ clean the document
def prepare(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, 'xml')
    for t in soup.find_all(['script', 'style', 'title', 'img', 'nonscript']):
        t.decompose()

    for t in soup.find_all(style=HIDDEN_RE):
        if not getattr(t, 'decomposed', False):
            t.decompose()

    for t in soup.find_all(lambda x: ":" in x.name):
        t.unwrap

    for t in soup.find_all('br'):
        t.replace_with(' ')
    for t in soup.find_all(['div', 'tr', 'li', 'p', 'td', 'th']):
        t.append(" ")

    return soup


def read_toc(soup: BeautifulSoup):
    toc, part, seen = [], None, set()
    for a in soup.find_all('a', href=True):
        href = a.get('href')
        if href is None or (isinstance(href, str) and not href.startswith("#")):
            continue  
        target = href[1:]
        txt = norm(a.get_text(""))


        



    pass    




def parse_filing(html: str):
    soup = prepare(html)
    toc = read_toc(soup)

    pass


if __name__ == "__main__":
    secs = parse_filing(open('filing.html', encoding="utf-8").read())
