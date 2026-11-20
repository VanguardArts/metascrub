VERSION := 0.7.0

.PHONY: icons deb rpm flatpak cli-gui install uninstall clean

icons:
	python3 scripts/make_icons.py

deb:
	bash packaging/make_deb.sh

rpm:
	bash scripts/build-rpm.sh

flatpak:
	bash scripts/build-flatpak.sh

cli-gui:
	python -m pip install --upgrade pip pyinstaller
	pyinstaller --onefile --name metascrub-cli packaging/cli_main.py
	pyinstaller --onefile --windowed --name metascrub-gui packaging/gui_main.py

install:
	./install.sh

uninstall:
	./uninstall.sh

clean:
	rm -rf build dist *.spec
