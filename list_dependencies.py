import ast
import os

def list_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=file_path)

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)
    
    return imports

def analyze_project(directory):
    dependencies = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                dependencies.update(list_imports(file_path))

    return dependencies

project_path = "./"
all_dependencies = analyze_project(project_path)

print("Dependencies found:")
print("\n".join(sorted(dep for dep in all_dependencies if dep)))
