;A simple nsis script file: osminstall.nsi

!include "MUI.nsh"
!include "StrFunc.nsh"
!include "Library.nsh"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

!define NAME "LuoYunCloud OSM"
Icon "osm.ico"

outfile "LuoYunCloud-OSM-1.0.exe"
installDir "C:\Program Files"
RequestExecutionLevel admin

; a test of background
BGGradient off

Section
SetOutPath "$INSTDIR\${NAME}"
; install KillProcDLL, http://nsis.sourceforge.net/KillProcDLL_plug-in
;KillProcDLL::KillProc "osmwinserv.exe"
File osmwinserv.exe
File w9xpopen.exe
File *.dll
File *.pyd
File library.zip
File osm.ico
File README.zh_CN.markdown
File license.txt
SectionEnd

Section "Uninstall"
;KillProcDLL::KillProc "osmwinserv.exe"
ExecWait '"$INSTDIR\osmwinserv.exe" -remove'
RMDir /r "$INSTDIR"
DeleteRegKey HKLM "Software\${NAME}"
DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}"
;SimpleSC::StopService "MSIServer"
SectionEnd

; post install
Function .onInstSuccess
ExecWait '"$INSTDIR\${NAME}\osmwinserv.exe" -install -interactive -auto'
WriteRegStr HKLM "Software\${NAME}" "" "$INSTDIR"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayName" "${NAME}"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "UninstallString" '"$INSTDIR\${NAME}\uninst.exe"'
WriteUninstaller "$INSTDIR\${NAME}\uninst.exe" 
FunctionEnd
