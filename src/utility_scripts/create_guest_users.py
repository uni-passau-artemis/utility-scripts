#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Artemis UniPassau Utility Scripts Contributors
#
# SPDX-License-Identifier: EUPL-1.2

"""
At the University of Passau, we occasionally want to add guest users for experiments to
our system. From the faculty admins, we get a list with logins in the form
```
guest1 password
guest2 password
```

This script creates the corresponding user accounts in Artemis.
"""

import argparse
import dataclasses
import logging
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any, Final

import requests

_log: Final[logging.Logger] = logging.getLogger(__name__)
CreateUserResponse = dict[str, Any]


@dataclasses.dataclass(frozen=True)
class User:
    username: str
    password: str

    @property
    def guest_id(self) -> int:
        return int(self.username.replace("guest", ""))


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = _argument_parser().parse_args(argv)

    users = _read_users(args.users_file)
    for user in users:
        created_user = _create_user(
            args.artemis_url, args.auth_cookie, args.email_domain, user
        )
        _log.info("Created user %s with id %d.", user.username, created_user["id"])

    return 0


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artemis-url", type=str, required=True, help="The base URL of Artemis."
    )
    parser.add_argument(
        "--auth-cookie",
        type=str,
        required=True,
        help="Artemis authentication cookie. Can be obtained from a browser that is logged in to Artemis.",
    )
    parser.add_argument(
        "--users-file",
        type=Path,
        required=True,
        help="Path to the file that contains the username/password pairs.",
    )
    parser.add_argument(
        "--email-domain",
        type=str,
        required=True,
        help="Part after the '@' of the user emails.",
    )

    return parser


def _read_users(file: Path) -> Generator[User]:
    with file.open(mode="r", encoding="utf-8") as f:
        for line in f:
            username, password = line.strip().split()
            yield User(username.strip(), password.strip())


def _create_user(
    artemis_url: str, cookie: str, email_domain: str, user: User
) -> CreateUserResponse:
    data = {
        "authorities": ["ROLE_USER"],
        "login": user.username,
        "email": f"{user.username}@{email_domain}",
        "firstName": "Guest",
        "lastName": f"{user.guest_id}",
        "langKey": "en",
        "guidedTourSettings": [],
        "groups": [],
        "internal": True,
        "password": user.password,
    }
    headers = {"Cookie": cookie}
    response = requests.post(
        f"{artemis_url}/api/admin/users", json=data, headers=headers
    )
    return response.json()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main(sys.argv[1:]))
