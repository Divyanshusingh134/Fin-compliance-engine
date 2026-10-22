import re
from bs4 import BeautifulSoup
from dataclasses import dataclass, field

HIDDEN_RE = re.compile(r"display\s*:\s*none", re.I)
PART_RE = re.compile(r"^part\s+([ivx])+\b", re.I)
ITEM_RE = re.compile(r"^item\s+(\d{1,2}[a-c]?)\b", re.I)


@dataclass
class Block:

    kind: str # heading , para, pagebreak, table, anchor
    text: str = ""
    level: int = 0 # for headings
    rows: list = field(default_factory=list)  # for tables


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


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


def read_toc(soup: BeautifulSoup) -> list:
    toc, part, seen = [], None, set()
    for a in soup.find_all('a', href=True):
        href = a.get('href')
        if href is None or (isinstance(href, str) and not href.startswith("#")):
            continue  
        target = href[1:]
        txt = norm(a.get_text(""))

        if m:=PART_RE.match(txt):
            part = m.group(0).upper()
            toc.append((part, None, target))
        elif (m:= ITEM_RE.match(txt)) and target not in seen:
            item = m.group(0).upper()
            toc.append((part, item, target))
        seen.add(target)

    return toc 


class Walker:
    def __init__(self, targets: dict) -> None:
        self.t = targets
        self.buf = []
        self.out = []
        pass

    def walk(self):
        pass



def parse_filing(html: str):
    soup = prepare(html)
    toc = read_toc(soup)
    targets = {t: (p, i) for p, i, t in toc}
    w = Walker(targets=targets)
    w.walk()
    pass


if __name__ == "__main__":
    secs = parse_filing(open('filing.html', encoding="utf-8").read())
