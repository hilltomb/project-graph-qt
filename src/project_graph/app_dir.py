"""
此模块仅仅导出一个变量 DATA_DIR，它代表了程序的用户数据目录。

数据目录的具体位置取决于操作系统和用户配置。
"""

from pathlib import Path

from appdirs import user_data_dir

from project_graph.logging import log

_APP_NAME = "project-graph"
_APP_AUTHOR = "LiRen"

DATA_DIR = user_data_dir(_APP_NAME, _APP_AUTHOR)
log(DATA_DIR)

log(Path(DATA_DIR) / "test.txt")
