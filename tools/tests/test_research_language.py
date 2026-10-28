from pathlib import Path
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[2]

class ResearchLanguageTests(unittest.TestCase):
    def test_language_links_and_canonical(self):
        for lang, filename in [('en', 'index.html'), ('ko', 'index.ko.html')]:
            doc = html.parse(str(ROOT / 'about' / filename))
            self.assertEqual(doc.getroot().get('lang'), lang)
            self.assertEqual(doc.xpath('//link[@rel="canonical"]/@href'),
                             ['https://hai.seoultech.ac.kr/about/' + filename])
            self.assertEqual(set(doc.xpath('//link[@rel="alternate"]/@hreflang')), {'en', 'ko', 'x-default'})
            self.assertEqual(doc.xpath('//nav[@class="join_language"]/a[@aria-current="page"]/@lang'), [lang])

    def test_english_terms_and_original_content_preserved(self):
        en, ko = [html.parse(str(ROOT / 'about' / p)) for p in ['index.html', 'index.ko.html']]
        for cls, count in [('area_tit', 3), ('area_tags', 3), ('spub_tit', 6), ('spub_au', 6)]:
            a = en.xpath('//*[@class="%s"]' % cls)
            b = ko.xpath('//*[@class="%s"]' % cls)
            self.assertEqual(len(a), count)
            self.assertEqual([x.text_content() for x in a], [x.text_content() for x in b])
        self.assertEqual(len(ko.xpath('//*[@class="area_tags"]/span')), 12)
        self.assertEqual(en.xpath('//main//img/@src'), ko.xpath('//main//img/@src'))
        self.assertEqual(len(ko.xpath('//*[@id="partners"]')), 1)
        self.assertIn('사람과 실제 환경', ko.xpath('//*[@class="ov_p"]')[0].text_content())
