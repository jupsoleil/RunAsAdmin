@schtasks /delete /tn "UpgradeManagedSoftware" /f
@schtasks /create /XML "C:\Program Files\LET\UpgradeManagedSoftware\UpgradeManagedSoftware.xml" /tn "UpgradeManagedSoftware"