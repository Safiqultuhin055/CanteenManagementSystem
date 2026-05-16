"""Load diagram sources for help / technical documentation."""
from pathlib import Path

from django.conf import settings


def _diagrams_dir():
    return Path(settings.BASE_DIR) / 'docs' / 'diagrams'


def load_mermaid(filename):
    """Read .mmd file and strip comment lines for cleaner Mermaid render."""
    path = _diagrams_dir() / filename
    if not path.exists():
        return ''
    lines = []
    for line in path.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if stripped.startswith('%%'):
            continue
        lines.append(line)
    return '\n'.join(lines).strip()


def diagram_assets():
    """Return URLs/flags for PNG diagrams if present on disk."""
    candidates = [
        Path(settings.BASE_DIR) / 'static' / 'docs',
        _diagrams_dir() / 'images',
    ]

    def find_png(name):
        for folder in candidates:
            path = folder / name
            if path.exists():
                return True
        return False

    return {
        'has_erd_png': find_png('erd_diagram.png'),
        'has_flow_png': find_png('overall_functional_flow.png'),
    }


def diagram_context():
    return {
        **diagram_assets(),
        'mermaid_erd': load_mermaid('erd.mmd'),
        'mermaid_flow': load_mermaid('overall_functional_flow.mmd'),
    }
