"""Refresh the CHI contribution highlight from the publication list."""
from pathlib import Path
import re
from lxml import html
from publication_info import info

ROOT = Path(__file__).resolve().parents[1]


def render(source):
    doc = html.fromstring(source)
    conferences = doc.xpath('//li[@class="pub" and @data-cat="international-conference"]')
    chi = [p for p in conferences if 'Extended Abstracts of the CHI Conference' in
           p.xpath('string(.//*[@class="venue"])')]
    percent = round(100 * len(chi) / len(conferences)) if conferences else 0
    description = ('%d of %d international conference contributions. CHI Extended Abstracts: '
                   'Poster, Late Breaking Work, Student Research Competition, and Workshops.'
                   % (len(chi), len(conferences)))
    pattern = (r'(<div class="pubhi_item">(?:(?!<div class="pubhi_item").)*?'
               r'<span class="pubhi_num">)[^<]*(</span></div><p class="pubhi_lab">)'
               r'(?:Top Conference Papers|CHI Conference Contributions|CHI Contributions)'
               r'(?:<span class="metric-info">.*?)?</p><p class="pubhi_sub">.*?</p>')
    result, count = re.subn(pattern, lambda m: m[1] + str(percent) + '%' + m[2] +
                          'CHI Contributions' + info('CHI contributions', 'chi', description) +
                          '</p><p class="pubhi_sub">%d of %d international conference contributions.</p>'
                          % (len(chi), len(conferences)), source, flags=re.S)
    if count != 1:
        raise ValueError('Expected exactly one CHI highlight')
    return result


if __name__ == '__main__':
    path = ROOT / 'publications/index.html'
    path.write_bytes(render(path.read_bytes().decode('utf-8')).encode('utf-8'))
