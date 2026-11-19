"""Keep the plugin and MCP registry metadata consistent with the package."""

from __future__ import annotations

import json
import re
from pathlib import Path

from soa import __version__
from soa.mcp_server import SERVER_NAME

ROOT = Path(__file__).resolve().parent.parent
NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    assert match
    return match.group(1)


def test_versions_agree():
    assert pyproject_version() == __version__
    assert load(".cursor-plugin/plugin.json")["version"] == __version__
    server = load("server.json")
    assert server["version"] == __version__
    assert all(pkg["version"] == __version__ for pkg in server["packages"])


def test_cursor_plugin_manifest():
    manifest = load(".cursor-plugin/plugin.json")
    assert NAME_PATTERN.match(manifest["name"])
    assert manifest["name"] == SERVER_NAME
    assert manifest["license"] == "MIT"
    assert manifest["description"]
    assert manifest["author"]["name"]
    for field in ("logo", "skills", "mcpServers"):
        value = manifest[field]
        assert not value.startswith("/") and ".." not in value
        assert (ROOT / value).exists(), value


def test_skill_frontmatter():
    for skill in (ROOT / "skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        front = text.split("---\n")[1]
        assert re.search(r"^name: \S+", front, re.MULTILINE)
        assert re.search(r"^description: .+", front, re.MULTILINE)


def test_mcp_json_launches_the_mcp_subcommand():
    servers = load("mcp.json")["mcpServers"]
    entry = servers[SERVER_NAME]
    assert entry["args"][-2:] == ["system-on-an-agent", "mcp"]
    assert "env" not in entry


def test_server_json_follows_registry_conventions():
    server = load("server.json")
    assert server["name"] == "io.github.fitzyracing1/system-on-an-agent-plugin"
    assert len(server["description"]) <= 100
    package = server["packages"][0]
    assert package["registryType"] == "pypi"
    assert package["identifier"] == "system-on-an-agent"
    assert package["transport"] == {"type": "stdio"}
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"mcp-name: {server['name']}" in readme


def test_logo_png_is_square():
    data = (ROOT / "assets" / "logo.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    assert width == height >= 256
