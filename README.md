# Upgrade Managed Software

## Description

This project allows to update and check managed software installations.

## Installation

1. Create a HelperAdmin domain user with admin rights on all workstations.
1. Create two batch scripts:
   * UpgradeManagedSoftware.cmd launching the python script UpgradeManagedSoftware.py
   * UpgradeManagedSoftwareTaskScheduler.cmd to delete/create the UpgradeManagedSoftware task
1. **REPEAT THIS STEP WHENEVER THE CMD IS CHANGED!** 
 To prevent terminal windows popping up, use the Windows built-in IExpress.exe
 utility to build a silently running .EXE out of these two batch files (see https://superuser.com/questions/62525/run-a-batch-file-in-a-completely-hidden-way). See the included SED files (they are plain text) for more info. 
 When using IExpress make sure you do the following:
   * select "extract files and run an installation command"
   * type a title for the package
   * select "no prompt"
   * select "do not display a license"
   * add only UpgradeManagedSoftware.cmd to the package
   * fil out "UpgradeManagedSoftware.cmd" as install program to launch (no post-install command)
   * select hidden for "show window" 
   * select "no message"
   * as target path and filename, fill out UpgradeManagedSoftware.exe and select "hide extraction progress"
   * select "no restart"
   * save as UpgradeManagedSoftware.SED
   * the package should be created - the resulting UpgradeManagedSoftware.exe will start the python script without terminal running.
 
1. Create and export a scheduled task to launch UpgradeManagedSoftware.xus - from the exported xml, 
remove the author ID so a non-privileged account is allowed to import the task using schtasks.

For the tasks below a working [WPKG](https://wpkg.org/) installation can be used; see WPKG-UpgradeManagedSoftware.xml for details.
1. Install RunAsRob as a service
1. Copy all UpgradeManagedSoftware files to a folder in Program Files 
   (to prevent users tinkering with them), eg "C:\Program Files\LET\UpgradeManagedSoftware".   
1. Use [RunAsRob](https://robotronic.de/runasserviceen.html) to create an encrypted 
   shortcut UpgradeManagedSoftware.xus to UpgradeManagedSoftware.EXE, using HelperAdmin's credentials, 
   but check to run using the service account.
1. Copy UpgradeManagedSoftwareTaskScheduler.EXE into the folder C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup
   to delete/create the scheduled task for any logged-on user.
1. Create a shortcut to UpgradeManagedSoftware.xus and set its icon.  Copy the shortcut to all users's start menu.

1. Using WPKG,  
1. For automatic installation, you need to have a working wpkg installation 
using wpkg-gp.
* -   No need for wpkg-gp.


### Configuration options

All options are configured in UpgradeManagedSoftware.py (start of the file).

### Updating

Change the VERSION variable of the package in WPKG-UpgradeManagedSoftware.xml . 

### Localization

Translations need to be defined at the start of UpgradeManagedSoftware.py:

```
SUPPORTED_LANGUAGES = ['fr','nl','sk']
```

To generate the pot file:

```
C:\Python37\python C:\Python37\Tools\i18n\pygettext.py -d UpgradeManagedSoftware -o locales/UpgradeManagedSoftware.pot UpgradeManagedSoftware.py
```

We need gettext tools to update po files from pot files.  On Windows, install Ubuntu 18.04 via de windows store.  Launch bash and install the prerequisites:

```
sudo apt install python3 gettext
```

Update po's with pot: (requires gettext utilities)

```
bash
python3 pot2po.py fr nl sk
```

Edit the po's using [poEdit](https://poedit.net/) .  You can create a catalog pointing to the 'locales' folder for easy managing the translations.
poEdit will compile the po's into mo's.
