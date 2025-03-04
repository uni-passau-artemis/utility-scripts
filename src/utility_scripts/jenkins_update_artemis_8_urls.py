#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Artemis UniPassau Utility Scripts Contributors
#
# SPDX-License-Identifier: EUPL-1.2

"""
Artemis changed the API endpoints for the whole API in release 8.0.0. This also
affects the endpoints Jenkins uses to send the results back to Artemis. This script
iterates over all Jenkins jobs and replaces old URLs with the new schema.

Related PRs:

- https://github.com/ls1intum/Artemis/pull/10416
- https://github.com/ls1intum/Artemis/pull/10433
"""

import argparse
import logging
import re
import sys
from typing import Final

import jenkins

_log: Final[logging.Logger] = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = _argument_parser().parse_args(argv)
    _update_jobs(
        args.jenkins_url, args.jenkins_user, args.password, dry_run=args.dry_run
    )

    return 0


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--jenkins-url", type=str, required=True, help="The base URL of Jenkins."
    )
    parser.add_argument(
        "--jenkins-user",
        type=str,
        required=True,
        help="Jenkins username to access the Jenkins API with.",
    )
    parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="Password of access token to access the Jenkins API with.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the planned changes without applying them.",
    )

    return parser


def _update_jobs(
    jenkins_url: str, username: str, password: str, *, dry_run: bool = True
) -> None:
    server = jenkins.Jenkins(jenkins_url, username=username, password=password)

    jobs = server.get_jobs(folder_depth=2)

    for job in jobs:
        job_name = job["fullname"]

        _log.info("Updating job %s", job_name)
        new_config = _update_job_xml(server.get_job_config(job_name))
        if dry_run:
            _log.info("New config would be:\n%s", new_config)
        else:
            server.reconfig_job(job_name, new_config)


def _update_job_xml(job_config_xml: str) -> str:
    new_xml = job_config_xml.replace(
        "/api/public/programming-exercises/new-result",
        "/api/programming/public/programming-exercises/new-result",
    ).replace(
        "/api/public/athena/programming-exercises/",
        "/api/athena/public/programming-exercises/",
    )
    new_xml = re.sub(
        r"/api/public/programming-exercises/(?P<exerciseId>[0-9]+)/build-plan",
        r"/api/programming/public/programming-exercises/\g<exerciseId>/build-plan",
        new_xml,
    )
    return new_xml


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main(sys.argv[1:]))
