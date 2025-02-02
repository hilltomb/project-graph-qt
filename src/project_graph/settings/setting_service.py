"""
单例模式

此模块接近底层，尽量不要依赖其他模块
"""

from pathlib import Path

from project_graph.app_dir import DATA_DIR


settings_file_path = Path(DATA_DIR) / "settings.json"


class SettingService:
    def __init__(self):
        """
        初始化默认数值
        """
        self.line_style = 0  # 0: 贝塞尔，1：直线
        self.theme_style = 0

        self.is_show_grid = True
        """是否显示网格"""

        self.is_show_debug_text = True
        """是否显示左上角调试信息"""

        self.is_enable_node_collision = True
        """是否启用节点碰撞检测"""

        self.camera_scale_exponent: float = 1.1
        """缩放指数，越大缩放速度越快, 1~2 """

        self.camera_move_amplitude: int = 2
        """摄像机移动加速度大小 1~10 """

        self.camera_move_friction: float = 0.1
        """摄像机移动的滑动摩擦力系数 0.0~1.0 默认0.1
        摩擦系数，越大摩擦力越大，摩擦力会使速度减慢
        """

        pass

    def __dict__(self):
        """
        返回设置字典
        """
        return {
            "line_style": self.line_style,
            "theme_style": self.theme_style,
            "is_show_grid": self.is_show_grid,
            "is_show_debug_text": self.is_show_debug_text,
            "is_enable_node_collision": self.is_enable_node_collision,
            "camera_scale_exponent": self.camera_scale_exponent,
            "camera_move_amplitude": self.camera_move_amplitude,
            "camera_move_friction": self.camera_move_friction,
        }

    def to_json_string(self):
        """
        将设置转换为json字符串
        """
        from json import dumps

        return dumps(self.__dict__())

    def load_settings(self):
        """
        从文件加载设置
        """
        if not settings_file_path.exists():
            # 没有文件就创建一个
            self.save_settings()
            return
        with open(settings_file_path, "r") as f:
            data = f.read()
            if data:
                import json

                settings = json.loads(data)
                self.line_style = settings.get("line_style", 0)
                self.theme_style = settings.get("theme_style", 0)
                self.is_show_grid = settings.get("is_show_grid", True)
                self.is_show_debug_text = settings.get("is_show_debug_text", True)
                self.is_enable_node_collision = settings.get(
                    "is_enable_node_collision", True
                )
                self.camera_scale_exponent = settings.get("camera_scale_exponent", 1.1)
                self.camera_move_amplitude = settings.get("camera_move_amplitude", 2)
                self.camera_move_friction = settings.get("camera_move_friction", 0.1)

    def save_settings(self):
        """
        保存设置到文件
        """
        with open(settings_file_path, "w") as f:
            f.write(self.to_json_string())


SETTING_SERVICE = SettingService()
"""
全局唯一单例
"""

SETTING_SERVICE.load_settings()
