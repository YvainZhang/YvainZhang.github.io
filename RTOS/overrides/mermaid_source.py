"""Keep Mermaid source as text until the local renderer handles it."""
import html
import re

_FENCE = re.compile(r'(<pre\b[^>]*class="rtos-mermaid"[^>]*><code>)(.*?)(</code></pre>)', re.S)


def on_page_content(content, **kwargs):
    # mermaid2's custom formatter emits raw labels. Escape once, before HTML parsing,
    # so angle brackets in comparisons and C types survive DOM textContent.
    return _FENCE.sub(lambda match: match[1] + html.escape(match[2]) + match[3], content)
