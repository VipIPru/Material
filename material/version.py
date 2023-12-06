import os
import git


version = (0, 1, 0)


def get_branch() -> str:
    """Get current branch"""
    try:
        repo = git.Repo(
            path=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        )
        return repo.active_branch.name
    except:
        return "master"
