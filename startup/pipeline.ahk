#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
#SingleInstance Force ; Hides popup asking to replace running ahk with new ahk

;---------- Start script ----------

root := A_ScriptDir "\.."

Run, cmd
Sleep, 2000
Send, cd %root%/transfer/automatic{Enter}
Send, cls{Enter}
Send, python .\server.py

Send ^+t
Sleep, 500
Send, cd %root%/process{Enter}
Send, cls{Enter}
Send, python .\synchronize.py

Send ^+t
Sleep, 500
Send, cd %root%/process{Enter}
Send, cls{Enter}
Send, python .\analyze.py

Send ^+t
Sleep, 500
Send, cd %root%/process{Enter}
Send, cls{Enter}
Send, python .\visualize.py