from cx_Freeze import setup, Executable
import sys

# Dependencies are automatically detected, but it might need
# fine-tuning.
build_options = {'packages': [], 'excludes': [], 'include_files': ['icon.ico']}

# buildOptions = dict(include_files = [('E:\Ai media operator\icon.ico','final_filename')]) #single file, absolute path.


base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('media controller.py', base=base, target_name='Ai Media Controller', icon='icon.ico')
]

setup(name='Ai Media Controller',
      version='1.0',
      description='An advanced ai assistant to control media player using camera made by Ayan Mandal',
      options={'build_exe': build_options},
      executables=executables)
