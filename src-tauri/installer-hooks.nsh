; NSIS installer hooks for WinSvalinn.
; Close the running app and its Python sidecar before copying files, so an
; update never fails with "error opening file for writing" (winsvalinn-sidecar.exe
; locked by a running process).

!macro NSIS_HOOK_PREINSTALL
  nsExec::Exec 'taskkill /F /IM winsvalinn-sidecar.exe'
  nsExec::Exec 'taskkill /F /IM winsvalinn.exe'
  Sleep 500
!macroend
