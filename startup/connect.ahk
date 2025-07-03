#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
#SingleInstance Force ; Hides popup asking to replace running ahk with new ahk

;---------- Start script ----------

ReadEnvValue(key) {
    envPath := A_ScriptDir "\..\.env"
    FileRead, content, %envPath%

    Loop, Parse, content, `n, `r
    {
        line := Trim(A_LoopField)
        if (RegExMatch(line, "^" . key . "=")) {
            return SubStr(line, InStr(line, "=") + 1)
        }
    }
    return ""
}


user := ReadEnvValue("USER")
pass := ReadEnvValue("PASS")
host1 := ReadEnvValue("HOST1")
host2 := ReadEnvValue("HOST2")
host3 := ReadEnvValue("HOST3")

RunSSH(host, command) {
    global user, pass
    Send, ssh %user%@%host%{Enter}
    Sleep, 1500
    Send, %pass%{Enter}
    Sleep, 1000
    Send, cd /home/hydro/Downloads/recordingModule/{Enter}
    Send, rm -f recordings/*{Enter}
    Send, clear{Enter}
    Send, ifconfig wlan0 `| grep " inet " {Enter}
    Sleep 200
    Send, %command%
}

Run, cmd
Sleep, 2000
RunSSH(host1, "./pr 1 demo 1")
Send ^+t
Sleep, 500
RunSSH(host1, "python client.py")

Run, cmd
Sleep, 2000
RunSSH(host2, "./pr 2 demo 0")
Send ^+t
Sleep, 500
RunSSH(host2, "python client.py")

Run, cmd
Sleep, 2000
RunSSH(host3, "./pr 3 demo 0")
Send ^+t
Sleep, 500
RunSSH(host3, "python client.py")
