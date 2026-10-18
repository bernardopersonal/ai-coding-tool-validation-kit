"""List the controlled source documents."""

import os


def list_sources(root):
    """Sorted repository-relative paths of the Markdown files in docs/sources."""
    base = os.path.join(root, "docs", "sources")
    return sorted("docs/sources/" + name for name in os.listdir(base) if name.endswith(".md"))
