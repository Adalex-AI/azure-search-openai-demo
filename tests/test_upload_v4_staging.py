import json
from types import SimpleNamespace

import pytest

from scripts.create_v4_staging_index import is_existing_index_error
from scripts.upload_v4_staging import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_FIELD,
    load_documents,
    project_document,
    validate_index_schema,
    validate_staging_target,
)


def test_staging_target_rejects_production():
    with pytest.raises(ValueError, match="production"):
        validate_staging_target("legal-court-rag-index-v3")


@pytest.mark.parametrize("index_name", ["legal-court-rag-index", "legal-court-rag-v4-prod"])
def test_staging_target_requires_v4_staging_name(index_name):
    with pytest.raises(ValueError, match="v4.*staging"):
        validate_staging_target(index_name)


def test_load_documents_validates_ids_and_embeddings(tmp_path):
    path = tmp_path / "documents.jsonl"
    document = {
        "id": "doc-1",
        "content": "content",
        "embedding": [0.0] * EMBEDDING_DIMENSIONS,
    }
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")

    assert load_documents(path) == [document]


def test_load_documents_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "documents.jsonl"
    document = {"id": "doc-1", "content": "content", "embedding": [0.0] * EMBEDDING_DIMENSIONS}
    path.write_text(json.dumps(document) + "\n" + json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate document id"):
        load_documents(path)


class FakeField:
    def __init__(
        self,
        name,
        dimensions=EMBEDDING_DIMENSIONS,
        profile="embedding-profile",
        permission_filter=None,
    ):
        self.name = name
        self.vector_search_dimensions = dimensions if name == EMBEDDING_FIELD else None
        self.vector_search_profile_name = profile if name == EMBEDDING_FIELD else None
        self.permission_filter = permission_filter


class FakeIndex:
    def __init__(self, fields, permission_filter_option="enabled"):
        self.fields = fields
        self.permission_filter_option = permission_filter_option


def test_validate_index_schema_requires_all_fields():
    with pytest.raises(ValueError, match="missing required fields"):
        validate_index_schema(FakeIndex([FakeField("id")]))


def test_validate_index_schema_checks_embedding_dimensions():
    fields = [
        FakeField(name, permission_filter={"oids": "userIds", "groups": "groupIds"}.get(name))
        for name in {
            "id",
            "content",
            "category",
            "sourcepage",
            "sourcefile",
            "storageUrl",
            "oids",
            "groups",
            "parent_id",
            "subsection_id",
            "subsections",
            "updated",
        }
    ]
    fields.append(FakeField(EMBEDDING_FIELD, dimensions=1536))

    with pytest.raises(ValueError, match="1536"):
        validate_index_schema(FakeIndex(fields))


def test_validate_index_schema_requires_acl_contract():
    fields = [
        FakeField(name, permission_filter={"oids": "userIds", "groups": "groupIds"}.get(name))
        for name in {
            "id",
            "content",
            "category",
            "sourcepage",
            "sourcefile",
            "storageUrl",
            "oids",
            "groups",
            "parent_id",
            "subsection_id",
            "subsections",
            "updated",
            EMBEDDING_FIELD,
        }
    ]

    validate_index_schema(FakeIndex(fields))

    with pytest.raises(ValueError, match="permission filtering"):
        validate_index_schema(FakeIndex(fields, permission_filter_option="disabled"))

    next(field for field in fields if field.name == "oids").permission_filter = None
    with pytest.raises(ValueError, match="oids.*userIds"):
        validate_index_schema(FakeIndex(fields))


def test_upload_documents_rejects_short_acknowledgement(monkeypatch):
    from scripts.upload_v4_staging import upload_documents

    class Result:
        succeeded = True

    class FakeIndexClient:
        def __init__(self, **kwargs):
            pass

        def get_index(self, index_name):
            return FakeIndex(
                [
                    FakeField(name, permission_filter={"oids": "userIds", "groups": "groupIds"}.get(name))
                    for name in {
                        "id",
                        "content",
                        "category",
                        "sourcepage",
                        "sourcefile",
                        "storageUrl",
                        "oids",
                        "groups",
                        "parent_id",
                        "subsection_id",
                        "subsections",
                        "updated",
                        EMBEDDING_FIELD,
                    }
                ]
            )

    class FakeSearchClient:
        def __init__(self, **kwargs):
            pass

        def upload_documents(self, documents):
            return [Result()]

    monkeypatch.setattr("azure.search.documents.indexes.SearchIndexClient", FakeIndexClient)
    monkeypatch.setattr("azure.search.documents.SearchClient", FakeSearchClient)
    documents = [
        {"id": "one", "content": "content", "embedding": [0.0] * EMBEDDING_DIMENSIONS},
        {"id": "two", "content": "content", "embedding": [0.0] * EMBEDDING_DIMENSIONS},
    ]

    with pytest.raises(RuntimeError, match="acknowledgement count"):
        upload_documents("legal-court-rag-v4-staging-test", "search", documents, 2)


def test_project_document_maps_artifact_embedding_to_v4_field():
    document = {"id": "one", "content": "content", "embedding": [0.0] * EMBEDDING_DIMENSIONS}

    projected = project_document(document)

    assert projected[EMBEDDING_FIELD] == document["embedding"]
    assert "embedding" not in projected


def test_provisioner_dry_run_accepts_disposable_target():

    # The parser-level behavior is covered by the validation-only invocation in
    # the release command; this test keeps the shared target guard exercised.
    validate_staging_target("legal-court-rag-v4-staging-test")


def test_provisioner_recognizes_only_the_expected_existing_index_conflict():
    expected = SimpleNamespace(
        response=SimpleNamespace(status_code=409), error=SimpleNamespace(code="ResourceNameAlreadyInUse")
    )
    wrong_code = SimpleNamespace(status_code=409, error=SimpleNamespace(code="CannotCreateExistingIndex"))
    wrong_status = SimpleNamespace(status_code=500, error=SimpleNamespace(code="ResourceNameAlreadyInUse"))

    assert is_existing_index_error(expected)
    assert not is_existing_index_error(wrong_code)
    assert not is_existing_index_error(wrong_status)
