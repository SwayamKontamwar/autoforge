"""What the model is allowed to see before it is asked to write code.

The builder sends a ranked slice of the repository with every task. The slice is
small and the repository is not, so ranking decides what the model knows -- and a
file that falls outside it may as well not exist. That failure is silent in the
worst way: the model answers with a patch that changes whatever it *was* shown,
the guardrail correctly rejects the half-finished result, and after three
attempts the task is retired as impossible. Nothing in that sequence looks like a
context bug, and nobody is watching.

Every repository here is synthetic. Asserting against the real ``app/`` would tie
these tests to whatever the bot has built so far, which is the one shape of test
this project cannot have: it passes until the bot succeeds, then fails on a clean
tree forever after.
"""

from pathlib import Path

from builder.run import _build_context, _ranked_files


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp_path


class TestContentDecidesRelevance:
    """A file is about what it contains, not only about what it is called."""

    def test_a_file_matching_only_by_contents_outranks_an_unrelated_one(
        self, tmp_path: Path
    ) -> None:
        root = _repo(
            tmp_path,
            {
                # Neither name shares a word with the task.
                "app/aaa.py": "COLOUR = 'red'\n",
                "app/zzz.py": "def expire_link(token):\n    return token\n",
            },
        )
        task = "Expire a link after its deadline passes."
        order = [str(p.relative_to(root)) for p in _ranked_files(root, task)]
        # Alphabetically aaa.py wins; only its contents can demote it.
        assert order.index("app/zzz.py") < order.index("app/aaa.py")

    def test_the_word_a_task_uses_finds_the_identifier_a_file_uses(
        self, tmp_path: Path
    ) -> None:
        """"timestamps" is about a file saying "timestamp"; "UTC" about utcnow()."""
        root = _repo(
            tmp_path,
            {
                "app/aaa.py": "LIMIT = 10\n",
                "app/bbb.py": "created = datetime.utcnow()\n",
            },
        )
        task = "Normalise created timestamps to timezone-aware UTC everywhere."
        order = [str(p.relative_to(root)) for p in _ranked_files(root, task)]
        assert order.index("app/bbb.py") < order.index("app/aaa.py")

    def test_a_file_named_by_the_task_still_leads(self, tmp_path: Path) -> None:
        """Negative control: naming a file explicitly is the strongest signal."""
        root = _repo(
            tmp_path,
            {
                "app/target.py": "X = 1\n",
                "app/other.py": "def expire(deadline, expiry, expires):\n    pass\n",
            },
        )
        task = "Rewrite app/target.py to handle expire deadline expiry expires."
        order = [str(p.relative_to(root)) for p in _ranked_files(root, task)]
        assert order[0] == "app/target.py"

    def test_ranking_is_deterministic(self, tmp_path: Path) -> None:
        """Negative control: the same repository must rank the same way twice."""
        root = _repo(
            tmp_path,
            {f"app/m{i}.py": f"VALUE = {i}\n" for i in range(12)},
        )
        task = "Add a value to the module."
        first = [str(p) for p in _ranked_files(root, task)]
        second = [str(p) for p in _ranked_files(root, task)]
        assert first == second


class TestMachineryDoesNotCrowdOutTheProduct:
    """Tests of the builder are not what the model is being asked to write."""

    def test_a_large_builder_test_does_not_displace_application_code(
        self, tmp_path: Path
    ) -> None:
        """The exact shape that hid app/storage.py from the model.

        Scoring contents is what makes this possible: a machinery test can now
        out-match the application file it is burying, because words like
        "timezone" and "utc" appear in tests about rate limiting and retries as
        readily as in the code that formats a timestamp. Size is what makes it
        fatal -- the file does not merely rank higher, it eats the budget the
        application file needed. Here the machinery file deliberately scores
        *more* content hits than the application file, so only demotion can put
        the application file in front of it.
        """
        root = _repo(
            tmp_path,
            {
                "app/storage.py": "created = datetime.utcnow()\n" * 20,
                "tests/test_machinery.py": (
                    "from builder import run\n"
                    "# timezone utc created timestamps normalise everywhere\n"
                    + "# padding\n" * 4000
                ),
            },
        )
        task = "Normalise created timestamps to timezone-aware UTC everywhere."
        order = [str(p.relative_to(root)) for p in _ranked_files(root, task)]
        assert order.index("app/storage.py") < order.index("tests/test_machinery.py")
        assert "--- app/storage.py ---" in _build_context(root, task)

    def test_machinery_is_demoted_not_discarded(self, tmp_path: Path) -> None:
        """Demoted, so a task that genuinely needs one can still reach it."""
        root = _repo(
            tmp_path,
            {
                # Scores higher on both name and contents than the app file.
                "tests/test_timezone.py": (
                    "from builder import run\n# timezone utc created timestamps\n"
                ),
                "app/thing.py": "X = 1\n",
            },
        )
        task = "Normalise created timestamps to timezone-aware UTC everywhere."
        order = [str(p.relative_to(root)) for p in _ranked_files(root, task)]
        assert set(order) == {"app/thing.py", "tests/test_timezone.py"}
        assert order.index("app/thing.py") < order.index("tests/test_timezone.py")

    def test_an_application_test_is_not_treated_as_machinery(
        self, tmp_path: Path
    ) -> None:
        """Negative control: tests of the app are ordinary files and must rank
        on merit, or the model never sees an example of how to test its work."""
        root = _repo(
            tmp_path,
            {
                "tests/test_links.py": "from app.main import app\n# expire deadline\n",
                "app/unrelated.py": "X = 1\n",
            },
        )
        task = "Expire a link after its deadline."
        order = [str(p.relative_to(root)) for p in _ranked_files(root, task)]
        assert order.index("tests/test_links.py") < order.index("app/unrelated.py")


class TestRankingSurvivesABadTree:
    """Ranking is a convenience; it must never be the thing that ends a run."""

    def test_an_unreadable_file_does_not_raise(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, {"app/fine.py": "X = 1\n"})
        (root / "app" / "broken.py").write_bytes(b"\xff\xfe\x00 not utf-8 \xc3\x28")
        order = [str(p.relative_to(root)) for p in _ranked_files(root, "anything")]
        assert "app/fine.py" in order
        assert "app/broken.py" in order

    def test_a_directory_named_like_a_module_is_skipped(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, {"app/real.py": "X = 1\n"})
        (root / "app" / "fake.py").mkdir()
        order = [str(p.relative_to(root)) for p in _ranked_files(root, "anything")]
        assert order == ["app/real.py"]

    def test_an_empty_task_still_returns_every_file(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, {"app/a.py": "X = 1\n", "tests/test_a.py": "Y = 2\n"})
        order = [str(p.relative_to(root)) for p in _ranked_files(root, "")]
        assert sorted(order) == ["app/a.py", "tests/test_a.py"]
