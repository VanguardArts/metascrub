; Inno Setup script: metascrub Windows installer (GUI + CLI).
; Build:  iscc /DAppVersion=0.2.1 packaging\metascrub.iss
#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{7E6A9C2E-3F0B-4A1D-9E2C-5B8F1A6D4C70}
AppName=metascrub
AppVersion={#AppVersion}
AppPublisher=metascrub contributors
AppPublisherURL=https://github.com/VanguardArts/metascrub
AppSupportURL=https://github.com/VanguardArts/metascrub/issues
DefaultDirName={autopf}\metascrub
DefaultGroupName=metascrub
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=metascrub-setup-windows
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\metascrub-gui.exe

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
    GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\metascrub-gui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\metascrub-cli.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\metascrub"; Filename: "{app}\metascrub-gui.exe"
Name: "{autodesktop}\metascrub"; Filename: "{app}\metascrub-gui.exe"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\metascrub-gui.exe"; Description: "Launch metascrub"; \
    Flags: nowait postinstall skipifsilent
