import os
from pathlib import Path

from app.toolkit.files import human_path, split_extension


def test_human_path_replaces_home_with_tilde():
    home = Path.home()
    # Construct a path inside the home directory
    p = home / "projects" / "myapp" / "main.py"
    result = human_path(str(p))
    # Expected representation starts with "~" and uses the relative part
    expected = os.path.join("~", "projects", "myapp", "main.py")
    assert result == expected


def test_human_path_shortens_long_path_with_ellipsis():
    # A deliberately long path that exceeds the default max_len (30)
    long_path = os.path.join(
        "/", "a", "very", "long", "path", "that", "exceeds", "the", "limit", "file.txt"
    )
    max_len = 20
    result = human_path(long_path, max_len=max_len)
    # Compute the expected shortened form using the same algorithm
    keep_start = (max_len - 1) // 2
    keep_end = max_len - 1 - keep_start
    expected = long_path[:keep_start] + "…" + long_path[-keep_end:]
    assert result == expected


def test_human_path_edge_cases():
    # Zero length limit returns empty string
    assert human_path("anything", max_len=0) == ""
    # Max length of 1 returns only the ellipsis
    assert human_path("anything", max_len=1) == "…"
    # Path not under home should remain unchanged if short enough
    short = "/tmp/file.txt"
    assert human_path(short, max_len=100) == short


def test_split_extension_basic():
    assert split_extension("file.txt") == ("file", ".txt")
    assert split_extension("archive.tar.gz") == ("archive.tar", ".gz")
    assert split_extension("folder.") == ("folder.", "")
    assert split_extension(".bashrc") == (".bashrc", "")


def test_split_extension_edge_cases():
    # Empty string yields empty stem and extension
    assert split_extension("") == ("", "")
    # Filename with multiple leading dots
    assert split_extension("..config") == ("..config", "")
    # No extension
    assert split_extension("README") == ("README", "")
