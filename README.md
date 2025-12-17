# Notebook Importer

A utility that allows you to import Jupyter Notebooks (`.ipynb`) directly into Python scripts as standard modules. It automatically handles conversion, caching for performance, and VS Code IntelliSense integration.

## 🎯 Why This Tool? (Requirement Checklist)

This utility is specifically engineered to solve the "Notebook Import" problem without the typical drawbacks:

* **Zero Folder Pollution:** Unlike other tools, this does not create `.py` files next to your notebooks. All generated code is tucked away in a hidden `.vscode/__export__/` directory.

* **VS Code IntelliSense:** It automatically updates your `settings.json` to include the hidden export path in `python.analysis.extraPaths`. This gives you **full autocomplete** and **jump-to-definition** for notebook functions.

* **No Code Changes:** Your notebooks remain standard `.ipynb` files. You do not need to manually convert them or change your coding style.

* **Minimal Boilerplate:** Once `import nbimport` is called, standard `import` statements work globally for all notebooks in your project.

## ✨ Features

* **Direct Imports:** Use `import my_notebook` just like a `.py` file.
* **Namespace Support:** Supports subfolder imports (e.g., `import research.data_processing`).
* **Caching:** Only re-converts notebooks when the `.ipynb` file is modified.
* **VS Code Ready:** Automatically updates workspace settings so autocomplete and jump-to-definition work seamlessly.
* **Silent & Robust:** Reports errors to `stderr` and fails gracefully if a notebook is corrupted.

## 🚀 Installation & Setup

1. Place `nbimport.py` in your project root.
2. Ensure you have the required dependency:
```bash
pip install nbconvert
```
3. In your main entry point (e.g., `main.ipynb`), simply import the loader:
```python
import nbimport
```

## 📂 Example Project Structure
```text
my_project/
├── nbimport.py           # The utility script
├── main.ipynb            # Your entry point
├── utils.ipynb           # A root-level notebook
└── research/
    └── processor.ipynb   # A subfolder notebook
```

## 🛠️ Usage
#### 1. `main.ipynb`
```python
import nbimport
import utils

print(utils.add(1, 2))
utils.run_analysis()
```

#### 2. `utils.ipynb` (Project Root)
Create a cell with this code:
```python
import nbimport # Required to enable nested notebook imports
from research.processor import run_analysis

def add(a, b):
    return a + b
```

#### 3. `research/processor.ipynb` (In a subfolder)
```python
def run_analysis():
    print("Analysis complete in the research subfolder.")
```