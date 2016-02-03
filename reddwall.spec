# -*- mode: python -*-

block_cipher = None


a = Analysis(['reddwall.py'],
             pathex=['/Users/mich8139/workspace/misnow1/reddwall'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='reddwall',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='reddwall')
app = BUNDLE(coll,
             name='reddwall.app',
             icon=None,
             bundle_identifier=None)
