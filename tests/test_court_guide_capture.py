import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

EXTRACTOR_PATH = (
    Path(__file__).parent.parent
    / "scripts"
    / "court_guides_processing_pipeline"
    / "scripts"
    / "extract_court_guides_azure_di.py"
)


def load_extractor_module():
    spec = importlib.util.spec_from_file_location("court_guide_extractor", EXTRACTOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, content: bytes, resolved_url: str):
        self.content = content
        self.resolved_url = resolved_url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.content

    def geturl(self):
        return self.resolved_url


def test_capture_canonical_sources_writes_verified_manifest(monkeypatch, tmp_path):
    extractor = load_extractor_module()
    content = b"%PDF-1.7 canonical guide"
    monkeypatch.setattr(
        extractor,
        "GUIDE_METADATA",
        {"guide.pdf": {"storageUrl": "https://source.example/guide.pdf"}},
    )
    monkeypatch.setattr(
        extractor,
        "urlopen",
        lambda request, timeout: FakeResponse(content, "https://cdn.example/guide.pdf"),
    )

    sources_dir = tmp_path / "sources"
    manifest = extractor.capture_canonical_sources(sources_dir, tmp_path / "source_manifest.json")

    assert (sources_dir / "guide.pdf").read_bytes() == content
    assert manifest["sources"] == [
        {
            "filename": "guide.pdf",
            "source_url": "https://source.example/guide.pdf",
            "resolved_url": "https://cdn.example/guide.pdf",
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        }
    ]


def test_capture_canonical_sources_rejects_non_pdf(monkeypatch, tmp_path):
    extractor = load_extractor_module()
    monkeypatch.setattr(
        extractor,
        "GUIDE_METADATA",
        {"guide.pdf": {"storageUrl": "https://source.example/guide.pdf"}},
    )
    monkeypatch.setattr(
        extractor,
        "urlopen",
        lambda request, timeout: FakeResponse(b"<html>unavailable</html>", "https://source.example/guide.pdf"),
    )

    with pytest.raises(RuntimeError, match="resolved resource is not a PDF"):
        extractor.capture_canonical_sources(tmp_path / "sources", tmp_path / "source_manifest.json")
