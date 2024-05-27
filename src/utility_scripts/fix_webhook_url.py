#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Artemis UniPassau Utility Scripts Contributors
#
# SPDX-License-Identifier: EUPL-1.2

"""
Artemis changed the webhook-URL that is used by GitLab to notify Artemis about
new commits from
`api/programming-submissions/{ID}`
to
`api/public/programming-submissions/{ID}`.

A migration should have been applied that changed the URL for all already
existing exercises, but this did not seem to work (for some repositories?) in
our case.

This script updates the webhook-URL for all repositories in GitLab.
"""
import argparse
import logging
import re
import sys

import gitlab
from gitlab.v4.objects import Project, ProjectHook


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = _argument_parser().parse_args(argv)

    artemis_base_url = args.artemis_base_url.rstrip("/")
    secret_token = args.secret_token

    gl = gitlab.Gitlab(args.gitlab_url, private_token=args.gitlab_api_token)
    for project in gl.projects.list(iterator=True):
        assert isinstance(project, Project)
        _update_hook(project, artemis_base_url, secret_token)

    return 0


def _update_hook(project: Project, artemis_base_url: str, secret_token: str) -> None:
    for hook in project.hooks.list(iterator=True):
        assert isinstance(hook, ProjectHook)
        if not _has_old_url(hook, artemis_base_url):
            continue

        submission_id = _get_submission_id(hook)
        project.hooks.create(
            {
                "url": f"{artemis_base_url}/api/public/programming-submissions/{submission_id}",
                "push_events": True,
                "enable_ssl_verification": False,
                "token": secret_token,
            }
        )

        # delete old hook only after new one was successfully created to be able
        # to try again if there was an error during creation
        hook.delete()

        logging.info("Updated webhook for project %s.", project.path_with_namespace)

        break


def _has_old_url(hook: ProjectHook, artemis_base_url: str) -> bool:
    regex = re.compile(f"{artemis_base_url}/api/programming-submissions/\\d+")
    return regex.fullmatch(hook.url) is not None


def _get_submission_id(hook: ProjectHook) -> int:
    return hook.url.split("/")[-1]


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artemis-base-url", type=str, required=True, help="The base URL of Artemis."
    )
    parser.add_argument(
        "--gitlab-url", type=str, required=True, help="The base URL of GitLab."
    )
    parser.add_argument(
        "--gitlab-api-token",
        type=str,
        required=True,
        help="API token used to access the GitLab API in this script.",
    )
    parser.add_argument(
        "--secret-token",
        type=str,
        help="Secret token that is sent by GitLab as part of the webhook POST request to Artemis.",
    )

    return parser


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main(sys.argv[1:]))
