import re
from bs4 import BeautifulSoup

HIDDEN_RE = re.compile(r"display\s*:\s*none", re.I)


def prepare(html: str):
    soup = BeautifulSoup(html, 'xml')
    for t in soup.find_all(['script', 'style', 'title', 'img', 'nonscript']):
        t.decompose()

    for t in soup.find_all(style=HIDDEN_RE):
        if not getattr(t, 'decomposed', False):
            t.decompose()

    for t in soup.find_all(lambda x: ":" in x.name):
        t.unwrap
    pass


    




def parse_filing(html: str):
    soup = prepare(html)

    pass


if __name__ == "__main__":
    secs = parse_filing(open('filing.html', encoding="utf-8").read())
