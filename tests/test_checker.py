"""Unit tests for the checker using respx to mock the RDAP gateway."""

from __future__ import annotations

import httpx
import pytest
import respx

from domhunt.checker import RDAP_GATEWAY, Status, check_many


@respx.mock
@pytest.mark.asyncio
async def test_mixed_responses_classified_correctly():
    respx.get(RDAP_GATEWAY + "demo.com").mock(return_value=httpx.Response(200, json={}))
    respx.get(RDAP_GATEWAY + "demo.io").mock(return_value=httpx.Response(404))
    respx.get(RDAP_GATEWAY + "demo.xyz").mock(return_value=httpx.Response(500))

    results = await check_many("demo", ["com", "io", "xyz"], concurrency=3)

    by_domain = {r.domain: r for r in results}
    assert by_domain["demo.com"].status is Status.TAKEN
    assert by_domain["demo.io"].status is Status.AVAILABLE
    assert by_domain["demo.xyz"].status is Status.UNKNOWN
    assert "HTTP 500" in by_domain["demo.xyz"].detail


@respx.mock
@pytest.mark.asyncio
async def test_timeout_becomes_unknown():
    respx.get(RDAP_GATEWAY + "x.com").mock(side_effect=httpx.TimeoutException("slow"))

    results = await check_many("x", ["com"], concurrency=1)

    assert results[0].status is Status.UNKNOWN
    assert results[0].detail == "timeout"


@respx.mock
@pytest.mark.asyncio
async def test_preserves_tld_order():
    for tld in ("com", "io", "dev"):
        respx.get(RDAP_GATEWAY + f"foo.{tld}").mock(return_value=httpx.Response(404))

    results = await check_many("foo", ["com", "io", "dev"])

    assert [r.domain for r in results] == ["foo.com", "foo.io", "foo.dev"]
