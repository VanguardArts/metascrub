Name:           metascrub
Version:        0.7.0
Release:        1%{?dist}
Summary:        Byte-safe audio metadata hygiene (CLI + GUI)
License:        MIT
URL:            https://github.com/VanguardArts/metascrub
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3
Requires:       python3-mutagen
Requires:       python3-pyside6

%description
Inspect, strip and normalize audio metadata (comments, lyrics, C2PA provenance,
origin URLs, cover art) without re-encoding audio. Ships the metascrub command
line tool and the metascrub-gui desktop app.

%prep
%autosetup

%build
# pure Python

%install
LIBDIR=%{buildroot}%{_prefix}/lib/metascrub
mkdir -p "$LIBDIR" %{buildroot}%{_bindir} \
         %{buildroot}%{_datadir}/applications \
         %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

cp -r src/metascrub "$LIBDIR/metascrub"
cp packaging/cli_main.py packaging/gui_main.py "$LIBDIR/"

printf '#!/bin/sh\nexec python3 %{_prefix}/lib/metascrub/cli_main.py "$@"\n' \
    > %{buildroot}%{_bindir}/metascrub
printf '#!/bin/sh\nexec python3 %{_prefix}/lib/metascrub/gui_main.py "$@"\n' \
    > %{buildroot}%{_bindir}/metascrub-gui
chmod 755 %{buildroot}%{_bindir}/metascrub %{buildroot}%{_bindir}/metascrub-gui

install -m 644 packaging/metascrub.desktop \
    %{buildroot}%{_datadir}/applications/metascrub.desktop
install -m 644 packaging/metascrub.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/metascrub.svg
for sz in 16 24 32 48 64 96 128 256 512; do
  install -Dm 644 "packaging/icons/hicolor/${sz}x${sz}/apps/metascrub.png" \
      "%{buildroot}%{_datadir}/icons/hicolor/${sz}x${sz}/apps/metascrub.png"
done

%files
%{_bindir}/metascrub
%{_bindir}/metascrub-gui
%{_prefix}/lib/metascrub/
%{_datadir}/applications/metascrub.desktop
%{_datadir}/icons/hicolor/scalable/apps/metascrub.svg
%{_datadir}/icons/hicolor/16x16/apps/metascrub.png
%{_datadir}/icons/hicolor/24x24/apps/metascrub.png
%{_datadir}/icons/hicolor/32x32/apps/metascrub.png
%{_datadir}/icons/hicolor/48x48/apps/metascrub.png
%{_datadir}/icons/hicolor/64x64/apps/metascrub.png
%{_datadir}/icons/hicolor/96x96/apps/metascrub.png
%{_datadir}/icons/hicolor/128x128/apps/metascrub.png
%{_datadir}/icons/hicolor/256x256/apps/metascrub.png
%{_datadir}/icons/hicolor/512x512/apps/metascrub.png

%changelog
* Sat Nov 21 2026 Vanguard Arts SRL <https://vanguardarts.vip/> - 0.7.0-1
* Sat Nov 21 2026 Vanguard Arts SRL <https://vanguardarts.vip/> - 0.6.0-1
- Initial RPM packaging (noarch, pure Python).
