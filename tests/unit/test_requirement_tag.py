import pytest

from traceability.domain.requirement_tag import RequirementTagParser


@pytest.mark.unit
def test_valid_tag_examples(tag_parser: RequirementTagParser) -> None:
    assert tag_parser.is_valid("REQ_ADAS_USS_042")
    assert tag_parser.is_valid("req_adas_uss_042")
    assert tag_parser.normalize("req_adas_uss_042") == "REQ_ADAS_USS_042"


@pytest.mark.unit
@pytest.mark.parametrize(
    "tag",
    ["REQ_", "ADAS_USS_042", "REQ-ADAS-USS-042", "REQ_ADAS_USS_42", ""],
)
def test_invalid_tags(tag_parser: RequirementTagParser, tag: str) -> None:
    assert not tag_parser.is_valid(tag)


@pytest.mark.unit
def test_extract_multiple_unique_sorted(tag_parser: RequirementTagParser) -> None:
    text = "See REQ_ADAS_CAM_010 and REQ_ADAS_USS_042; also REQ_ADAS_USS_042 again."
    assert tag_parser.extract(text) == ("REQ_ADAS_CAM_010", "REQ_ADAS_USS_042")


@pytest.mark.unit
def test_extract_from_commit_prefers_requires_header(tag_parser: RequirementTagParser) -> None:
    message = (
        "fix: sensor glitch\n\n"
        "Requires: REQ_ADAS_USS_042, REQ_ADAS_USS_043\n"
        "Mentions unrelated REQ_ADAS_CAM_010 in body for context only should still be ignored "
        "because header wins."
    )
    # Header extraction returns only Requires: line tags
    assert tag_parser.extract_from_commit_message(message) == (
        "REQ_ADAS_USS_042",
        "REQ_ADAS_USS_043",
    )


@pytest.mark.unit
def test_extract_from_commit_falls_back_to_body(tag_parser: RequirementTagParser) -> None:
    message = "chore: docs\n\nLinked to REQ_ADAS_CAM_010"
    assert tag_parser.extract_from_commit_message(message) == ("REQ_ADAS_CAM_010",)
