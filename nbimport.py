#!/usr/bin/env python
# coding: utf-8

import os, sys
import json
import importlib
import importlib.util
import importlib.machinery
from nbconvert.exporters import PythonExporter

EXPORT_DIR = os.path.join(".", ".vscode", "__export__")
VSCODE_SETTINGS_PATH = os.path.join(".", ".vscode", "settings.json")
EXTRA_PATHS_KEY = "python.analysis.extraPaths"


class ImportInterceptor:
    def find_spec(self, fullname: str, path=None, target=None):
        module_name = fullname.split(".")[-1]
        search_dirs = path if path is not None else [os.path.abspath(os.curdir)]

        for entry in search_dirs:
            file_path = os.path.join(entry, f"{module_name}.ipynb")

            if os.path.exists(file_path):
                # print("FOUND", fullname, file_path, entry)
                export_path = os.path.join(EXPORT_DIR, *fullname.split(".")) + ".py"

                is_cache_valid = False

                if os.path.exists(export_path):
                    ipynb_mtime = os.path.getmtime(file_path)
                    py_mtime = os.path.getmtime(export_path)

                    if py_mtime >= ipynb_mtime:
                        is_cache_valid = True

                if not is_cache_valid:
                    try:
                        # print("CONVERTING", fullname)
                        os.makedirs(os.path.dirname(export_path), exist_ok=True)
                        with open(export_path, "w", encoding="utf-8") as f:
                            f.write(convert_notebook_to_source(file_path))
                    except Exception as e:
                        print(
                            f"ERROR: Failed to convert/load notebook '{file_path}': {e}",
                            file=sys.stderr,
                        )
                        break

                return importlib.util.spec_from_file_location(
                    fullname,
                    export_path,
                    loader=importlib.machinery.SourceFileLoader(fullname, export_path),
                )

        return None


def update_vscode_settings():
    try:
        with open(VSCODE_SETTINGS_PATH, "r") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}
    except Exception as e:
        print(
            f"WARNING: An unexpected error occurred while reading VS Code settings: {e}",
            file=sys.stderr,
        )
        return

    extra_paths: list = settings.get(EXTRA_PATHS_KEY, [])

    if EXPORT_DIR not in extra_paths:
        extra_paths.append(EXPORT_DIR)
        settings[EXTRA_PATHS_KEY] = extra_paths

        os.makedirs(os.path.dirname(VSCODE_SETTINGS_PATH), exist_ok=True)
        try:
            with open(VSCODE_SETTINGS_PATH, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(
                f"ERROR: Failed to write VS Code settings to {VSCODE_SETTINGS_PATH}: {e}",
                file=sys.stderr,
            )


def convert_notebook_to_source(input_notebook_path):
    exporter = PythonExporter(config={"prompt_config": {"include_prompt": False}})
    content, _ = exporter.from_filename(input_notebook_path)
    return content


if not any(isinstance(f, ImportInterceptor) for f in sys.meta_path):
    update_vscode_settings()
    sys.meta_path.insert(0, ImportInterceptor())
