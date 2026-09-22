import json
import subprocess
import sys

import pytest

from scripts import validate_v4_active_release
from scripts.validate_v4_active_release import (
    ActiveReleaseError,
    validate_active_release,
    validate_appservice_release,
)


def app_with_release(release_id):
    return {
        "properties": {
            "template": {
                "containers": [
                    {
                        "image": "registry.example.test/legal-rag@sha256:" + "a" * 64,
                        "env": [{"name": "V4_RELEASE_ID", "value": release_id}],
                    }
                ],
            },
            "latestRevisionName": "legal-rag--release-1",
            "configuration": {"ingress": {"traffic": [{"revisionName": "legal-rag--release-1", "weight": 100}]}},
        }
    }


def test_active_release_matches_exactly():
    assert (
        validate_active_release(
            app_with_release("release-1"),
            "release-1",
            expected_image_digest="registry.example.test/legal-rag@sha256:" + "a" * 64,
            expected_revision_name="legal-rag--release-1",
        )
        == "release-1"
    )


@pytest.mark.parametrize("app", [{}, app_with_release(""), {"properties": {"template": {"containers": []}}}])
def test_active_release_rejects_missing_or_empty_identity(app):
    with pytest.raises(ActiveReleaseError):
        validate_active_release(app, "release-1")


def test_active_release_rejects_mismatch():
    with pytest.raises(ActiveReleaseError, match="mismatch"):
        validate_active_release(app_with_release("release-1"), "release-2")


@pytest.mark.parametrize("release_id", ["release-r4", "legacy-release", "v3-release"])
def test_active_release_rejects_legacy_identity(release_id):
    with pytest.raises(ActiveReleaseError, match="legacy"):
        validate_active_release(app_with_release(release_id), release_id)


def test_active_release_rejects_image_mismatch():
    with pytest.raises(ActiveReleaseError, match="image mismatch"):
        validate_active_release(
            app_with_release("release-1"),
            "release-1",
            expected_image_digest="registry.example.test/legal-rag@sha256:" + "b" * 64,
        )


def test_active_release_rejects_revision_without_full_traffic():
    app = app_with_release("release-1")
    app["properties"]["configuration"]["ingress"]["traffic"][0]["weight"] = 90
    with pytest.raises(ActiveReleaseError, match="100% active traffic"):
        validate_active_release(app, "release-1")


def test_active_release_rejects_missing_traffic():
    app = app_with_release("release-1")
    del app["properties"]["configuration"]["ingress"]["traffic"]
    with pytest.raises(ActiveReleaseError, match="traffic"):
        validate_active_release(app, "release-1")


@pytest.mark.parametrize(
    "mutation, message",
    [
        (
            lambda app: app["properties"]["template"]["containers"][0].update(
                image="registry.example.test/legal-rag:latest"
            ),
            "not immutable",
        ),
        (lambda app: app["properties"].pop("latestRevisionName"), "no latest revision"),
        (lambda app: app["properties"]["template"]["containers"][0].update(env={}), "environment is invalid"),
        (lambda app: app["properties"]["configuration"]["ingress"].update(traffic=[]), "traffic configuration"),
    ],
)
def test_active_release_rejects_invalid_runtime_shape(mutation, message):
    app = app_with_release("release-1")
    mutation(app)

    with pytest.raises(ActiveReleaseError, match=message):
        validate_active_release(app, "release-1")


def test_active_release_rejects_empty_legacy_or_mismatched_revision_expectations():
    app = app_with_release("release-1")

    with pytest.raises(ActiveReleaseError, match="must not be empty"):
        validate_active_release(app, " ")
    with pytest.raises(ActiveReleaseError, match="legacy"):
        validate_active_release(app, "release-v3")
    with pytest.raises(ActiveReleaseError, match="revision mismatch"):
        validate_active_release(app, "release-1", expected_revision_name="other-revision")


def test_appservice_active_release_matches_identity():
    image = "registry.example.test/legal-rag@sha256:" + "a" * 64
    settings = [
        {"name": "V4_RELEASE_ID", "value": "release-1"},
        {"name": "V4_IMAGE_DIGEST", "value": image},
        {"name": "V4_REVISION_NAME", "value": "production-v4"},
    ]
    assert (
        validate_appservice_release(
            settings, "release-1", expected_image_digest=image, expected_revision_name="production-v4"
        )
        == "release-1"
    )


@pytest.mark.parametrize(
    "settings, expected, message",
    [
        ([], "release-1", "release mismatch"),
        ([{"name": "V4_RELEASE_ID", "value": "release-1"}], "release-2", "release mismatch"),
        ([{"name": "V4_RELEASE_ID", "value": "release-1"}], "release-1", "not immutable"),
        (
            [
                {"name": "V4_RELEASE_ID", "value": "release-1"},
                {"name": "V4_IMAGE_DIGEST", "value": "registry@sha256:abc"},
            ],
            "release-1",
            "no revision name",
        ),
    ],
)
def test_appservice_active_release_rejects_missing_or_mismatched_identity(settings, expected, message):
    with pytest.raises(ActiveReleaseError, match=message):
        validate_appservice_release(settings, expected)


def test_appservice_active_release_rejects_expected_identity_mismatches():
    image = "registry.example.test/legal-rag@sha256:" + "a" * 64
    settings = [
        {"name": "V4_RELEASE_ID", "value": "release-1"},
        {"name": "V4_IMAGE_DIGEST", "value": image},
        {"name": "V4_REVISION_NAME", "value": "production-v4"},
    ]

    with pytest.raises(ActiveReleaseError, match="image mismatch"):
        validate_appservice_release(settings, "release-1", expected_image_digest="registry@sha256:other")
    with pytest.raises(ActiveReleaseError, match="revision mismatch"):
        validate_appservice_release(settings, "release-1", expected_revision_name="other")


def test_validator_cli_accepts_appservice_settings_array(tmp_path):
    image = "registry.example.test/legal-rag@sha256:" + "a" * 64
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            [
                {"name": "V4_RELEASE_ID", "value": "release-1"},
                {"name": "V4_IMAGE_DIGEST", "value": image},
                {"name": "V4_REVISION_NAME", "value": "production-v4"},
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_v4_active_release.py",
            "--app-json",
            str(settings_path),
            "--expected-release-id",
            "release-1",
            "--platform",
            "appservice",
            "--expected-image-digest",
            image,
            "--expected-revision-name",
            "production-v4",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "release-1"


@pytest.mark.parametrize("release_id", ["release-v3", "release-r4", "legacy-release"])
def test_appservice_active_release_rejects_legacy_identity(release_id):
    settings = [{"name": "V4_RELEASE_ID", "value": release_id}]
    with pytest.raises(ActiveReleaseError, match="legacy"):
        validate_appservice_release(settings, release_id)


def test_active_release_main_validates_container_app_in_process(monkeypatch, tmp_path, capsys):
    app_path = tmp_path / "container-app.json"
    app_path.write_text(json.dumps(app_with_release("release-1")))
    monkeypatch.setattr(
        "sys.argv",
        [
            "validate_v4_active_release.py",
            "--app-json",
            str(app_path),
            "--expected-release-id",
            "release-1",
        ],
    )

    assert validate_v4_active_release.main() == 0
    assert capsys.readouterr().out.strip() == "release-1"


@pytest.mark.parametrize(
    "payload, platform, message",
    [
        ([], "containerapps", "Container App response must be a JSON object"),
        ({}, "appservice", "App Service settings response must be a JSON array"),
    ],
)
def test_active_release_main_rejects_wrong_platform_response(monkeypatch, tmp_path, payload, platform, message):
    app_path = tmp_path / "app.json"
    app_path.write_text(json.dumps(payload))
    monkeypatch.setattr(
        "sys.argv",
        [
            "validate_v4_active_release.py",
            "--app-json",
            str(app_path),
            "--expected-release-id",
            "release-1",
            "--platform",
            platform,
        ],
    )

    with pytest.raises(SystemExit) as error:
        validate_v4_active_release.main()

    assert error.value.code == 2
