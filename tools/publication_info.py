"""Shared accessible information control for publication metrics."""
import html


def info(name, key, description):
    return ('<span class="metric-info"><button type="button" class="metric-info-button" '
            'aria-label="About %s" aria-expanded="false" aria-controls="metric-%s">'
            '<span aria-hidden="true">i</span></button>'
            '<span class="metric-info-panel" id="metric-%s" role="region" aria-label="About %s" hidden>%s</span></span>'
            % (html.escape(name), key, key, html.escape(name), description))
