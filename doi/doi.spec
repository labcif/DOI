# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['doi.py'],
             pathex=['C:\\projeto\\repo\\doi'],
             binaries=[],
             datas=[('detectors/darknet/yolo_cpp_dll.dll', 'detectors/darknet'), ('detectors/darknet/yolo_cpp_dll_nogpu.dll', 'detectors/darknet'), ('detectors/darknet/pthreadGC2.dll', 'detectors/darknet'), ('detectors/darknet/pthreadVC2.dll', 'detectors/darknet')],
             hiddenimports=[],
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
          name='doi',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True)
