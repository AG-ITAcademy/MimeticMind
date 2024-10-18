import ast
import os

def find_imported_class(folder_path, module_name, class_name):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read(), filename=file)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ImportFrom) and node.module == module_name:
                                    for alias in node.names:
                                        if alias.name == class_name:
                                            print(f"Class '{class_name}' imported from '{module_name}' in {file_path}")
                        except SyntaxError:
                            print(f"Skipping file due to syntax error: {file_path}")
                except (UnicodeDecodeError, FileNotFoundError):
                    print(f"Skipping file due to encoding or file error: {file_path}")

# Example usage
find_imported_class("X:/_PROIECTE/__MimeticMind/_repo", "filter_utils.py", "FilterForm")