#!/usr/bin/env python
# coding: utf-8

# no fancy syntax here
# all for easier debugging and compatibility with older Python versions

DEBUG_MODE = False

UPDATE_VSCODE_SETTINGS = True
UPDATE_GITIGNORE = True

import os, sys
import inspect
from pathlib import Path

try:
    base_dir = os.path.dirname(__file__)
except NameError:
    base_dir = os.getcwd()

base_dir = os.path.realpath(base_dir)

EXPORT_DIR = Path(base_dir, ".vscode", ".export").as_posix()
VSCODE_SETTINGS_PATH = Path(base_dir, ".vscode", "settings.json").as_posix()
EXTRA_PATHS_KEY = "python.analysis.extraPaths"
GITIGNORE_PATH = Path(base_dir, ".gitignore").as_posix()

if DEBUG_MODE:
    print(f"EXPORT_DIR: {EXPORT_DIR}")
    print(f"VSCODE_SETTINGS_PATH: {VSCODE_SETTINGS_PATH}")
    print(f"GITIGNORE_PATH: {GITIGNORE_PATH}")


def update_vscode_settings():
    import json

    try:
        target_path = Path(EXPORT_DIR).as_posix()

        settings = {}
        if os.path.exists(VSCODE_SETTINGS_PATH):
            with open(VSCODE_SETTINGS_PATH, "r", encoding="utf-8") as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError:
                    settings = {}

        extra_paths = settings.get(EXTRA_PATHS_KEY, [])
        if not isinstance(extra_paths, list):
            extra_paths = []

        if any(Path(p).as_posix() == target_path for p in extra_paths):
            return

        extra_paths.append(target_path)
        settings[EXTRA_PATHS_KEY] = extra_paths

        os.makedirs(os.path.dirname(VSCODE_SETTINGS_PATH), exist_ok=True)
        with open(VSCODE_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

    except Exception as e:
        print(
            f"ERROR: Failed to update VS Code settings at {VSCODE_SETTINGS_PATH}: {e}",
            file=sys.stderr,
        )

    if DEBUG_MODE:
        print(f"Updated VS Code settings at {VSCODE_SETTINGS_PATH} with {target_path}")


def update_gitignore():
    try:
        path = Path(os.path.relpath(EXPORT_DIR, base_dir)).as_posix()

        lines = []
        if os.path.exists(GITIGNORE_PATH):
            with open(GITIGNORE_PATH, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f]

            if path in lines or path + "/" in lines:
                return

        with open(GITIGNORE_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n# Notebook Interceptor Export Cache\n{path}/\n")
    except Exception as e:
        print(
            f"ERROR: Failed to update .gitignore at {GITIGNORE_PATH}: {e}",
            file=sys.stderr,
        )

    if DEBUG_MODE:
        print(f"Updated .gitignore at {GITIGNORE_PATH} with {path}/")


def ipynb_to_source(ipynb_path: str) -> str:
    from nbconvert.exporters import PythonExporter

    exporter = PythonExporter()
    exporter.exclude_input_prompt = True

    source, _ = exporter.from_filename(ipynb_path)

    if DEBUG_MODE:
        print(f"Converted {ipynb_path} to <str len={len(source)}>")

    return source


def ipynb_to_py(ipynb_path: str, py_path: str):
    os.makedirs(os.path.dirname(py_path), exist_ok=True)

    with open(py_path, "w", encoding="utf-8") as f:
        f.write(ipynb_to_source(ipynb_path))

    if DEBUG_MODE:
        print(f"Exported {ipynb_path} to {py_path}")


def in_subdir(child: str, parent: str) -> bool:
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def load_spec(fullname: str, path: str):
    from importlib.util import spec_from_file_location
    from importlib.machinery import SourceFileLoader

    return spec_from_file_location(
        fullname,
        path,
        loader=SourceFileLoader(fullname, path),
    )


class ImportInterceptor:
    def find_spec(self, fullname: str, path, target=None):
        module_parts = fullname.split(".")
        module_name = module_parts[-1]

        if DEBUG_MODE:
            print(f"Attempting to import '{fullname}' with path: {path}")

        # only handle those imports that are in the same directory or subdirectories of the base_dir

        if path is None:
            current_cwd = os.path.realpath(os.getcwd())
            path = [current_cwd, base_dir]

            try:
                for frame in inspect.stack():
                    filename = frame.filename

                    if not os.path.isabs(filename):
                        continue

                    if DEBUG_MODE:
                        print(f"Inspecting frame path: {filename}")

                    if in_subdir(filename, EXPORT_DIR):
                        dir_path = os.path.dirname(filename)
                        rel_path = os.path.relpath(dir_path, EXPORT_DIR)

                        actual_dir = os.path.abspath(os.path.join(base_dir, rel_path))
                        path.insert(0, actual_dir)

                        if DEBUG_MODE:
                            print(f"Found frame in EXPORT_DIR: {filename}")
                            print(f"Adding {actual_dir} to search paths")

                        break
            except:
                pass

        path = list(dict.fromkeys(path))

        if DEBUG_MODE:
            print(f"Search paths for '{fullname}': {path}")
            print("=" * 40)
            print()

        for dir_path in path:
            if DEBUG_MODE:
                print(f"Checking directory: {dir_path}")

            if not in_subdir(dir_path, base_dir):
                if DEBUG_MODE:
                    print(f"Skipping directory outside base_dir: {dir_path}")
                continue

            file_path = os.path.join(dir_path, f"{module_name}.ipynb")
            file_path = os.path.normpath(file_path)

            if DEBUG_MODE:
                print(f"Looking for notebook at: {file_path}")

            if not os.path.exists(file_path):
                if DEBUG_MODE:
                    print(f"No notebook found at: {file_path}")
                continue

            if DEBUG_MODE:
                print(f"Found notebook for '{fullname}' at: {file_path}")

            export_path = os.path.join(EXPORT_DIR, *module_parts) + ".py"

            use_cache = os.path.exists(export_path) and os.path.getmtime(
                export_path
            ) >= os.path.getmtime(file_path)

            if DEBUG_MODE:
                print(f"Export path for '{fullname}': {export_path}")
                print(f"Cache exists: {os.path.exists(export_path)}")
                print(f"Notebook modified time: {os.path.getmtime(file_path)}")
                print(f"Cache modified time: {os.path.getmtime(export_path)}")
                print(f"Using cache: {use_cache}")
                print()

            if not use_cache:
                ipynb_to_py(file_path, export_path)

            return load_spec(fullname, export_path)

        return None


if UPDATE_VSCODE_SETTINGS:
    update_vscode_settings()
    
if UPDATE_GITIGNORE:
    update_gitignore()

if not any(isinstance(f, ImportInterceptor) for f in sys.meta_path):
    sys.meta_path.append(ImportInterceptor())
