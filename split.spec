# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
         ( './MetaDataProviders/*.py', 'MetaDataProviders' ),
         ( './utils/*.py', 'utils'),
         ( './split_init.py', '.')
         ]

hiddenmodules = ['bs4', 'pyqt5', 'QVBoxLayout', 'QPlainTextEdit', 'QWidget', 'QStatusBar', 'QAction', 'QMessageBox','QFileDialog','QPrintDialog']

a = Analysis(['split.py'],
             pathex=['c:\\Album Splitter\\album-splitter'],
             binaries=[],
             datas=added_files,
             hiddenimports=hiddenmodules,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='split',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
