#define MyAppName "Degree Compare"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Student Success Lab"
#define MyAppExeName "DegreeCompare.exe"

[Setup]
AppId={{8F7BF4A1-9A2F-4D5E-8A3E-8F40A6D9D331}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\DegreeCompare
DefaultGroupName=Degree Compare
DisableProgramGroupPage=yes
OutputDir=..\installer-output
OutputBaseFilename=DegreeCompare-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Degree Compare"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Degree Compare"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Degree Compare"; Flags: nowait postinstall skipifsilent
