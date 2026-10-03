"""CLI entrypoints for CI / nightly release builds."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from traceability.container import build_container
from traceability.logging_setup import configure_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option("--config", "config_path", type=click.Path(exists=True), default=None)
@click.option("--log-level", default=None, help="Override log level")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, log_level: str | None) -> None:
    """ASPICE Continuous Traceability Matrix Generator."""
    container = build_container(config_path=config_path)
    configure_logging(log_level or container.settings.app.log_level)
    ctx.ensure_object(dict)
    ctx.obj["container"] = container


@main.command("sync")
@click.option("--git-since", default=None)
@click.option("--git-branch", default=None)
@click.option("--build-id", default=None)
@click.pass_context
def sync_cmd(
    ctx: click.Context,
    git_since: str | None,
    git_branch: str | None,
    build_id: str | None,
) -> None:
    """Synchronize DOORS ↔ Codebeamer ↔ Git ↔ RQM."""
    container = ctx.obj["container"]

    async def _run() -> int:
        try:
            result = await container.sync_service.sync_all(
                git_since=git_since,
                git_branch=git_branch,
                build_id=build_id,
            )
            click.echo(result.model_dump_json(indent=2))
            return 1 if result.errors else 0
        finally:
            await container.aclose()

    raise SystemExit(asyncio.run(_run()))


@main.command("validate-pr")
@click.argument("pr_number", type=int)
@click.pass_context
def validate_pr_cmd(ctx: click.Context, pr_number: int) -> None:
    """Validate requirement tags and RQM coverage for a pull request."""
    container = ctx.obj["container"]

    async def _run() -> int:
        try:
            result = await container.pr_validator.validate(pr_number)
            click.echo(result.model_dump_json(indent=2))
            return 0 if result.compliant else 2
        finally:
            await container.aclose()

    raise SystemExit(asyncio.run(_run()))


@main.command("generate-matrix")
@click.option("--build-id", default=None)
@click.option("--git-since", default=None)
@click.option("--git-branch", default=None)
@click.option("--skip-sync", is_flag=True, default=False)
@click.option("--pdf/--no-pdf", default=True)
@click.option("--html/--no-html", default=True)
@click.option("--output-dir", default=None, type=click.Path())
@click.pass_context
def generate_matrix_cmd(
    ctx: click.Context,
    build_id: str | None,
    git_since: str | None,
    git_branch: str | None,
    skip_sync: bool,
    pdf: bool,
    html: bool,
    output_dir: str | None,
) -> None:
    """Generate ASPICE HTML/PDF matrix artifact (nightly release builds)."""
    container = ctx.obj["container"]
    out = Path(output_dir or container.settings.matrix.output_dir)

    async def _run() -> int:
        try:
            if not skip_sync:
                await container.sync_service.sync_all(
                    git_since=git_since,
                    git_branch=git_branch,
                    build_id=build_id,
                )
            matrix = container.matrix_generator.generate(build_id=build_id)
            stamp = matrix.generated_at.strftime("%Y%m%dT%H%M%SZ")
            artifacts: dict[str, str] = {}
            if html:
                path = container.html_exporter.write(
                    matrix, out / f"traceability_matrix_{stamp}.html"
                )
                artifacts["html"] = str(path)
            if pdf:
                path = container.pdf_exporter.write(
                    matrix, out / f"traceability_matrix_{stamp}.pdf"
                )
                artifacts["pdf"] = str(path)
            click.echo(
                json.dumps(
                    {
                        "summary": matrix.summary,
                        "artifacts": artifacts,
                        "build_id": build_id,
                    },
                    indent=2,
                )
            )
            # Non-zero if there are coverage gaps — useful for quality gates
            return 0 if matrix.summary.get("rows_with_gaps", 0) == 0 else 3
        finally:
            await container.aclose()

    raise SystemExit(asyncio.run(_run()))


@main.command("serve")
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8080, type=int)
@click.pass_context
def serve_cmd(ctx: click.Context, host: str, port: int) -> None:
    """Run the REST synchronization API."""
    import uvicorn

    # Rebuild app with current config via env/file already loaded into process.
    uvicorn.run("traceability.api.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main(obj={})
