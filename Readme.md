<!--
SPDX-FileCopyrightText: 2024 Benedikt Fein <fein@fim.uni-passau.de>

SPDX-License-Identifier: EUPL-1.2
-->

# Readme

Utility scripts used to automate some tasks that occur during the administration of the [Artemis](https://github.com/ls1intum/artemis) system and helper scripts to apply necessary fixes in case of breaking changes and major updates.

Python dependencies are managed using [uv](https://docs.astral.sh/uv/).

The `project.scripts` entry in `pyproject.toml` contains a list of scripts that can be run like `uv run script_name`.
The script itself usually accepts a `--help` option to show the possible arguments.
More detailed documentation about the script’s purpose is placed as module-level documentation in the script file itself.


## Licence

Licensed under the EUPL-1.2-or-later.
See `LICENSE` or https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12 for the full licence text.
