import json
import sys
import unittest
from pathlib import Path
from lxml import html

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from build_publication_highlights import render


class SiteMetadataTests(unittest.TestCase):
    def test_project_description_matches_cards(self):
        doc = html.parse(str(ROOT / 'research/index.html'))
        total = len(doc.xpath('//article[@class="proj"]'))
        ongoing = len(doc.xpath('//article[@class="proj" and @data-status="ongoing"]'))
        descriptions = doc.xpath('//meta[@name="description" or @property="og:description"]/@content')
        self.assertEqual(len(descriptions), 2)
        for text in descriptions:
            self.assertIn('%d건(진행 중 %d건)' % (total, ongoing), text)

    def test_chi_highlight_updates_when_list_changes(self):
        source = (ROOT / 'publications/index.html').read_text(encoding='utf-8')
        self.assertEqual(render(source), source)
        # A reclassified venue must change the numerator, not the denominator.
        modified = source.replace('Extended Abstracts of the CHI Conference: Poster', 'Other Conference', 1)
        result = render(modified)
        self.assertIn('11 of 16 international conference contributions', result)
        self.assertIn('69%</span>', result)

    def test_fwci_discloses_saved_date_and_coverage(self):
        data = json.loads((ROOT / 'tools/fwci_data.json').read_text(encoding='utf-8'))
        doc = html.parse(str(ROOT / 'publications/index.html'))
        tile = doc.xpath('//div[contains(@class,"pubhi_item--fwci")]')[0]
        count = sum(w.get('fwci') is not None for w in data['works'])
        self.assertIn('%d/%d' % (count, len(data['works'])), tile.text_content())
        self.assertEqual(tile.xpath('.//time/@datetime'), [data['fetched']])
        self.assertIn('../tools/fwci_data.json', tile.xpath('.//a/@href'))
