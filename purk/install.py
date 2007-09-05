import os
import shutil
import subprocess

install_path = os.curdir
bin_path = os.curdir
dirs_to_install = []
files_to_install = []
exclude_dirs = ['CVS', 'profile', '.idlerc']
exclude_files = ['install.py', 'urk.desktop', 'urk.nsi', 'installer.exe', 'urk.exe']

nsis_outfile="urk.exe"
nsis_make_exe=["makensis"] #for non-windows systems

def identify_files(path=os.curdir, prefix='', sep=os.path.join):
    #set files to a list of the files we want to install
    print "Searching for files to install"
    for filename in os.listdir(path):
        abs_file = os.path.join(path,filename)
        rel_file = sep(prefix,filename)
        if os.path.isfile(abs_file) and filename not in exclude_files:
            print "Marking file %s for installation" % rel_file
            files_to_install.append(rel_file)
        elif os.path.isdir(abs_file) and filename not in exclude_dirs:
            print "Marking directory %s for installation" % rel_file
            dirs_to_install.append(rel_file)
            identify_files(abs_file, rel_file, sep)

def install_files():
    #copy .py files to the destination directory
    print "Installing files to %s" % install_path
    for dirname in dirs_to_install:
        dest = os.path.join(install_path,dirname)
        if os.access(dest,os.X_OK):
            print "Found directory %s" % dest
        else:
            print "Creating new directory %s" % dest
            os.mkdir(dest,0755)
    for filename in files_to_install:
        source = os.path.join(os.curdir,filename)
        dest = os.path.join(install_path,filename)
        print "Copying %s to %s" % (source, dest)
        shutil.copy(source, dest)

def nsis_generate_script():
    filename = os.path.join(install_path,"urk.nsi")
    print "Generating NSIS installer script %s" % filename
    f = file(filename,'w')
    #header
    f.write(r"""
; This file was automatically generated by urk's install.py. Don't
; even bother to modify it.

Name "urk"

OutFile "installer.exe"

InstallDir $PROGRAMFILES\urk

InstallDirRegKey HKLM "Software\urk" "Install_Dir"


Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles


Function GetPythonDir
  Var /GLOBAL python_dir
  ReadRegStr $python_dir HKLM "Software\Python\PythonCore\2.4\InstallPath" ""
FunctionEnd


Function GetPythonVersion
  Var /GLOBAL python_version
  Call GetPythonDir
  ExecWait "$python_dir\python.exe -V"
  
FunctionEnd


Section /o "dependencies"
  Call GetPythonDir
  MessageBox MB_OK $python_dir
SectionEnd


Section "urk (required)"
 SetOutPath $INSTDIR
""")
    #look for existing installation?
    for dirname in dirs_to_install:
        f.write(' CreateDirectory "$INSTDIR\\%s"\n' % dirname)
    for filename in files_to_install:
        f.write(' File "/oname=%s" "%s"\n' % (filename, filename))
    f.write(r"""

 WriteRegStr HKLM SOFTWARE\urk "Install_Dir" "$INSTDIR"

 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\urk" "DisplayName" "urk IRC Client"
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\urk" "UninstallString" '"$INSTDIR\uninstall.exe"'
 WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\urk" "NoModify" 1
 WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\urk" "NoRepair" 1
 WriteUninstaller "uninstall.exe"
SectionEnd
""")
    
    #uninstaller
    f.write(r"""
Section "Uninstall"

 ; Remove registry keys
 DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\urk"
 DeleteRegKey HKLM SOFTWARE\urk
""")
    for filename in files_to_install:
        f.write(' Delete $INSTDIR\\%s\n' % filename)
    for dirname in dirs_to_install[::-1]:
        f.write(' RMDIR $INSTDIR\\%s\n' % dirname)
    f.write(r"""
 Delete "$INSTDIR\uninstall.exe"
 RMDIR "$INSTDIR"

SectionEnd
""")
    
    f.close()

def nsis_generate_exe():
    filename = os.path.join(install_path,"urk.nsi")
    print "Calling makensis on %s" % filename
    try: #look for NSIS in the registry
        import _winreg
        key_software = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,"Software")
        key_nsis = _winreg.OpenKey(key_software,"NSIS")
        make_exe = [os.path.join(_winreg.QueryValueEx(key_nsis,None)[0],"makensis.exe")]
    except: #..or just use the global for it
        make_exe = nsis_make_exe
    subprocess.call(make_exe + [filename])

def install_to_nsis():
    def sep(*args):
        return '\\'.join(x for x in args if x)
    identify_files(sep=sep)
    nsis_generate_script()
    nsis_generate_exe()

def install_to_linux_system():
    identify_files()
    
    pass