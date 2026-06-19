"""Smoke tests for the CLI surface (parsing, validation, help)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from domhunt.checker import CheckResult, Status
from domhunt.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_help_works(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "domhunt" in result.output


def test_rejects_invalid_name(runner: CliRunner) -> None:
    result = runner.invoke(main, ["-bad-"])
    assert result.exit_code != 0


def test_renders_table_for_valid_name(runner: CliRunner) -> None:
    fake = [
        CheckResult("demo.com", Status.TAKEN),
        CheckResult("demo.io", Status.AVAILABLE),
    ]

    async def fake_check_many(name, tlds, concurrency=10):
        return fake

    with patch("domhunt.cli.check_many", side_effect=fake_check_many):
        result = runner.invoke(main, ["demo", "--tlds", "com,io"])

    assert result.exit_code == 0
    assert "demo.com" in result.output
    assert "demo.io" in result.output
    assert "1 available" in result.output


def test_runs_suggester_when_nothing_available(runner: CliRunner) -> None:
    call_count = {"n": 0}

    async def fake_check_many(name, tlds, concurrency=10):
        call_count["n"] += 1
        # First call: original name, everything taken.
        # Subsequent calls: variations — first one has a free domain, rest taken.
        if call_count["n"] == 1:
            return [CheckResult(f"{name}.{t}", Status.TAKEN) for t in tlds]
        if call_count["n"] == 2:
            return [CheckResult(f"{name}.{tlds[0]}", Status.AVAILABLE)]
        return [CheckResult(f"{name}.{tlds[0]}", Status.TAKEN)]

    with patch("domhunt.cli.check_many", side_effect=fake_check_many):
        result = runner.invoke(main, ["takenname", "--tlds", "com"])

    assert "Try one of these instead" in result.output


def test_no_suggest_flag_disables_suggester(runner: CliRunner) -> None:
    async def fake_check_many(name, tlds, concurrency=10):
        return [CheckResult(f"{name}.{t}", Status.TAKEN) for t in tlds]

    with patch("domhunt.cli.check_many", side_effect=fake_check_many):
        result = runner.invoke(main, ["takenname", "--tlds", "com", "--no-suggest"])

    assert "Try one of these instead" not in result.output


def test_available_only_filters(runner: CliRunner) -> None:
    fake = [
        CheckResult("demo.com", Status.TAKEN),
        CheckResult("demo.io", Status.AVAILABLE),
    ]

    async def fake_check_many(name, tlds, concurrency=10):
        return fake

    with patch("domhunt.cli.check_many", side_effect=fake_check_many):
        result = runner.invoke(main, ["demo", "--tlds", "com,io", "--available-only"])

    assert result.exit_code == 0
    assert "demo.io" in result.output
    assert "demo.com" not in result.output
