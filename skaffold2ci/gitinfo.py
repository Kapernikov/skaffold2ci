from pathlib import PosixPath
def is_submodule(main_project_path: PosixPath, submodule_path: PosixPath) -> bool:
    """Check if a submodule is a submodule of the main project"""
    while submodule_path != main_project_path:
        git_folder = submodule_path / ".git"
        if git_folder.exists():
            return True
        submodule_path = submodule_path.parent
    return False


def contains_git_folder(path: PosixPath) -> bool:
    """Check if a path contains a .git folder"""
    for p in path.rglob(".git"):
        return True
    return False

def should_clone_recursive(main_project_path: PosixPath, context: PosixPath) -> bool:
    """Check if a submodule should be cloned recursively"""
    if is_submodule(main_project_path, context):
        return True
    if contains_git_folder(context):
        return True
    return False
