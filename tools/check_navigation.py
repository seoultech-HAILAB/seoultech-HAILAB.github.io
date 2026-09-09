#!/usr/bin/env python3
"""전체 페이지의 About 메뉴를 읽기 전용으로 검사한다."""
from pathlib import Path

from about_navigation import ABOUT_LINKS, navigation_errors
from tidy_pages import PAGES, ROOT


def main():
    errors = []
    for _, target in ABOUT_LINKS:
        if not (Path(ROOT) / target).is_file():
            errors.append("missing navigation destination: " + target)
    for rel in PAGES:
        source = (Path(ROOT) / rel).read_text(encoding="utf-8")
        errors.extend("%s: %s" % (rel, error) for error in navigation_errors(source, rel))
    if errors:
        print("\n".join(errors))
        print("Run python tools/tidy_pages.py and commit the corrected HTML.")
        return 1
    print("About navigation OK on %d pages." % len(PAGES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
