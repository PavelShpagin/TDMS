import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_options = {
    'packages': ['webview', 'json', 'pathlib', 'atexit', 'datetime', 're'],
    'excludes': ['tkinter', 'unittest', 'email', 'http', 'urllib', 'xml'],
    'include_files': [],
    'optimize': 2
}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('src/desktop/simple_app.py', 
               base=base, 
               target_name='TDMS-Desktop.exe',
               icon=None)
]

setup(name='TDMS-Desktop',
      version='1.0',
      description='TDMS Desktop Application with Persistent Storage',
      options={'build_exe': build_options},
      executables=executables)

