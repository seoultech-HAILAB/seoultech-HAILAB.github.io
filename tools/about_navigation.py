"""About 메뉴의 기준과 정적 HTML 동기화. 브라우저의 JS 없이도 같은 메뉴를 쓴다."""
import html
from html.parser import HTMLParser
import posixpath
import re
from urllib.parse import urljoin


ABOUT_LINKS = (
    ("Research Area", "about/index.html"),
    ("Facility", "about/facility.html"),
    ("Patent", "about/patents.html"),
    ("Join Us", "about/join.html"),
)
NAV = re.compile(r'<nav\b[^>]*\bclass="lnb"[^>]*>.*?</nav>', re.S)
ABOUT = re.compile(r'(<a\b[^>]*>\s*About\s*</a>\s*<ul\b[^>]*>)(.*?)(</ul>)', re.S)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            self.current = ["", attrs.get("href", ""), "on" in attrs.get("class", "").split()]

    def handle_data(self, data):
        if self.current is not None:
            self.current[0] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.current[0] = " ".join(self.current[0].split())
            self.items.append(tuple(self.current))
            self.current = None


def active_page(rel):
    # 특허 목록의 2쪽부터도 Patent를 선택 상태로 둔다.
    if re.fullmatch(r"about/patents/\d+/index\.html", rel):
        return "about/patents.html"
    return rel


def menu_matches(menu, rel):
    links = Links()
    links.feed(menu)
    # 404는 없는 하위 주소에서도 표시되므로 루트 기준 링크여야 한다.
    if rel == "404.html" and any(not href.startswith("/") for _, href, _ in links.items):
        return False
    actual = [(label, urljoin("https://site.invalid/" + rel, href), selected)
              for label, href, selected in links.items]
    expected = [(label, "https://site.invalid/" + target, target == active_page(rel))
                for label, target in ABOUT_LINKS]
    return actual == expected


def navigation_errors(source, rel):
    navs = list(NAV.finditer(source))
    if len(navs) != 1:
        return ["main navigation must occur exactly once"]
    menus = list(ABOUT.finditer(navs[0].group()))
    if len(menus) != 1:
        return ["About submenu must occur exactly once"]
    if not menu_matches(menus[0].group(2), rel):
        return ["About labels, destinations, order or selected item differ from ABOUT_LINKS"]
    return []


def sync_about_nav(source, rel):
    if not navigation_errors(source, rel):
        return source
    navs = list(NAV.finditer(source))
    if len(navs) != 1:
        raise ValueError("%s: expected one main navigation" % rel)
    nav = navs[0]
    menus = list(ABOUT.finditer(nav.group()))
    if len(menus) != 1:
        raise ValueError("%s: expected one About submenu" % rel)
    menu = menus[0]
    items = []
    for label, target in ABOUT_LINKS:
        href = "/" + target if rel == "404.html" else posixpath.relpath(target, posixpath.dirname(rel) or ".")
        selected = ' class="on"' if target == active_page(rel) else ""
        items.append('<li><a href="%s"%s>%s</a></li>' % (html.escape(href, quote=True), selected, html.escape(label)))
    start, end = nav.start() + menu.start(2), nav.start() + menu.end(2)
    return source[:start] + "".join(items) + source[end:]
