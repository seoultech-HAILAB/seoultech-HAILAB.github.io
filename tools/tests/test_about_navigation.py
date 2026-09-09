import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from about_navigation import navigation_errors, sync_about_nav


# Issue #2: Facility was renamed only in href; Join Us disappeared on arrival.
BROKEN = '''<nav id="lnb" class="lnb" aria-label="Main menu">
<ul class="depth1"><li><a href="#" class="d1">About</a><ul class="depth2">
<li><a href="../about/index.html">Research Area</a></li>
<li><a href="../about/join.html" class="on">Facility</a></li>
<li><a href="../about/patents.html">Patent</a></li>
</ul></li><li><a href="../members/index.html" class="d1">Members</a></li></ul>
</nav><main><a href="../about/join.html">Apply</a></main>'''


class AboutNavigationTests(unittest.TestCase):
    def test_issue_2_is_detected_and_repaired(self):
        self.assertTrue(navigation_errors(BROKEN, "about/join.html"))
        fixed = sync_about_nav(BROKEN, "about/join.html")
        self.assertEqual(navigation_errors(fixed, "about/join.html"), [])
        self.assertIn('<a href="facility.html">Facility</a>', fixed)
        self.assertIn('<a href="join.html" class="on">Join Us</a>', fixed)
        self.assertIn('<a href="../members/index.html" class="d1">Members</a>', fixed)
        self.assertTrue(fixed.endswith('<main><a href="../about/join.html">Apply</a></main>'))
        self.assertEqual(sync_about_nav(fixed, "about/join.html"), fixed)

    def test_relative_paths_and_selection(self):
        cases = (
            ("index.html", "about/join.html", None),
            ("about/index.html", "join.html", "Research Area"),
            ("about/facility.html", "join.html", "Facility"),
            ("about/patents.html", "join.html", "Patent"),
            ("about/patents/2/index.html", "../../join.html", "Patent"),
            ("board/news/82.html", "../../about/join.html", None),
            ("404.html", "/about/join.html", None),
        )
        for rel, join_href, active in cases:
            with self.subTest(rel=rel):
                fixed = sync_about_nav(BROKEN, rel)
                self.assertEqual(navigation_errors(fixed, rel), [])
                self.assertIn('href="%s">Join Us' % join_href, fixed)
                self.assertEqual(fixed.count('class="on"'), int(active is not None))
                if active:
                    self.assertIn('class="on">%s</a>' % active, fixed)

    def test_corruptions_fail_validation(self):
        fixed = sync_about_nav(BROKEN, "about/join.html")
        join = '<li><a href="join.html" class="on">Join Us</a></li>'
        facility = '<li><a href="facility.html">Facility</a></li>'
        corruptions = (
            fixed.replace(join, ""),
            fixed.replace(join, join + join),
            fixed.replace("Join Us", "Facility"),
            fixed.replace('href="facility.html"', 'href="join.html"'),
            fixed.replace(' class="on"', ""),
            fixed.replace('href="facility.html"', 'href="facility.html" class="on"'),
            fixed.replace(facility, "").replace(join, join + facility),
            fixed.replace('href="join.html"', 'href="https://other.invalid/about/join.html"'),
        )
        for source in corruptions:
            with self.subTest(source=source):
                self.assertTrue(navigation_errors(source, "about/join.html"))
                self.assertEqual(sync_about_nav(source, "about/join.html"), fixed)

    def test_missing_menu_fails_loudly(self):
        for source in ("<main>No menu</main>", BROKEN.replace("About", "Missing"), BROKEN + BROKEN):
            self.assertTrue(navigation_errors(source, "about/join.html"))
            with self.assertRaises(ValueError):
                sync_about_nav(source, "about/join.html")

    def test_404_links_work_at_missing_nested_urls(self):
        fixed = sync_about_nav(BROKEN, "404.html")
        self.assertEqual(navigation_errors(fixed, "404.html"), [])
        broken = fixed.replace('href="/about/join.html"', 'href="about/join.html"')
        self.assertTrue(navigation_errors(broken, "404.html"))
        self.assertEqual(sync_about_nav(broken, "404.html"), fixed)


if __name__ == "__main__":
    unittest.main()
