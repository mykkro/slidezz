#!/bin/bash

mkdir ./backend
mkdir ./backend/app.py
mkdir ./backend/ppt
mkdir ./backend/ppt/generator.py
mkdir ./backend/ppt/theme.py
mkdir ./backend/ppt/templates
mkdir ./backend/ppt/templates/title.py
mkdir ./backend/ppt/templates/conclusion.py
mkdir ./backend/ppt/templates/references.py
mkdir ./backend/models
mkdir ./backend/models/presentation.py
mkdir ./backend/exports

# Create frontend directory and its contents
mkdir ./frontend
touch ./frontend/index.html
mkdir ./frontend/css
mkdir ./frontend/js
touch ./frontend/js/api.js
touch ./frontend/js/slides.js
touch ./frontend/js/preview.js

# Create data directory and its contents
mkdir ./data
mkdir ./data/projects

# Create venv directory
mkdir ./venv

# Create requirements.txt
touch ./requirements.txt

# Create run.py
touch ./run.py
