"""Run using the installed wheel's interpreter, outside the source checkout."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="studytrail-wheel-") as temp:
        work = Path(temp)
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("GROQ_", "STUDYTRAIL_")) and key != "PYTHONPATH"
        }
        env["STUDYTRAIL_HOME"] = str(work / "personal")
        env["PYTHONIOENCODING"] = "utf-8"
        command = Path(sys.executable).parent / (
            "studytrails.exe" if os.name == "nt" else "studytrails"
        )

        def run(args, answers=""):
            result = subprocess.run(
                [str(command), *args],
                input=answers,
                text=True,
                encoding="utf-8",
                capture_output=True,
                cwd=work,
                env=env,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            return result.stdout

        assert "Welcome to StudyTrail" in run([], "n\n0\n")
        assert "API key: not configured" in run(["doctor"])
        assert "100.0%" in run(["demo"], "b\nc\nd\n")
        assert "Completed quizzes: 1" in run(["scores", "--demo"])
        assert "No completed quizzes" in run(["scores"])
        assert "python/" in run(["notes", "loops", "--subject", "python"])
        run(["notes-add"], "1\nbiology\ncells\nMitochondria produce ATP.\n.done\n")
        assert "Mitochondria" in run(["notes", "mitochondria", "--subject", "biology"])
        assert "No matching notes" in run(["notes", "mitochondria", "--subject", "java"])
        # Exercise configuration without touching the real credential store or network.
        env["STUDYTRAIL_API_KEY"] = "fake-install-test-key"
        run(["config"], "1\nhttps://example.invalid/v1\nfake-tool-model\nn\n")
        doctor = run(["doctor"])
        assert "fake-tool-model" in doctor and "fake-install-test-key" not in doctor
        assert "fake-install-test-key" not in (work / "personal/config.json").read_text()
        print(
            "Installed-wheel checks passed: menu, demo, progress, notes, setup, and secret masking."
        )


if __name__ == "__main__":
    main()
