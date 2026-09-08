; Inno Setup script for Norvox Reader.
;
; Deliberately configured to need NO administrator rights: installs to the
; current user's own AppData folder, not Program Files, and never triggers
; a UAC prompt. This matters on restricted machines (e.g. school PCs) where
; the user may not have admin rights at all.
;
; Version is passed in from build_release.ps1 via /DMyAppVersion=X.Y.Z so
; it always matches app/version.py — don't hardcode it here.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "Norvox Reader"
#define MyAppExeName "Norvox Reader.exe"

[Setup]
AppId={{B6E2C6B0-6C0B-4B3D-9C0A-6E9F6C7B9A1E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Distracted
AppPublisherURL=https://github.com/DistractibleD/norvox-reader
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=installer_output
OutputBaseFilename=NorvoxReaderSetup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\Norvox Reader\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
