"""Git hosting REST adapter (GitHub-compatible by default)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from traceability.adapters.http_base import HttpAdapterBase
from traceability.config import GitSettings
from traceability.domain.models import GitCommit, PullRequest
from traceability.domain.requirement_tag import RequirementTagParser
from traceability.exceptions import AdapterError


class GitAdapter(HttpAdapterBase):
    def __init__(
        self,
        settings: GitSettings,
        *,
        tag_parser: RequirementTagParser | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        token = settings.token.get_secret_value()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        super().__init__(
            system="git",
            base_url=settings.base_url,
            timeout_seconds=settings.timeout_seconds,
            max_retries=settings.max_retries,
            client=client,
            headers=headers,
        )
        if settings.provider != "github":
            # Provider-specific path mapping can be extended without changing services.
            raise AdapterError(
                "git",
                f"provider '{settings.provider}' not implemented; "
                "use github or inject a custom port",
                retryable=False,
            )
        self._owner = settings.owner
        self._repo = settings.repo
        self._tag_parser = tag_parser or RequirementTagParser()

    @property
    def _repo_prefix(self) -> str:
        return f"/repos/{self._owner}/{self._repo}"

    async def fetch_pull_request(self, number: int) -> PullRequest:
        pr = await self.get_json(f"{self._repo_prefix}/pulls/{number}")
        commits_payload = await self.get_json(f"{self._repo_prefix}/pulls/{number}/commits")
        commits = tuple(self._to_commit(c, pr_number=number) for c in commits_payload)
        return PullRequest(
            number=int(pr["number"]),
            title=str(pr.get("title") or ""),
            body=str(pr.get("body") or ""),
            author=str((pr.get("user") or {}).get("login") or "unknown"),
            source_branch=str((pr.get("head") or {}).get("ref") or ""),
            target_branch=str((pr.get("base") or {}).get("ref") or ""),
            commits=commits,
            head_sha=str((pr.get("head") or {}).get("sha") or ""),
            url=pr.get("html_url"),
        )

    async def fetch_commits(
        self,
        *,
        since: str | None = None,
        branch: str | None = None,
        limit: int = 100,
    ) -> list[GitCommit]:
        params: dict[str, Any] = {"per_page": min(limit, 100)}
        if since:
            params["since"] = since
        if branch:
            params["sha"] = branch
        payload = await self.get_json(f"{self._repo_prefix}/commits", params=params)
        return [self._to_commit(item) for item in payload[:limit]]

    def _to_commit(self, item: dict[str, Any], *, pr_number: int | None = None) -> GitCommit:
        commit = item.get("commit") or item
        message = str(commit.get("message") or "")
        author_block = commit.get("author") or {}
        login = (item.get("author") or {}).get("login")
        author = str(author_block.get("name") or login or "unknown")
        date_raw = author_block.get("date") or item.get("committed_at")
        committed_at = (
            datetime.fromisoformat(str(date_raw).replace("Z", "+00:00"))
            if date_raw
            else datetime.fromtimestamp(0)
        )
        files = tuple(
            str(f.get("filename") or f)
            for f in (item.get("files") or [])
            if f
        )
        return GitCommit(
            sha=str(item.get("sha") or item.get("id") or ""),
            message=message,
            author=author,
            committed_at=committed_at,
            pr_number=pr_number,
            requirement_tags=self._tag_parser.extract_from_commit_message(message),
            files_changed=files,
        )
