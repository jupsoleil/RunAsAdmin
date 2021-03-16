set PKG_SOURCE=C:\MySandbox\LCGIT\RunAsAdmin
set PKG_DESTINATION=\\172.16.15.33\install\RunasRob\UpgradeManagedSoftware
set LOCAL_DESTINATION=C:\Program Files\LET\UpgradeManagedSoftware
set WPKG_PACKAGE=\\172.16.15.33\install\packages\LET_RunAsRob.xml
set EDITOR=C:\Tools\Notepad++\notepad++.exe

copy "%PKG_SOURCE%\pot2po.py" "%PKG_DESTINATION%"
xcopy /r /h /c /y "%PKG_SOURCE%\UpgradeManagedSoftware*.*" "%PKG_DESTINATION%"
xcopy /r /e /h /s /c /y "%PKG_SOURCE%\Locales" "%PKG_DESTINATION%"
:: launch notepad to update the timestamp of this wpkg package file so the new release gets installed at next wpkg run
"%EDITOR%" "%WPKG_PACKAGE%"
goto DONE

:: below only for tests
set PKG_SOURCE=C:\MySandbox\LCGIT\RunAsAdmin
set LOCAL_DESTINATION=C:\Program Files\LET\UpgradeManagedSoftware
copy /y "%PKG_SOURCE%\UpgradeManagedSoftware.py" "%LOCAL_DESTINATION%"
copy /y "%PKG_SOURCE%\UpgradeManagedSoftware.exe" "%LOCAL_DESTINATION%"
copy /y "%PKG_SOURCE%\UpgradeManagedSoftware.cmd" "%LOCAL_DESTINATION%"
copy /y "%PKG_SOURCE%\UpgradeManagedSoftware.xml" "%LOCAL_DESTINATION%"

:DONE