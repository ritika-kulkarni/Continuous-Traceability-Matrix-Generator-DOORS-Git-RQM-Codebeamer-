"""Requirement tag parsing and validation (e.g. REQ_ADAS_USS_042)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DEFAULT_REQ_TAG_PATTERN = r"REQ_[A-Z0-9]+(?:_[A-Z0-9]+)*_\d{3,}"


@dataclass(frozen=True)
class RequirementTagParser:
    """Extracts and validates ASPICE-style requirement identifiers."""

    pattern: str = DEFAULT_REQ_TAG_PATTERN
    _regex: re.Pattern[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_regex", re.compile(self.pattern, re.IGNORECASE))

    def is_valid(self, tag: str) -> bool:
        if not tag:
            return False
        return bool(self._regex.fullmatch(tag.strip()))

    def normalize(self, tag: str) -> str:
        return tag.strip().upper()

    def extract(self, text: str | None) -> tuple[str, ...]:
        """Return unique, normalized tags found in free-form text."""
        if not text:
            return ()
        found = {self.normalize(m.group(0)) for m in self._regex.finditer(text)}
        return tuple(sorted(found))

    def extract_from_commit_message(self, message: str) -> tuple[str, ...]:
        """Prefer tags from conventional headers, then fall back to body scan.

        Supported header forms:
          Requires: REQ_ADAS_USS_042, REQ_ADAS_USS_043
          REQ: REQ_ADAS_USS_042
        """
        headers: list[str] = []
        for line in message.splitlines():
            lower = line.lower().strip()
            if lower.startswith("requires:") or lower.startswith("req:"):
                headers.extend(self.extract(line))
        if headers:
            return tuple(sorted(set(headers)))
        return self.extract(message)
