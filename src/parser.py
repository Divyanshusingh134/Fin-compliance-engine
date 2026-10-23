import re
from bs4 import BeautifulSoup, Comment, Tag
from bs4.element import NavigableString
from functools import lru_cache
from dataclasses import dataclass, field

HIDDEN_RE = re.compile(r"display\s*:\s*none", re.I)
PART_RE = re.compile(r"^part\s+([ivx])+\b", re.I)
ITEM_RE = re.compile(r"^item\s+(\d{1,2}[a-c]?)\b", re.I)
W_RE = re.compile(r"font-weight\s*:\s*(\w+)")
S_RE = re.compile(r"font-style\s*:\s*(\w+)")
FOOTER_RE = re.compile(r"^(?:.{0,80}\|\s*\d{4}\s+Form\s+(?:10|8)-[KQ]\s*\|\s*\d+\s*|\d{1,4}\.?|table\s+of\s+contents)$", re.I)
BLOCK     = ["div", "p", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
             "section", "center", "blockquote"]


@dataclass
class Block:

    kind: str # heading , para, pagebreak, table, anchor
    text: str = ""
    level: int = 0 # for headings
    rows: list = field(default_factory=list)  # for table


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

# ---------------------------------------------------------------- 
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

# ---------------------------------------------------------------- 

@lru_cache(maxsize=None)
def parse_styling(style:str):
    bold = ital = None
    if m:= W_RE.match(style):
        v = m.group(1)
        bold = v in ('bold', 'bolder') or (v.isdigit() and int(v) >= 600)
    if m:= S_RE.match(style):
        ital = (m.group(1) == "italic")

    return bold, ital


def tag_flags(tag, parent_flags):
    bold, ital = parent_flags

    if tag.name in ('b', 'bold'):
        bold = True
    if tag.name in ('i', 'em'):
        ital = True

    b, i = parse_styling(tag.get('style', ""))

    if b is not None:
        bold = b
    if i is not None:
        ital = i

    return bold, ital


def collect_runs(node, inherited=(False, False)):
    runs = []

    for n in node.children:
        if isinstance(n, Comment):
            continue
        if isinstance(n, NavigableString):
            runs.append((str(n), *inherited))
        else:
            runs += collect_runs(n, tag_flags(n, *inherited))
    return runs

def classify(text, flags):
    pass

# ---------------------------------------------------------------- 
class Walker:
    def __init__(self, targets: dict) -> None:
        self.t = targets
        self.buf = []
        self.out = []

    def anchor(self, n, deep=True):
        for n in ([n] + n.find_all(True) if deep else [n]):
            v = n.get("id") or n.get("name")
            if v in self.t:
                self.out.append(Block("anchor", v))

        

    def flush(self):
        self.leaf(self.buf)
        self.buf = []
        pass

    def walk(self, parent):
        for ch in parent.children:
            if isinstance(ch, Comment): 
                continue
            if isinstance(ch, NavigableString):
                self.buf.append(ch)
                continue

            if ch.name == "hr":
                self.flush()
                self.out.append(Block("pagebreak"))
                continue

            if ch.name == 'table':
                self.flush()


            if ch in BLOCK:
                self.flush()
                if ch.find(BLOCK + ['table']):
                    pass
                pass
            else :
                self.buf.append(ch)

        pass

    def leaf(self, nodes):
        runs = []
        for node in nodes:
            if isinstance(node, Tag): 
                self.anchor(node)
                runs += collect_runs(node=node)
            else:
                runs.append(node)

        text = norm("".join(t for t, _, _ in runs))
        if not text or FOOTER_RE.match(text):
            return
        flags = [(b, i) for t, b, i in runs if t.strip() not in("®", "™", "℠", "©")]
        if lvl:= classify(text, flags):
            pass
        pass



def parse_filing(html: str):
    soup = prepare(html)
    toc = read_toc(soup)
    targets = {t: (p, i) for p, i, t in toc}
    w = Walker(targets=targets)
    w.walk(soup.body or soup)
    pass


if __name__ == "__main__":
    secs = parse_filing(open('filing.html', encoding="utf-8").read())
