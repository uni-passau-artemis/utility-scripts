#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Artemis UniPassau Utility Scripts Contributors
#
# SPDX-License-Identifier: EUPL-1.2

"""
It is sometimes quite challenging to get an overview over all inline feedbacks made
across all files during assessment. This script fetches both the inline feedbacks and
file contents for a manually assessed submission and combines them into a single
Markdown-style file.

The file contents are printed to STDOUT, so in most cases you want to redirect the
output to a file.
"""

import argparse
import re
import sys
from collections.abc import Generator, Iterable
from typing import Any

import requests


class Artemis:
    def __init__(self, url: str, cookie: str) -> None:
        self._url = url
        self._cookie = cookie

    def fetch_assessment(self, submission_id: int) -> dict[str, Any]:
        headers = {"Cookie": self._cookie}
        response = requests.get(
            f"{self._url}/api/programming/programming-submissions/{submission_id}/lock",
            headers=headers,
        )
        return response.json()

    def fetch_file_content(self, participation_id: int, file_path: str) -> str:
        headers = {"Cookie": self._cookie}
        url = f"{self._url}/api/programming/repository/{participation_id}/file?file={file_path}"
        response = requests.get(url, headers=headers)
        return response.text


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = _argument_parser().parse_args(argv)

    artemis = Artemis(args.artemis_url, args.auth_cookie)
    lines = _process_submission(artemis, args.submission)

    for line in lines:
        print(line)

    return 0


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artemis-url",
        type=str,
        required=False,
        default="https://artemis.fim.uni-passau.de",
        help="The base URL of Artemis.",
    )
    parser.add_argument(
        "--auth-cookie",
        type=str,
        required=True,
        help=(
            "Artemis authentication cookie. "
            "Can be obtained from a browser that is logged in to Artemis. "
            "Format: `jwt=COOKIE_VALUE`."
        ),
    )
    parser.add_argument(
        "--submission",
        type=int,
        required=True,
        help="ID of the submission. When on the assessment page in the Artemis, is the ID in the path element after `/submissions/`.",
    )

    return parser


def _process_submission(artemis: Artemis, submission_id: int) -> Generator[str]:
    assessment = artemis.fetch_assessment(submission_id)
    participation_id = assessment["participation"]["id"]
    result = assessment["results"][0]
    feedbacks = result["feedbacks"]

    inline_feedbacks = _parse_feedbacks(feedbacks)
    file_contents = _get_file_contents(artemis, participation_id, inline_feedbacks)

    yield "# Feedbacks only"
    yield from _format_feedbacks(inline_feedbacks)
    yield ""

    yield "# Inline feedbacks"
    yield from _merge_file_content_with_feedbacks(file_contents, inline_feedbacks)


FileToLineContent = dict[str, dict[int, str]]


def _parse_feedbacks(
    feedbacks: list[dict[str, Any]],
) -> FileToLineContent:
    """
    Extracts the manual feedbacks from the given feedbacks and associates them with a
    file and line number.

    :param feedbacks: The feedbacks from the last result of the assessment.
    :return: A mapping of files to (a mapping of line numbers to the list of feedbacks
             for this line).
    """
    result: FileToLineContent = {}

    for feedback in feedbacks:
        feedback_ref_marker = feedback.get("text")
        if feedback_ref_marker is None:
            continue

        feedback_text: str = feedback["detailText"]
        file, line = _parse_feedback_ref_marker(feedback_ref_marker)

        file_feedbacks = result.get(file, {})
        file_feedbacks[line] = feedback_text
        result[file] = file_feedbacks

    return result


def _parse_feedback_ref_marker(feedback_ref: str) -> tuple[str, int]:
    # example: File src/shell/Shell.java at line 1
    ref = feedback_ref.replace("File ", "", 1)
    line_match = re.search(r"\d+$", ref)
    assert line_match is not None
    line = int(line_match.group(0))
    file = re.sub(r" at line \d+$", "", ref)

    return file, line


def _get_file_contents(
    artemis: Artemis, participation_id: int, files: Iterable[str]
) -> FileToLineContent:
    result = {}

    for file in files:
        file_content = artemis.fetch_file_content(participation_id, file)
        result[file] = {
            idx + 1: line for idx, line in enumerate(file_content.splitlines())
        }

    return result


def _format_feedbacks(inline_feedbacks: FileToLineContent) -> Generator[str]:
    for file, lines in sorted(inline_feedbacks.items()):
        yield f"## File: {file}"

        for line, line_content in sorted(lines.items()):
            for feedback_line in line_content.splitlines():
                yield f"* [{line}] {feedback_line}"

        yield ""


def _merge_file_content_with_feedbacks(
    file_contents: FileToLineContent, feedbacks: FileToLineContent
) -> Generator[str]:
    for file, lines in sorted(file_contents.items()):
        yield f"## File: {file}"
        yield "```java"

        feedback_for_file = feedbacks.get(file, {})

        for line, line_content in sorted(lines.items()):
            yield f"\t{line_content}"
            if (feedback_lines := feedback_for_file.get(line)) is not None:
                for feedback in feedback_lines.splitlines():
                    yield f"// {feedback}"

        yield "```"
        yield ""


if __name__ == "__main__":
    raise SystemExit(main())
