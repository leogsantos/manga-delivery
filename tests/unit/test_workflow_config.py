"""
Validates that GitHub Actions workflow files are internally consistent.
Prevents typos in image references from breaking the scheduled pipeline.
"""

from pathlib import Path

WORKFLOWS_DIR = Path(__file__).parents[2] / ".github" / "workflows"


def _read(filename: str) -> str:
    return (WORKFLOWS_DIR / filename).read_text(encoding="utf-8")


class TestPipelineImageReference:
    def test_pipeline_uses_dynamic_owner(self):
        content = _read("pipeline.yml")
        assert "github.repository_owner" in content, (
            "pipeline.yml must use ${{ github.repository_owner }} in the container "
            "image — hardcoded usernames cause 'manifest unknown' errors on GHCR."
        )

    def test_pipeline_image_name_is_manga_delivery(self):
        content = _read("pipeline.yml")
        assert "manga-delivery:latest" in content

    def test_no_hardcoded_username_in_pipeline_image(self):
        content = _read("pipeline.yml")
        # Matches lines that define the container image with a literal username
        # (anything that is NOT a GitHub expression)
        image_lines = [
            line.strip()
            for line in content.splitlines()
            if "image: ghcr.io/" in line
        ]
        for line in image_lines:
            assert "${{" in line, (
                f"Container image must use a GitHub expression, not a hardcoded "
                f"username. Found: {line!r}"
            )


class TestBuildImageWorkflow:
    def test_build_pushes_manga_delivery_image(self):
        content = _read("build-image.yml")
        assert "manga-delivery:latest" in content

    def test_build_lowercases_username(self):
        content = _read("build-image.yml")
        assert "tr '[:upper:]' '[:lower:]'" in content, (
            "build-image.yml must lowercase the username before pushing to GHCR."
        )

    def test_build_uses_github_output_for_username(self):
        content = _read("build-image.yml")
        assert "GITHUB_OUTPUT" in content

    def test_build_image_tag_uses_step_output(self):
        content = _read("build-image.yml")
        assert "steps.lower.outputs.username" in content


class TestWorkflowConsistency:
    def test_both_workflows_reference_same_image_name(self):
        image_name = "manga-delivery:latest"
        assert image_name in _read("pipeline.yml"), (
            f"pipeline.yml must reference '{image_name}'"
        )
        assert image_name in _read("build-image.yml"), (
            f"build-image.yml must reference '{image_name}'"
        )

    def test_pipeline_workflow_file_exists(self):
        assert (WORKFLOWS_DIR / "pipeline.yml").exists()

    def test_build_image_workflow_file_exists(self):
        assert (WORKFLOWS_DIR / "build-image.yml").exists()

    def test_tests_workflow_file_exists(self):
        assert (WORKFLOWS_DIR / "tests.yml").exists()
