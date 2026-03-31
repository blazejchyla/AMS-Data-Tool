[Setup]
; --- Identity & Branding ---
AppId={{CF76F099-2A43-4F78-AB9F-8B0FC36296BD}
AppName=AMS Data Tool
AppVersion=1.0.0
AppPublisher=Błażej Chyła
AppCopyright=Copyright (C) 2026 Błażej Chyła
AppSupportURL=https://www.smc.eu/pl-pl
AppUpdatesURL=https://github.com/blazejchyla/AMS-Data-Tool

; --- Installation Folders ---
DefaultDirName={autopf}\SMC\AMS Data Tool
DefaultGroupName=AMS Data Tool
UninstallDisplayIcon={app}\AMS Data Tool.exe

; --- System Settings ---
PrivilegesRequired=admin
VersionInfoVersion=1.0.0.0
VersionInfoCompany=SMC
VersionInfoDescription=High-performance AMS Data Visualization & Conversion Tool

; --- Compression & Output ---
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=.\build\installer
OutputBaseFilename=AMS_Data_Tool_Setup_v1.0.0
SetupIconFile=.\resources\icons\app_icon.ico

[Registry]
; Double the opening bracket to escape it, but keep the closing one single
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{{CF76F099-2A43-4F78-AB9F-8B0FC36296BD}_is1"; ValueType: dword; ValueName: "NoModify"; ValueData: 1; Flags: uninsdeletevalue
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{{CF76F099-2A43-4F78-AB9F-8B0FC36296BD}_is1"; ValueType: dword; ValueName: "NoRepair"; ValueData: 1; Flags: uninsdeletevalue

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; Packages the entire PyInstaller output folder
Source: "build\dist\AMS Data Tool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AMS Data Tool"; Filename: "{app}\AMS Data Tool.exe"
Name: "{group}\Uninstall AMS Data Tool"; Filename: "{uninstallexe}"
Name: "{autodesktop}\AMS Data Tool"; Filename: "{app}\AMS Data Tool.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AMS Data Tool.exe"; Description: "Launch AMS Data Tool"; Flags: nowait postinstall skipifsilent