' launch_dashboard.vbs — 혼살림 운영 대시보드 (콘솔창 없이 실행). 바탕화면 바로가기로 사용.
' 더블클릭하면 대시보드 창이 뜹니다. 로그는 대시보드 하단 '실행 로그' 패널에 표시됩니다.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
root = fso.GetParentFolderName(scriptDir)
sh.Run "cmd /c cd /d """ & root & """ && set PYTHONPATH=src && pythonw -m dashboard.app", 0, False
