"""Build the Korean Research Areas page from the English layout and translations."""
import hashlib
import json
import re
from pathlib import Path
from lxml import html, etree

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://hai.seoultech.ac.kr/'

def find(panel, selector):
    path = '.'
    for part in selector.split():
        nth = re.search(r':(?:nth-child\((\d+)\)|last-child)', part)
        part = re.sub(r':(?:nth-child\(\d+\)|last-child)', '', part)
        if part.startswith('.'):
            path += '//*[contains(concat(" ",normalize-space(@class)," ")," %s ")]' % part[1:]
        elif part.startswith('#'):
            path += '//*[@id="%s"]' % part[1:]
        else:
            path += '//' + part
        if nth:
            path += '[' + (nth.group(1) or 'last()') + ']'
    nodes = panel.xpath(path)
    if len(nodes) != 1:
        raise ValueError('Expected one translation target: ' + selector)
    return nodes[0]

def build():
    path = ROOT / 'about/index.html'
    source = path.read_text(encoding='utf-8')
    source = source.replace('<html lang="ko">', '<html lang="en">', 1)
    if 'hreflang="x-default"' not in source:
        links = '\n'.join('<link rel="alternate" hreflang="%s" href="%sabout/%s">' % (lang, SITE, name)
                          for lang, name in [('en', 'index.html'), ('ko', 'index.ko.html'), ('x-default', 'index.html')])
        source = source.replace('<meta property="og:type"', links + '\n<meta property="og:type"', 1)
    if 'join-language.css' not in source:
        digest = hashlib.sha256((ROOT / 'assets/css/join-language.css').read_bytes()).hexdigest()[:8]
        source = source.replace('<link rel="icon" href=', '<link rel="stylesheet" href="../assets/css/join-language.css?v=%s">\n<link rel="icon" href=' % digest, 1)
    if 'class="join_language"' not in source:
        source = source.replace('<h2 class="tit">Research Areas</h2>', '<div class="join_title_group"><h2 class="tit">Research Areas</h2><nav class="join_language" aria-label="Page language"><a href="index.html" lang="en" hreflang="en" aria-current="page" aria-label="English">EN</a><a href="index.ko.html" lang="ko" hreflang="ko" aria-label="한국어">KO</a></nav></div>', 1)
    start = source.index('<main class="content"')
    end = source.index('</main>', start) + len('</main>')
    panel = html.fromstring(source[start:end])
    translations = json.loads((ROOT / 'tools/research_ko.json').read_text(encoding='utf-8'))
    # Research field names, all twelve topic tags and publication metadata stay English.
    for n in range(1, 4):
        prefix = '#area-' + str(n)
        translations += [(prefix + ' .area_c .sel_head b', '대표 프로젝트'),
                         (prefix + ' .area_c .sel_head a', '전체 프로젝트 보기 →'),
                         (prefix + ' .area_r .sel_head b', '대표 논문'),
                         (prefix + ' .area_r .sel_head a', '전체 논문 보기 →')]
        for j in range(1, 3):
            selector = prefix + ' .sp:nth-child(%d) .sp_badges .hm_badge:nth-child(1)' % j
            status = find(panel, selector).text_content().strip()
            translations.append((selector, {'Ongoing': '진행 중', 'Completed': '종료'}[status]))
    translations += [('#partners .hm_kicker', '협력기관'), ('#partners h3', '다양한 분야의 파트너와 함께합니다'),
                     ('#partners .hm_sub', '의료·교육·산업·공공기관 및 해외 학계의 전문가들과 협력합니다.')]
    for selector, text in translations:
        el = find(panel, selector)
        for child in list(el):
            el.remove(child)
        fragment = html.fragment_fromstring(text, create_parent='div')
        el.text = fragment.text
        for child in list(fragment):
            el.append(child)
    nav = panel.xpath('.//nav[@class="join_language"]')[0]
    nav.set('aria-label', '페이지 언어')
    for a in nav:
        a.attrib.pop('aria-current', None)
        if a.get('lang') == 'ko':
            a.set('aria-current', 'page')
    panel.xpath('.//*[@id="LocationPath"]/li[last()]/a')[0].set('href', 'index.ko.html')
    korean = source[:start] + etree.tostring(panel, encoding='unicode', method='html') + source[end:]
    korean = korean.replace('<html lang="en">', '<html lang="ko">', 1)
    korean = korean.replace('Research Area | SeoulTech HAI Lab', '연구 분야 | 서울과학기술대학교 HAI Lab')
    for attr in ['rel="canonical" href', 'property="og:url" content']:
        korean = korean.replace(attr + '="' + SITE + 'about/index.html"', attr + '="' + SITE + 'about/index.ko.html"')
    description = '서울과학기술대학교 HAI Lab의 연구 분야를 소개합니다. Agentic AI, Physical AI, AI for Social Good를 중심으로 인간-AI 협력, 멀티모달 AI, 교육·헬스케어 연구와 대표 프로젝트·논문을 확인하세요.'
    korean = re.sub(r'(<meta (?:name="description"|property="og:description") content=")[^"]*', lambda m: m[1] + description, korean)
    # Update only the last breadcrumb; parent About keeps its original destination.
    def breadcrumb(match):
        data = json.loads(match[1])
        if data.get('@type') == 'BreadcrumbList':
            data['itemListElement'][-1].update(name='연구 분야', item=SITE + 'about/index.ko.html')
        return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + '\n</script>'
    korean = re.sub(r'<script type="application/ld\+json">(.*?)</script>', breadcrumb, korean, flags=re.S)
    path.write_text(source, encoding='utf-8')
    (ROOT / 'about/index.ko.html').write_text(korean, encoding='utf-8')

if __name__ == '__main__':
    build()
