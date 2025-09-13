[Setup]
; Basic installation settings
AppName=Training Assistant
AppVersion=1.2.3
; The default installation directory name
DefaultDirName={autopf}\Training Assistant
DefaultGroupName=Training Assistant
AppPublisher=Your Name
UninstallDisplayIcon={app}\TrainingAssistant.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Output settings for the installer
OutputBaseFilename=TrainingAssistant-Installer
OutputDir=.\InstallerOutput
SetupIconFile=assets\myIcon.ico
UninstallDisplayName=Training Assistant
Uninstallable=yes

[Files]
; Source file path (your PyInstaller executable) to the destination directory
Source: "dist\TrainingAssistant.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include any other files your app might need
; Example: Source: "dist\data\settings.json"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
; Defines a task called "desktopicon" that is checked by default
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; 

[Icons]
; Creates a Start Menu folder and an application icon
Name: "{group}\Training Assistant"; Filename: "{app}\TrainingAssistant.exe"

; Creates a Desktop shortcut that depends on the 'desktopicon' task
Name: "{autodesktop}\Training Assistant"; Filename: "{app}\TrainingAssistant.exe"; Tasks: desktopicon

[Run]
; Runs the app after installation
Filename: "{app}\TrainingAssistant.exe"; Description: "Launch Training Assistant"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the entire installation directory with all its subfolders and files
Type: filesandordirs; Name: "{app}"
