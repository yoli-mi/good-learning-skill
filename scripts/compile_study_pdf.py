"""Compile self-contained TeX into PDF using an ASCII build name.

Some Windows TeX installations cannot create log files whose names contain
Chinese characters. Build as study.tex in a temporary directory while keeping
the delivered TeX and PDF names descriptive.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Self-contained TeX source")
    parser.add_argument("output", type=Path, help="Final PDF file")
    parser.add_argument("--compiler", choices=["xelatex", "lualatex"], default="xelatex")
    args = parser.parse_args()
    compiler = shutil.which(args.compiler)
    if compiler is None:
        raise SystemExit(f"{args.compiler} is unavailable; PDF was not created")
    if args.source.suffix.lower() != ".tex" or args.output.suffix.lower() != ".pdf":
        raise SystemExit("Expected a .tex source and .pdf output")

    with tempfile.TemporaryDirectory(prefix="good-learning-") as directory:
        build = Path(directory)
        tex = build / "study.tex"
        shutil.copyfile(args.source, tex)
        command = [compiler, "-interaction=nonstopmode", "-halt-on-error", tex.name]
        for pass_number in (1, 2):
            result = subprocess.run(
                command, cwd=build, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                errors="replace", check=False,
            )
            if result.returncode:
                raise SystemExit(
                    f"{args.compiler} pass {pass_number} failed:\n"
                    + "\n".join(result.stdout.splitlines()[-30:])
                )
        pdf = build / "study.pdf"
        if not pdf.is_file() or pdf.stat().st_size == 0:
            raise SystemExit("Compiler finished without producing a PDF")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, args.output)
        print(f"Compiled {args.output} with {args.compiler} (2 passes)")


if __name__ == "__main__":
    main()
