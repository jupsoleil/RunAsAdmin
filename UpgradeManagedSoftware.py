# -*- coding: utf-8 -*-

import queue
import tkinter as tk
from tkinter import messagebox
import threading
import random
import ctypes
import sys
import socket
import re
#import subprocess
import json
import locale
import smtplib
import gettext
import time
#import os
import subprocess

# Define global variables
# Script version number
VERSION = "v1.8 (202011301506)"

# Localization - needed also for some variables defined below - see README.md for instructions
# Localization - provided languages
SUPPORTED_LANGUAGES = ['fr', 'nl', 'sk']

# Initialize localization
gettext.install("UpgradeManagedSoftware")
locale_language_code, locale_encoding = locale.getdefaultlocale()
locale_language = locale_language_code[:2]
LANGUAGE = locale_language
if LANGUAGE in SUPPORTED_LANGUAGES:
    lang = gettext.translation('UpgradeManagedSoftware', localedir='locales', languages=[LANGUAGE])
    lang.install()
    _ = lang.gettext

def process_exists(process_name):
    call = 'TASKLIST'
    output = subprocess.check_output(call).decode()
    lines = output.strip().split('\r\n')
    for line in lines:
        if line.split(' ')[0] == process_name:
           return True
    return False

# path to the chocolatey binary
CHOCOSCRIPT = 'C:/ProgramData/chocolatey/bin/choco'
# Company name
COMPANY = 'LET'
# check/ask for elevation
ELEVATION = True
# Program icon
ICON = 'C:/Program Files/LET/UpgradeManagedSoftware/UpgradeManagedSoftware.ico'
# Mail sender address
MAILFROM = "sysadmin@let.be"
# smtp server
MAILSERVER = "uit.telenet.be"
# mail subject
MAILSUBJECT = _("Managed software upgrade report for %s") % (socket.gethostname())
# whom to inform about troubles
MAILTO = ['jde@let.be']
# Default text for 'no upgrades found":
NOCHOCOUPGRADES = _('No packages to upgrade')
# path to the wpkg script
WPKGSCRIPT = '\\\\172.16.15.33\\install\\service\\let-tools\\wpkglet.cmd'
# error triggers for output filter
ERRORS = ['Could not process (install)', 'Exit code returned non-successful']
# send mail autmatically, when error is present in the log
SENDAUTOMAIL = True
# subject prefix
SUBJECTPREFIX = '[Automatic error mail] - '

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", package])
    finally:
        globals()[package] = importlib.import_module(package)

def restart_explorer():
    # kill all explorer processes
    # os.system("taskkill /im explorer.exe /F")
    subprocess.call(["taskkill", "/im", "explorer.exe", "/F"], shell=True)
    time.sleep(0.5)
    # Check if any explorer process is running or not.
    while (False == process_exists('explorer.exe')):
        subprocess.call(["start", "explorer.exe"], shell=True)
        time.sleep(0.5)


def disable_event():
    pass


def isAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def isOpen(ip,port):
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   try:
      s.connect((ip, int(port)))
      s.shutdown(2)
      return True
   except:
      return False

def sendMail(fromaddr, toaddrs, message, subject=MAILSUBJECT):
    """
    Function for sending mails
    :param fromaddr: sender address
    :param toaddrs:  recipients adress
    :param message: message body
    :param subject: mail subject
    """

    try:
        msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
               % (fromaddr, ", ".join(toaddrs), SUBJECTPREFIX + subject))
        msg += message
        server = smtplib.SMTP(MAILSERVER)
        server.set_debuglevel(1)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
    except:
        messagebox.showinfo(_('Info'), _(
            "SMTP connection failed; check your internet connection."))

class GuiPart:
    """ GUI thread, used for drawing gui
    the communication with this thread is done by 2 queues: queue_gui_in and queue_gui_out
    """
    def __init__(self, master, queue_in, queue_out, endCommand):
        """
        :param master: parent
        :param queue_gui_in: queue for communication to gui
        :param queue_gui_out: queue for communication to worker thread
        :param endCommand:
        """
        self.queue_gui_in = queue_in
        self.queue_gui_out = queue_out
        # Statuses of the main window
        self._statuses = ('start', 'check', 'upgrade', 'wpkg')
        self.status = 'start'
        # View states, for showing the short or longer output.
        self._output_statuses = ('less', 'more')
        self.output_status = 'less'
        self.parent = master
        # longer output in gui
        self.output = ''
        # shorter output in gui
        self.short_output = ''
        # text for mail
        self.mail_output = ''
        # if first_start is True, the first step (get list of outdated packages) is automatically started
        self.first_start = True
        self.endCommand = endCommand

        # GUI
        self.label_project = tk.Label(master, text=_('Packages to upgrade:'), justify=tk.LEFT)
        self.frame_listbox = tk.Frame(master)

        self.listbox_dialogs = tk.Listbox(self.frame_listbox, width=117, selectmode='SINGLE')

        self.scrollbar_dialogs = tk.Scrollbar(self.frame_listbox, orient='vertical')
        self.scrollbar_dialogs.config(command=self.listbox_dialogs.yview)

        self.scrollbar_dialogs_horizontal = tk.Scrollbar(self.frame_listbox, orient='horizontal')
        self.scrollbar_dialogs_horizontal.config(command=self.listbox_dialogs.xview)

        self.listbox_dialogs.config(xscrollcommand=self.scrollbar_dialogs_horizontal.set,
                                    yscrollcommand=self.scrollbar_dialogs.set)

        self.button_first = tk.Button(master, text=_("Check for outdated packages"),
                                      command=lambda: self.click_first(),
                                      justify=tk.LEFT, padx=20)
        self.button_second = tk.Button(master, text=_("More detail"),
                                       command=lambda: self.click_second(), padx=20)
        self.button_quit = tk.Button(master, text=_("Quit"),
                                     command=lambda: self.click_quit(), padx=20)

        # GUI set widgets to grid
        self.label_project.grid(row=0, column=0, stick='w', pady=2, padx=5)
        self.frame_listbox.grid(row=1, column=0, columnspan=3, padx=6, pady=2, sticky='nsew')
        self.listbox_dialogs.grid(row=0, column=0, sticky='nesw')
        self.scrollbar_dialogs.grid(row=0, column=1, sticky='ns')
        self.scrollbar_dialogs_horizontal.grid(row=2, column=0, sticky='ew')
        self.button_first.grid(row=3, column=0, pady=2, padx=6, sticky='sw')
        self.button_second.grid(row=3, column=1, pady=2, padx=6, sticky='s')
        self.button_quit.grid(row=3, column=2, pady=2, padx=6, sticky='s')

    def list_outdated(self):
        """
        queries list of outdated packages from the worker thread
        sends a command to the out queue
        """
        self.queue_gui_out.put('get_list_outdated')

    def upgrade_packages(self):
        """
        send upgrade packages message to the worker thread
        sends a command to the out queue
        """
        self.queue_gui_out.put('upgrade_packages')

    def run_wpkg(self):
        """
        send run wpkgmessage to the worker thread
        sends a command to the out queue
        """
        self.queue_gui_out.put('run_wpkg')

    def set_disabled_state(self, description):
        """
        disables the buttons in the GUI
        :param description: text to show in the label
        """
        self.button_first.configure(state=tk.DISABLED)
        self.button_second.configure(state=tk.DISABLED)
        self.button_quit.configure(state=tk.DISABLED)
        self.label_project.configure(text=description)

    def set_enabled_state(self, description):
        """
        enables the buttons in the GUI
        :param description: text to show in the label
        """
        self.button_first.configure(state=tk.NORMAL)
        self.button_second.configure(state=tk.NORMAL)
        self.button_quit.configure(state=tk.NORMAL)
        self.label_project.configure(text=description)

    def click_first(self):
        """
        Event for the first button's click
            - turns off the buttons
            - clears the listbox in the gui
            - calls a function depending on the status
        """
        if self.status == 'start':
            self.set_disabled_state(_('Checking for outdated packages; please wait...'))
            self.show_message('')
            self.list_outdated()
        elif self.status == 'check':
            self.set_disabled_state(_("Upgrading all outdated packages; please wait and don't close the program..."))
            self.show_message('')
            self.upgrade_packages()
        elif self.status == 'upgrade':
            self.set_disabled_state(_("Running wpkg; please wait and don't close the program..."))
            self.show_message('')
            self.run_wpkg()
        elif self.status == 'wpkg':
            self.set_disabled_state(_('Sending all output by mail to %s...') % (MAILTO[0]))
            self.show_message('')
            sendMail(MAILFROM, MAILTO, self.mail_output)
            self.set_enabled_state(_('Mail sent to %s.') % (MAILTO[0]))
            self.button_first.configure(state=tk.DISABLED)

    def click_second(self):
        """
        Event for the second button's click
        Changes between short and long text, changing the 2nd buttons text accordingly
        """
        if self.output_status == 'less':
            self.output_status = 'more'
            self.button_second.configure(text=_("Less detail"))
        else:
            self.output_status = 'less'
            self.button_second.configure(text=_("More detail"))
        self.show_output()

    def click_quit(self):
        """
        Event for the quit button's click
        """
        self.endCommand()
        self.parent.destroy()
        # sys.exit is considered good to use in production code. This is because the sys module will always be there. you can just do directly what sys.exit does behind the scenes and run:
        raise SystemExit

    def show_output(self):
        """
        Shows short or long output from command depending on output_status (more or less)
        """
        if self.output_status == 'less':
            self.show_message(self.short_output)
        else:
            self.show_message(self.output)

    def show_message(self, message):
        """
        Clears the listbox_dialog and shows a message in it
        """
        self.listbox_dialogs.delete(0, 'end')
        for a_string in message.split('\n'):
            self.listbox_dialogs.insert('end', a_string)

    def processIncoming(self):
        """ Check if is a message in queue gui_in, and if yes, responds """
        # if first_start is true autostarts the first step (get list of outdated packages)
        if self.first_start:
            self.first_start = False
            self.set_disabled_state(_('Checking for outdated packages; please wait...'))
            self.show_message('')
            self.list_outdated()

        # gets a message from queue, depending on message's description does what need to be done
        while self.queue_gui_in.qsize():
            try:
                msg = self.queue_gui_in.get(0)
                message = json.loads(msg)

                if message['description'] == 'list_outdated':
                    self.set_enabled_state(_('Outdated packages:') + '\n' + _('(before upgrading, please close the listed outdated applications to prevent problems.)'))
                    self.status = 'check'
                    self.output = message['output']
                    self.short_output = message['short_output']
                    self.mail_output += message['output']
                    self.show_output()
                    self.button_first.configure(text=_("Upgrade packages"))
                    if self.short_output == NOCHOCOUPGRADES:
                        self.button_first.configure(text=_("Run WPKG"))
                        self.status = 'upgrade'
                elif message['description'] == 'upgrade_packages':
                    self.set_enabled_state(_('Upgrade result:') + '\n' + _("(please run WPKG now - it will take only a few seconds.)"))
                    self.status = 'upgrade'
                    self.output = message['output']
                    self.short_output = message['short_output']
                    self.mail_output += message['output']
                    self.show_output()
                    self.button_first.configure(text=_("Run WPKG"))
                    # we don't want the user to quit now - WPKG should be run.
                    self.button_quit.configure(state=tk.DISABLED)
                elif message['description'] == 'wpkg':
                    self.set_enabled_state(_('WPKG result:') + '\n' + _("(only errors are displayed below)"))
                    self.status = 'wpkg'
                    self.output = message['output']
                    self.short_output = message['short_output']
                    self.mail_output += message['output']
                    self.show_output()
                    self.button_first.configure(text=_("Report upgrade problems by mail"))
                    if (message['short_output'] != '') and SENDAUTOMAIL:
                        self.click_first()
                        self.button_first.configure(state=tk.DISABLED)
                        self.show_output()

                if message['description'] == 'show_message':
                    self.listbox_dialogs.insert('end', message['output'])
                    self.listbox_dialogs.yview(tk.END)

            except Queue.Empty:
                pass


class ThreadedClient:
    """
    Working thread, mainly for calling upgrade processes
    """
    def __init__(self, master):
        """
        Initialization
        """
        self.master = master

        # The queues for communication with the GUI
        self.queue_gui_in = queue.Queue()
        self.queue_gui_out = queue.Queue()

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue_gui_in, self.queue_gui_out, self.endApplication)

        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        # Start the periodic call in the GUI to check if the queue contains anything
        self.periodicCall()

    def periodicCall(self):
        """

        """
        self.gui.processIncoming()
        if not self.running:
            sys.exit(1)
        self.master.after(200, self.periodicCall)

    def workerThread1(self):
        """
        Checkes the queue for command from the GUI (queue_gui_out),
        does it and
        sends a message back to gui (queue_gui_in)
        """
        while self.running:
            time.sleep(0.01)
            upgradeSW.setQueue(self.queue_gui_in)
            try:
                msg = self.queue_gui_out.get()
                if msg == 'get_list_outdated':
                    msg_back = upgradeSW.listOutdated()
                    self.queue_gui_in.put(json.dumps(msg_back))
                elif msg == 'upgrade_packages':
                    msg_back = upgradeSW.upgrade()
                    self.queue_gui_in.put(json.dumps(msg_back))
                elif msg == 'run_wpkg':
                    msg_back = upgradeSW.wpkg()
                    self.queue_gui_in.put(json.dumps(msg_back))
            except:
                pass

    def endApplication(self):
        self.running = 0


class UpgradeManagedSoftware:
    """
    Class for managing windows software
    """
    cmdChoco = CHOCOSCRIPT
    cmdWpkg = WPKGSCRIPT

    def __init__(self):
        self.output = ""
        self.long_output = ""
        self.queue_gui_in = ''
        self.gitextensions_is_present = False

    def setQueue(self, queue_gui_in):
        """
        set queue for communication with GUI
        used for real time print output from subprocess to GUI
        """
        self.queue_gui_in = queue_gui_in

    def runCommand(self, command_line):
        """ runs a command
        output from the command is sent to GUI
        """
        process = subprocess.Popen(command_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        # subprocess.Popen(command_line, stdout=subprocess.PIPE, creationflags=CREATE_NEW_CONSOLE)

        result = ''

        while True:
            line = process.stdout.readline()
            # print (line.decode("utf-8").replace("\r", "").replace("\n", ""))
            result += line.decode("utf-8")

            # A message with "show_message" in  description is appended to the listbox in the GUI
            # Can be used for debugging,
            msg = dict()
            msg['error'] = False
            msg['short_output'] = 'OK.'
            msg['output'] = line.decode("utf-8")
            msg['description'] = 'show_message'
            self.queue_gui_in.put(json.dumps(msg))

            if not line:
                break

        #result = process.communicate()

        return result

    def listOutdated(self):
        """ Lists outdated software from choco to self.output as text
            runs command : choco outdated """
        # execute
        #   choco outdated
        packages = []

        command_line = [self.cmdChoco, 'outdated']
        result = self.runCommand(command_line)

        short_result = ''

        # filter output
        for a_line in result.split():
            found_package = re.search(r'(.+)\|false', a_line)
            if found_package:
                packages.append(found_package.group(1))
        if len(packages) == 0:
            short_result = NOCHOCOUPGRADES
        else:
            # self.output = 'Packages to upgrade:\n\n'
            short_result += '\n'.join(packages)
            short_result += '\n\n   ' + _("Total: {} package(s)").format(len(packages)) + '\n'

        msg = dict()
        msg['error'] = False
        msg['short_output'] = short_result
        msg['output'] = result
        msg['description'] = 'list_outdated'

        # if gitextensions is to be upgraded, we better warn the user about possibly disappearing taskbar/desktop icons
        if short_result.find('gitextensions') > -1:
            self.gitextensions_is_present = True

        return msg

    def upgrade(self):
        """ Lists outdated software from choco to self.output as text
            runs command : choco upgrade all -y
        """

        #upgrade all packages except gitextensions
        command_line = [self.cmdChoco, 'upgrade', 'all', '--except=gitextensions', '-y']
        result = self.runCommand(command_line)

        report = []
        include_line = False
        for a_line in re.split('\r\n', result):
            if re.match('^Upgrading', a_line):
                include_line = True
            if include_line:
                report.append(a_line)
            if re.search('Chocolatey upgraded ', a_line):
                include_line = False

        msg = dict()
        msg['error'] = False
        msg['short_output'] = report[-1]
        msg['output'] = result
        msg['description'] = 'upgrade_packages'

        if self.gitextensions_is_present:

            messagebox.showinfo(_('Info'), _(
                "GitExtensions will be updated.  Due to some problem with the installer, explorer.exe may be killed during the upgrade and restarted after the upgrade of all packages has completed.  Your taskbar and desktop icons may be unavailable till all upgrades have been completed."))

            # upgrade only gitextensions at the end of the upgrade process
            command_line = [self.cmdChoco, 'upgrade', 'gitextensions', '-y']
            result = self.runCommand(command_line)

            messagebox.showinfo(_('Info'), _(
                "Gitextensions has been upgraded and your taskbar may have disappeared.  If so, please press CTRL-SHIFT-ESC and from the File menu, start a new task explorer.exe . "))

            report = []
            include_line = False
            for a_line in re.split('\r\n', result):
                if re.match('^Upgrading', a_line):
                    include_line = True
                if include_line:
                    report.append(a_line)
                if re.search('Chocolatey upgraded ', a_line):
                    include_line = False

            msg['short_output'] += report[-1]
            msg['output'] += result

            #restart_explorer()

        return msg

    def wpkg(self):
        """ runs wpkglet.cmd
            result is saved to self.output """
        command_line = [self.cmdWpkg]
        result = self.runCommand(command_line)
        short_output = ''
        resultlines = result.split('\r\n')
        for a_line in resultlines:
            found_error = False
            for error_text in ERRORS:
                if a_line.find(error_text) > -1:
                    found_error = True
            if found_error:
                short_output += a_line + '\r\n'

        # report = []
        # for a_line in re.split('\r\n', result[0].decode('utf-8')):
        #     report.append(a_line)
        # self.output = '\n'.join(report)

        msg = dict()
        msg['error'] = False
        msg['short_output'] = short_output
        msg['output'] = result
        msg['description'] = 'wpkg'

        return msg


if __name__ == "__main__":
    # Checking wpkglet, but too slow when not found...
    # if not (os.path.isfile('\\\\172.16.15.33\\install\\service\\let-tools\\wpkglet.cmd')):
    #    print ("wpkglet.cmd not found")
    #    print ("Check your VPN connection")
    #    exit()

    # Check need for elevation
    if (ELEVATION and isAdmin()) | (not ELEVATION):
        #restart_explorer()
        
        upgradeSW = UpgradeManagedSoftware()
        rand = random.Random()
        root = tk.Tk()

        #disable alt-F4
        root.bind('<Alt-F4>', disable_event)
        root.bind('<Escape>', disable_event)
        root.protocol("WM_DELETE_WINDOW", disable_event)

        root.title("Upgrade %s managed software - %s" % (COMPANY, VERSION))
        try:
            root.iconbitmap(ICON)
        except:
            print("Icon not found!")
        # set the tray icon to the same
        myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        root.resizable(height=False, width=False)

        client = ThreadedClient(root)
        root.mainloop()

    else:
        if sys.version_info > (3, 0):
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        else:
            ctypes.windll.shell32.ShellExecuteW(None, u"runas", unicode(sys.executable), unicode(__file__), None, 1)
