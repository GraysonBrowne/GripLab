# scripts/build_exe.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--name=GripLab',
    '--onefile',
    '--windowed',
    '--add-data=ui/styles.css:ui',
    '--icon=docs/images/GripLab_Icon.png',
    '--splash=docs/images/GripLab_Splash.png',
    '--add-data=docs:docs',
    '--hidden-import=panel',
    '--hidden-import=plotly',
])