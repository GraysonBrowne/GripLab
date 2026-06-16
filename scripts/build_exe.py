# scripts/build_exe.py
import PyInstaller.__main__

PyInstaller.__main__.run(
    [
        "main.py",
        "--name=GripLab",
        "--onefile",
        "--version-file=version.txt",
        "--add-data=ui/styles.css:ui",
        "--add-data=ui/tabs.css:ui",
        "--icon=docs/images/GripLab_Icon.png",
        "--splash=docs/images/GripLab_Splash.png",
        "--add-data=docs:docs",
        "--add-data=pyproject.toml:.",
        "--hidden-import=panel",
        "--hidden-import=plotly",
    ]
)
