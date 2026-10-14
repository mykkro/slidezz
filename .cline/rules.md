Assume the workspace root is the Git repository root.

When creating project configuration files such as:
- .gitignore
- README.md
- pyproject.toml
- requirements.txt
- .editorconfig
- .gitattributes

always place them in the repository root unless explicitly instructed otherwise.

Never create project-level files inside .venv, build, dist, or cache directories.