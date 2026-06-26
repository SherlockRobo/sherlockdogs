Option Explicit

Dim shell, fso, scriptDir, taskRunner, kind, cmd

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
taskRunner = fso.BuildPath(scriptDir, "task_runner.ps1")

If WScript.Arguments.Count > 0 Then
  kind = WScript.Arguments(0)
Else
  kind = "local-inbox"
End If

cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File " & Chr(34) & taskRunner & Chr(34) & " -Kind " & kind
shell.Run cmd, 0, False
