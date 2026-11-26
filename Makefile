# Malayalam Games Build & Asset Pipeline
# Game Concept by "Kududu & Kukudu"
# Licensed under GNU GPLv3

PYTHON ?= python3
APP_NAME ?= MalayalamGames
ENTRY_SCRIPT ?= malayalam_games.py

.PHONY: help audio audio-force validate build clean

help:
	@echo "Targets:"
	@echo "  make validate     - Validate assets/csv/*.csv and check audio assets"
	@echo "  make audio        - Generate missing MP3 files in assets/audio"
	@echo "  make audio-force  - Regenerate all MP3 files in assets/audio"
	@echo "  make build        - Validate CSVs, ensure audio, and build macOS app via PyInstaller"
	@echo "  make clean        - Remove PyInstaller build and dist artifacts"

validate:
	$(PYTHON) validate_csvs.py

audio:
	$(PYTHON) generate_audio.py

audio-force:
	$(PYTHON) generate_audio.py --overwrite

build: validate audio
	$(PYTHON) -m PyInstaller \
		--noconfirm \
		--windowed \
		--name "$(APP_NAME)" \
		--add-data "assets/csv:assets/csv" \
		--add-data "assets/audio:assets/audio" \
		--add-data "assets/fonts:assets/fonts" \
		$(ENTRY_SCRIPT)

clean:
	rm -rf build dist "$(APP_NAME).spec"