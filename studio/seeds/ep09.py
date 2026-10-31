"""EP09_仮制作.py を英数字の名前で呼ぶ入口（.bat から使う）。引数はそのまま渡す。"""
import runpy
import sys
from pathlib import Path

sys.argv[0] = str(Path(__file__).with_name("EP09_仮制作.py"))
runpy.run_path(sys.argv[0], run_name="__main__")
