$ErrorActionPreference = "Stop"
Unregister-ScheduledTask -TaskName "SherlockdogsLocalInbox" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "SherlockdogsCodexRunner" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "SherlockdogsWindowsWeChatInbox" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Sherlockdogs Scheduled Tasks removed. User data and config were kept."
