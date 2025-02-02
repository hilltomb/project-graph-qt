from PyQt5.QtGui import QColor

from project_graph.data_struct.circle import Circle
from project_graph.data_struct.curve import ConnectCurve
from project_graph.data_struct.line import Line
from project_graph.data_struct.number_vector import NumberVector
from project_graph.data_struct.rectangle import Rectangle
from project_graph.entity.entity_node import EntityNode
from project_graph.paint.paint_utils import PainterUtils
from project_graph.paint.paintables import PaintContext
from project_graph.settings.setting_service import SETTING_SERVICE


class NodeManager:
    """
    存储并管理所有节点和连接
    节点的增删改、连接断开、移动、渲染等操作都在这里进行
    """

    def __init__(self):
        self.nodes: list[EntityNode] = []

        self._lines: list[Line] = []
        """lines只用于绘制的时候给一个缓存，不参与逻辑运算，只在改变的时候重新计算"""

        self.cursor_node: EntityNode | None = None
        """有一个游标在节点群上移动，这个游标通过上下左右或者点击更改附着的节点"""

        self.grow_node_location: NumberVector | None = None
        """相对于cursor_node的位置，看成一个相对位置矢量，世界坐标格式，用于生长节点"""
        self.grow_node_inner_text: str = ""
        """生长节点的内置文本"""
        pass

    def move_cursor(self, direction: str):
        """
        移动游标，方向为上下左右键
        """
        if self.cursor_node is None:
            # 随机选一个节点作为游标
            if self.nodes:
                self.cursor_node = self.nodes[0]
            return
        # 当前一定 有游标
        if direction == "up":
            # 搜一个距离自己上边缘最近的节点
            min_dist = float("inf")
            min_node = None
            for node in self.nodes:
                if node == self.cursor_node:
                    continue
                if node.body_shape.center.y < self.cursor_node.body_shape.center.y:
                    dist = node.body_shape.bottom_center.distance_to(
                        self.cursor_node.body_shape.top_center
                    )
                    if dist < min_dist:
                        min_dist = dist
                        min_node = node
            if min_node is not None:
                self.cursor_node = min_node
        elif direction == "down":
            # 搜一个距离自己下边缘最近的节点
            min_dist = float("inf")
            min_node = None
            for node in self.nodes:
                if node == self.cursor_node:
                    continue
                if node.body_shape.center.y > self.cursor_node.body_shape.center.y:
                    dist = node.body_shape.top_center.distance_to(
                        self.cursor_node.body_shape.bottom_center
                    )
                    if dist < min_dist:
                        min_dist = dist
                        min_node = node
            if min_node is not None:
                self.cursor_node = min_node
        elif direction == "left":
            # 搜一个距离自己左边缘最近的节点
            min_dist = float("inf")
            min_node = None
            for node in self.nodes:
                if node == self.cursor_node:
                    continue
                if node.body_shape.center.x < self.cursor_node.body_shape.center.x:
                    dist = node.body_shape.right_center.distance_to(
                        self.cursor_node.body_shape.left_center
                    )
                    if dist < min_dist:
                        min_dist = dist
                        min_node = node
            if min_node is not None:
                self.cursor_node = min_node
        elif direction == "right":
            # 搜一个距离自己右边缘最近的节点
            min_dist = float("inf")
            min_node = None
            for node in self.nodes:
                if node == self.cursor_node:
                    continue
                if node.body_shape.center.x > self.cursor_node.body_shape.center.x:
                    dist = node.body_shape.left_center.distance_to(
                        self.cursor_node.body_shape.right_center
                    )
                    if dist < min_dist:
                        min_dist = dist
                        min_node = node
            if min_node is not None:
                self.cursor_node = min_node
        else:
            pass

    def is_grow_node_prepared(self) -> bool:
        """
        是否已经准备好生长节点
        """
        return self.grow_node_location is not None

    def grow_node(self):
        """
        生长节点，按下Tab的时候使用
        """
        if self.cursor_node is None:
            return
        self.grow_node_location = NumberVector(400, 0)
        self.grow_node_inner_text = "New Node"
        pass

    def grow_node_cancel(self):
        """
        生长节点取消
        """
        self.grow_node_location = None
        self.grow_node_inner_text = ""
        pass

    def grow_node_confirm(self):
        """
        生长节点确认，再次按下tab的时候使用
        """
        if self.cursor_node is None:
            return
        if self.grow_node_location is None:
            return
        new_node = self.add_node_by_click(
            self.cursor_node.body_shape.center + self.grow_node_location
        )
        self.connect_node(self.cursor_node, new_node)
        self.grow_node_cancel()

    def rotate_grow_direction(self, is_clockwise: bool):
        """
        旋转生长方向
        是否是顺时针
        """
        if self.grow_node_location is None:
            return
        if is_clockwise:
            self.grow_node_location = self.grow_node_location.rotate(30)
        else:
            self.grow_node_location = self.grow_node_location.rotate(-30)

    def dump_all_nodes(self) -> dict:
        """
        将所有节点信息转成字典等可序列化的格式
        {
            "nodes": [
                {
                    body_shape: {
                        "type": "Rectangle",
                        "location_left_top": [x, y],
                        "width": w,
                        "height": h,
                    },
                    inner_text: "text",
                    uuid: "(uuid str)",
                    children: [ "(uuid str)" ]
                },
            ]
        }
        """
        res = {"nodes": [node.dump() for node in self.nodes]}

        return res

    @staticmethod
    def _refresh_all_uuid(data: dict) -> dict:
        """
        刷新所有节点的uuid, 并返回更新后的字典
        刷新的意义是用户可能会重复复制添加一大堆节点内容，防止出现uuid冲突
        """
        from copy import deepcopy
        from uuid import uuid4

        new_data = deepcopy(data)
        for node in new_data["nodes"]:
            # 把每个节点的uuid都改成新的uuid
            old_uuid = node["uuid"]
            new_uuid = str(uuid4())
            node["uuid"] = new_uuid

            for _, other_node in enumerate(new_data["nodes"]):
                if other_node == node:
                    continue
                for j, child_uuid in enumerate(other_node.get("children", [])):
                    if child_uuid == old_uuid:
                        other_node["children"][j] = new_uuid
        return new_data

    def add_from_dict(
        self, data: dict, location_world: NumberVector, refresh_uuid=True
    ):
        """
        从字典等可序列化的格式中添加节点信息
        """
        if refresh_uuid:
            data = self._refresh_all_uuid(data)
        # 开始构建节点本身
        for node_data in data["nodes"]:
            assert isinstance(node_data, dict)

            body_shape_data = node_data["body_shape"]
            if body_shape_data["type"] == "Rectangle":
                body_shape = Rectangle(
                    NumberVector(
                        body_shape_data["location_left_top"][0] + location_world.x,
                        body_shape_data["location_left_top"][1] + location_world.y,
                    ),
                    body_shape_data["width"],
                    body_shape_data["height"],
                )
            else:
                raise ValueError(
                    f"Unsupported body shape type: {body_shape_data['type']}"
                )

            node = EntityNode(body_shape)
            node.inner_text = node_data.get("inner_text", "")
            node.details = node_data.get("details", "")

            node.uuid = node_data["uuid"]
            self.nodes.append(node)

        # 构建节点之间的连接关系
        for node_data in data["nodes"]:
            node = self.get_node_by_uuid(node_data["uuid"])
            if node is None:
                continue
            for child_uuid in node_data.get("children", []):
                child = self.get_node_by_uuid(child_uuid)
                if child is None:
                    continue
                node.add_child(child)

        self.update_lines()
        pass

    def load_from_dict(self, data: dict):
        """
        从字典等可序列化的格式中恢复节点信息
        """
        # 先清空原有节点
        self.nodes.clear()
        self.add_from_dict(data, NumberVector(0, 0), refresh_uuid=False)
        self.update_lines()

    def get_node_by_uuid(self, uuid: str) -> EntityNode | None:
        for node in self.nodes:
            if node.uuid == uuid:
                return node
        return None

    def move_node(self, node: EntityNode, d_location: NumberVector):
        """
        移动一个节点（不带动子节点的单独移动）
        """
        node.move(d_location)
        self.collide_dfs(node)
        self.update_lines()

    def move_node_with_children(self, node: EntityNode, d_location: NumberVector):
        """
        移动一个节点（带动子节点的整体移动）
        """
        self._move_node_with_children_dfs(node, d_location, [node.uuid])
        self.update_lines()

    def _move_node_with_children_dfs(
        self, node: EntityNode, d_location: NumberVector, visited_uuids: list[str]
    ):
        node.move(d_location)
        self.collide_dfs(node)
        for child in node.children:
            if child.uuid in visited_uuids:
                # 防止出现环形连接，导致无限递归
                continue
            self._move_node_with_children_dfs(
                child, d_location, visited_uuids + [node.uuid]
            )

    def collide_dfs(self, self_node: EntityNode):
        """
        self_node 是主体
        这个dfs指的不是子节点递归，是和周围其他节点的碰撞传递
        """
        if not SETTING_SERVICE.is_enable_node_collision:
            return

        for node in self.nodes:
            if node == self_node:
                continue
            if node.body_shape.is_collision(self_node.body_shape):
                self_node.collide_with(node)
                self.collide_dfs(node)

    def add_node_by_click(self, location_world: NumberVector) -> EntityNode:
        res = EntityNode(Rectangle(location_world - NumberVector(50, 50), 100, 100))
        self.nodes.append(res)
        return res

    def delete_node(self, node: EntityNode):
        if node in self.nodes:
            self.nodes.remove(node)
        # 不仅要删除节点本身，其他节点的child中也要删除该节点
        for father_node in self.nodes:
            if node in father_node.children:
                father_node.children.remove(node)
        self.update_lines()

    def delete_nodes(self, nodes: list[EntityNode]):
        for node in nodes:
            if node in self.nodes:
                self.nodes.remove(node)
            # 不仅要删除节点本身，其他节点的child中也要删除该节点
            for father_node in self.nodes:
                if node in father_node.children:
                    father_node.children.remove(node)
        self.update_lines()

    def connect_node(self, from_node: EntityNode, to_node: EntityNode) -> bool:
        if from_node in self.nodes and to_node in self.nodes:
            res = from_node.add_child(to_node)
            self.update_lines()
            return res
        return False

    def disconnect_node(self, from_node: EntityNode, to_node: EntityNode) -> bool:
        if from_node in self.nodes and to_node in self.nodes:
            res = from_node.remove_child(to_node)
            self.update_lines()
            return res
        return False

    def _get_all_lines(self) -> list[Line]:
        lines = []
        for node in self.nodes:
            for child in node.children:
                connect_line = Line(node.body_shape.center, child.body_shape.center)
                from_point = node.body_shape.get_line_intersection_point(connect_line)
                to_point = child.body_shape.get_line_intersection_point(connect_line)

                lines.append(Line(from_point, to_point))
        return lines

    def update_lines(self):
        """
        注意：此方法不要在外界频繁调用（尤其是循环渲染中），否则可能很卡
        建议只在必要操作之后调用一下。
        """
        self._lines = self._get_all_lines()

    def get_all_lines_and_node(self) -> list[tuple[Line, EntityNode, EntityNode]]:
        lines = []
        for node in self.nodes:
            for child in node.children:
                connect_line = Line(node.body_shape.center, child.body_shape.center)
                from_point = node.body_shape.get_line_intersection_point(connect_line)
                to_point = child.body_shape.get_line_intersection_point(connect_line)

                lines.append((Line(from_point, to_point), node, child))
        return lines

    def rotate_node(self, node: EntityNode, degrees: float):
        """
        按照一定角度旋转节点，旋转的是连接这个节点的所有子节点
        也就是如果这个节点没有子节点，那么看上去没有效果
        """
        self._rotate_node_dfs(node, node, degrees, [])
        self.update_lines()

    def _rotate_node_dfs(
        self,
        rotate_center_node: EntityNode,
        current_node: EntityNode,
        degrees: float,
        visited_uuids: list[str],
    ):
        rotate_center_location = rotate_center_node.body_shape.center
        # 先旋转自己
        radius = current_node.body_shape.center.distance_to(rotate_center_location)
        center_to_child_vector = (
            current_node.body_shape.center - rotate_center_location
        ).normalize()
        center_to_child_vector = center_to_child_vector.rotate(degrees) * radius
        new_location = rotate_center_location + center_to_child_vector
        current_node.move_to(
            new_location
            - NumberVector(
                current_node.body_shape.width / 2, current_node.body_shape.height / 2
            )
        )
        # 再旋转子节点
        for child in current_node.children:
            if child.uuid in visited_uuids:
                # 防止出现环形连接，导致无限递归
                continue
            self._rotate_node_dfs(
                rotate_center_node, child, degrees, visited_uuids + [current_node.uuid]
            )

    def paint(self, context: PaintContext):
        # 画节点本身
        for node in self.nodes:
            node.paint(context)

        # 连线
        context.painter.q_painter().setTransform(
            context.camera.get_world2view_transform()
        )
        for line in self._lines:
            if SETTING_SERVICE.line_style == 0:
                context.painter.paint_curve(
                    ConnectCurve(line.start, line.end), QColor(204, 204, 204)
                )
            elif SETTING_SERVICE.line_style == 1:
                PainterUtils.paint_arrow(
                    context.painter.q_painter(),
                    line.start,
                    line.end,
                    QColor(204, 204, 204),
                    4,
                    30,
                )

        context.painter.q_painter().resetTransform()
        # 画游标
        if self.cursor_node is not None:
            margin = 10
            PainterUtils.paint_rect(
                context.painter.q_painter(),
                context.camera.location_world2view(
                    self.cursor_node.body_shape.location_left_top
                    - NumberVector(margin, margin)
                ),
                context.camera.current_scale
                * (self.cursor_node.body_shape.width + margin * 2),
                context.camera.current_scale
                * (self.cursor_node.body_shape.height + margin * 2),
                QColor(255, 255, 255, 0),
                QColor(255, 255, 255, 200),
                int(8 * context.camera.current_scale),
            )
        # 画虚拟的待生长的节点
        if self.grow_node_location is not None and self.cursor_node is not None:
            PainterUtils.paint_circle(
                context.painter.q_painter(),
                Circle(
                    context.camera.location_world2view(
                        self.cursor_node.body_shape.center + self.grow_node_location
                    ),
                    50 * context.camera.current_scale,
                ),
                QColor(255, 255, 255, 0),
                QColor(255, 255, 255, 128),
                4 * context.camera.current_scale,
            )
            PainterUtils.paint_arrow(
                context.painter.q_painter(),
                context.camera.location_world2view(self.cursor_node.body_shape.center),
                context.camera.location_world2view(
                    self.grow_node_location + self.cursor_node.body_shape.center
                ),
                QColor(23, 159, 255),
                4 * context.camera.current_scale,
                30 * context.camera.current_scale,
            )
