"""Create the Search schema for an immutable v4 staging index."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.upload_v4_staging import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_FIELD,
    PRODUCTION_INDEX,
    validate_index_schema,
    validate_staging_target,
)


def build_index(index_name: str):
    from azure.search.documents.indexes.models import (
        HnswAlgorithmConfiguration,
        HnswParameters,
        PermissionFilter,
        SearchableField,
        SearchField,
        SearchFieldDataType,
        SearchIndex,
        SearchIndexPermissionFilterOption,
        SemanticConfiguration,
        SemanticField,
        SemanticPrioritizedFields,
        SemanticSearch,
        SimpleField,
        VectorSearch,
        VectorSearchProfile,
    )

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
        SearchField(
            name=EMBEDDING_FIELD,
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name=f"{EMBEDDING_FIELD}-profile",
        ),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="sourcepage", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="sourcefile", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="storageUrl", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="oids",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            permission_filter=PermissionFilter.USER_IDS,
        ),
        SearchField(
            name="groups",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            permission_filter=PermissionFilter.GROUP_IDS,
        ),
        SimpleField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="subsection_id", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(
            name="subsections", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True
        ),
        SimpleField(name="child_window", type=SearchFieldDataType.Int32, filterable=True),
        SimpleField(name="child_window_count", type=SearchFieldDataType.Int32, filterable=True),
        SearchableField(name="section_title", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
        SearchableField(name="hierarchy_path", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
        SearchField(
            name="legal_references",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True,
            analyzer_name="standard.lucene",
        ),
        SearchableField(name="embedding_text", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
        SimpleField(name="updated", type=SearchFieldDataType.String, filterable=True, sortable=True),
    ]
    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name=f"{EMBEDDING_FIELD}-profile", algorithm_configuration_name="hnsw-config")],
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config", parameters=HnswParameters(metric="cosine"))],
    )
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="default",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="section_title"),
                    content_fields=[
                        SemanticField(field_name="hierarchy_path"),
                        SemanticField(field_name="embedding_text"),
                    ],
                ),
            )
        ]
    )
    return SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
        permission_filter_option=SearchIndexPermissionFilterOption.ENABLED,
    )


def is_existing_index_error(error: Any) -> bool:
    service_error = getattr(error, "error", None)
    generated_error = getattr(error, "model", None)
    response = getattr(error, "response", None)
    status_code = getattr(error, "status_code", None) or getattr(response, "status_code", None)
    expected_code = "ResourceNameAlreadyInUse"
    structured_code = (
        getattr(service_error, "code", None) == expected_code
        or getattr(generated_error, "code", None) == expected_code
    )
    return (
        (status_code == 409 and structured_code)
        or (status_code is None and f"({expected_code})" in str(error))
    )


def provision(index_name: str, service: str) -> None:
    from azure.identity import DefaultAzureCredential
    from azure.core.exceptions import HttpResponseError
    from azure.search.documents.indexes import SearchIndexClient

    endpoint = service if service.startswith("https://") else f"https://{service}.search.windows.net"
    client = SearchIndexClient(endpoint=endpoint, credential=DefaultAzureCredential())
    try:
        result = client.create_index(build_index(index_name))
        status = "created"
    except HttpResponseError as error:
        if not is_existing_index_error(error):
            raise
        result = client.get_index(index_name)
        status = "reused"
    validate_index_schema(result)
    validate_index_schema(client.get_index(index_name))
    print(json.dumps({"index": result.name, "status": status}))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True)
    parser.add_argument("--service", default=os.environ.get("AZURE_SEARCH_SERVICE", ""))
    parser.add_argument("--execute", action="store_true", help="Create the index; default is validation-only")
    args = parser.parse_args()
    validate_staging_target(args.index)
    if args.index.casefold() == PRODUCTION_INDEX.casefold():
        raise ValueError("Refusing to provision the production index")
    if args.execute:
        if not args.service:
            raise ValueError("--service or AZURE_SEARCH_SERVICE is required with --execute")
        provision(args.index, args.service)
    else:
        print(json.dumps({"index": args.index, "status": "validated", "execute": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
