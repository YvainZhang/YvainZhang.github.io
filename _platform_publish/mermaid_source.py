"""Preserve diagram source as text for the dedicated client renderer."""
import html
import re

_FENCE = re.compile(r'(<pre\b[^>]*class="platform-mermaid"[^>]*><code>)(.*?)(</code></pre>)', re.S)


def on_page_content(content, **kwargs):
    return _FENCE.sub(lambda match: match[1] + html.escape(match[2]) + match[3], content)
