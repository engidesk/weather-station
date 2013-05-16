Name "Starter Kit: Weather Station Demo <<DEMO_DOT_VERSION>>"

OutFile "starter_kit_weather_station_demo_windows_<<DEMO_UNDERSCORE_VERSION>>.exe"

XPStyle on

; The default installation directory
InstallDir "$PROGRAMFILES\Tinkerforge\Starter Kit Weather Station Demo"

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Tinkerforge\Starter Kit Weather Station Demo" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

!define DEMO_VERSION <<DEMO_DOT_VERSION>>

;--------------------------------

!macro macrouninstall

  DetailPrint "Uninstall Starter Kit: Weather Station Demo..."

  ; Remove directories used
  RMDir /R $INSTDIR

  ; Remove menu shortcuts
  Delete "$SMPROGRAMS\Tinkerforge\Starter Kit Weather Station Demo *.lnk"
  RMDir "$SMPROGRAMS\Tinkerforge"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo"
  DeleteRegKey HKLM "Software\Tinkerforge\Starter Kit Weather Station Demo"

!macroend

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

Section /o "-uninstall old demo" SEC_UNINSTALL_OLD

  !insertmacro macrouninstall

SectionEnd

;--------------------------------

; The stuff to install
Section "Install Starter Kit: Weather Station Demo ${DEMO_VERSION}"
  SectionIn RO

  DetailPrint "Install Starter Kit: Weather Station Demo..."

  SetOutPath "$INSTDIR"
  File "..\*"

  ; Write the installation path into the registry
  WriteRegStr HKLM "Software\Tinkerforge\Starter Kit Weather Station Demo" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Tinkerforge\Starter Kit Weather Station Demo" "Version" ${DEMO_VERSION}

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo" "DisplayName" "Tinkerforge Starter Kit: Weather Station Demo ${DEMO_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo" "DisplayIcon" '"$INSTDIR\demo-icon.ico"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo" "DisplayVersion" "${DEMO_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo" "Publisher" "Tinkerforge GmbH"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tinkerforge Starter Kit Weather Station Demo" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

  ; Create start menu shortcut
  SetOutPath $INSTDIR\ ; set working directory for demo.exe
  createDirectory "$SMPROGRAMS\Tinkerforge"
  createShortCut "$SMPROGRAMS\Tinkerforge\Starter Kit Weather Station Demo ${DEMO_VERSION}.lnk" "$INSTDIR\demo.exe"

SectionEnd

;--------------------------------

!include "Sections.nsh"
!include "WinVer.nsh"

Function .onInit

  ; Check to see if already installed
  ClearErrors
  ReadRegStr $0 HKLM "Software\Tinkerforge\Starter Kit Weather Station Demo" "Version"
  IfErrors not_installed ; Version not set

  SectionSetText ${SEC_UNINSTALL_OLD} "Uninstall Starter Kit Weather Station Demo $0" ; make item visible
  IntOp $0 ${SF_SELECTED} | ${SF_RO}
  SectionSetFlags ${SEC_UNINSTALL_OLD} $0

not_installed:

FunctionEnd

;--------------------------------
; Uninstaller

Section "Uninstall"

  !insertmacro macrouninstall

SectionEnd
