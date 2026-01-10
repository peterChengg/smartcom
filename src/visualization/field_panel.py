"""
字段面板组件

提供协议字段的树形显示和实时数值更新功能。
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from ..core.protocol_parser import ParsedPacket
from ..processing.data_processor import DataProcessor
from .protocol_visualizer import FieldExtractor, ColorScheme

logger = logging.getLogger(__name__)


class FieldTreeNode:
    """字段树节点"""

    def __init__(
        self,
        name: str,
        value: Any = None,
        field_type: str = "unknown",
        description: str = "",
        parent: Optional["FieldTreeNode"] = None,
    ):
        self.name = name
        self.value = value
        self.field_type = field_type
        self.description = description
        self.parent = parent
        self.children: List["FieldTreeNode"] = []
        self.is_expanded = True
        self.last_update_time = 0
        self.update_count = 0
        self.min_value = None
        self.max_value = None

    def add_child(self, child: "FieldTreeNode") -> None:
        """添加子节点"""
        child.parent = self
        self.children.append(child)

    def find_child(self, name: str) -> Optional["FieldTreeNode"]:
        """查找子节点"""
        for child in self.children:
            if child.name == name:
                return child
        return None

    def get_path(self) -> str:
        """获取节点路径"""
        path_parts = []
        current = self
        while current:
            path_parts.append(current.name)
            current = current.parent
        return ".".join(reversed(path_parts))

    def update_value(self, value: Any, timestamp: Optional[float] = None) -> None:
        """更新节点值"""
        self.value = value
        self.last_update_time = timestamp or time.time()
        self.update_count += 1

        # 更新统计值
        if isinstance(value, (int, float)):
            if self.min_value is None or value < self.min_value:
                self.min_value = value
            if self.max_value is None or value > self.max_value:
                self.max_value = value

    def get_display_value(self) -> str:
        """获取显示用的格式化值"""
        if self.value is None:
            return "N/A"
        elif isinstance(self.value, bytes):
            return self.value.hex().upper()
        elif isinstance(self.value, bool):
            return "TRUE" if self.value else "FALSE"
        elif isinstance(self.value, (int, float)):
            return f"{self.value:.3f}"
        else:
            return str(self.value)

    def get_color(self) -> str:
        """获取节点颜色"""
        # 使用B4的着色功能
        if hasattr(self.value, "_color"):
            return getattr(self.value, "_color")

        # 根据数据类型分配颜色
        return ColorScheme.get_data_type_color(self.field_type)


class FieldTreeBuilder:
    """字段树构建器"""

    @staticmethod
    def build_from_packet(packet: ParsedPacket) -> FieldTreeNode:
        """从数据包构建字段树"""
        root = FieldTreeNode("root", field_type="packet")

        for field_name, field_value in packet.fields.items():
            # 处理嵌套字段（如带有点的字段名）
            if "." in field_name:
                FieldTreeBuilder._add_nested_field(root, field_name, field_value)
            else:
                child = FieldTreeNode(
                    name=field_name,
                    value=field_value,
                    field_type=FieldTreeBuilder._get_field_type(field_value),
                )
                root.add_child(child)

        return root

    @staticmethod
    def _add_nested_field(root: FieldTreeNode, field_path: str, value: Any) -> None:
        """添加嵌套字段"""
        parts = field_path.split(".")
        current = root

        for i, part in enumerate(parts[:-1]):
            child = current.find_child(part)
            if not child:
                child = FieldTreeNode(part, field_type="struct")
                current.add_child(child)
            current = child

        # 添加叶子节点
        leaf = FieldTreeNode(
            name=parts[-1],
            value=value,
            field_type=FieldTreeBuilder._get_field_type(value),
        )
        current.add_child(leaf)

    @staticmethod
    def _get_field_type(value: Any) -> str:
        """获取字段类型"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, bytes):
            return "bytes"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"


class FieldFilter:
    """字段过滤器"""

    def __init__(self):
        self.filter_text = ""
        self.field_types: List[str] = []
        self.show_updated_only = False
        self.min_update_count = 0

    def set_filter_text(self, text: str) -> None:
        """设置过滤文本"""
        self.filter_text = text.lower()

    def set_field_types(self, types: List[str]) -> None:
        """设置显示的字段类型"""
        self.field_types = [t.lower() for t in types]

    def set_show_updated_only(self, show: bool) -> None:
        """设置只显示更新的字段"""
        self.show_updated_only = show

    def matches_filter(self, node: FieldTreeNode) -> bool:
        """检查节点是否匹配过滤条件"""
        # 文本过滤
        if self.filter_text:
            if (
                self.filter_text not in node.name.lower()
                and self.filter_text not in node.get_display_value().lower()
            ):
                return False

        # 类型过滤
        if self.field_types and node.field_type.lower() not in self.field_types:
            return False

        # 更新次数过滤
        if self.show_updated_only and node.update_count < self.min_update_count:
            return False

        return True


class FieldPanel:
    """字段面板组件"""

    def __init__(self, width: int = 400, height: int = 600):
        self.width = width
        self.height = height
        self.root_nodes: Dict[str, FieldTreeNode] = {}
        self.field_filter = FieldFilter()
        self.selected_node: Optional[FieldTreeNode] = None
        self.expanded_nodes: set = set()
        self.auto_expand_depth = 2
        self.show_descriptions = True

        # 统计信息
        self.field_stats: Dict[str, Any] = defaultdict(
            lambda: {"count": 0, "total_updates": 0, "last_update": 0}
        )

    def add_protocol_data(self, protocol_name: str, packet: ParsedPacket) -> None:
        """添加协议数据"""
        if protocol_name not in self.root_nodes:
            self.root_nodes[protocol_name] = FieldTreeNode(
                name=protocol_name,
                field_type="protocol",
                description=f"Protocol: {protocol_name}",
            )

        root = self.root_nodes[protocol_name]

        # 更新字段树
        new_tree = FieldTreeBuilder.build_from_packet(packet)
        self._merge_field_tree(root, new_tree)

        # 更新统计
        self._update_field_stats(protocol_name, new_tree)

    def _merge_field_tree(
        self, existing_root: FieldTreeNode, new_tree: FieldTreeNode
    ) -> None:
        """合并字段树"""
        timestamp = time.time()

        for new_child in new_tree.children:
            existing_child = existing_root.find_child(new_child.name)

            if existing_child:
                # 更新现有节点
                existing_child.update_value(new_child.value, timestamp)

                # 递归合并子节点
                if new_child.children:
                    temp_root = FieldTreeNode("temp")
                    temp_root.children = existing_child.children
                    self._merge_field_tree(temp_root, new_child)
                    existing_child.children = temp_root.children
            else:
                # 添加新节点
                new_child.update_value(new_child.value, timestamp)
                existing_root.add_child(new_child)

    def _update_field_stats(self, protocol_name: str, tree: FieldTreeNode) -> None:
        """更新字段统计"""

        def update_stats_recursive(node: FieldTreeNode) -> None:
            field_key = f"{protocol_name}.{node.get_path()}"
            stats = self.field_stats[field_key]

            stats["count"] += 1
            stats["total_updates"] = node.update_count
            stats["last_update"] = node.last_update_time

            for child in node.children:
                update_stats_recursive(child)

        for child in tree.children:
            update_stats_recursive(child)

    def set_filter_text(self, text: str) -> None:
        """设置过滤文本"""
        self.field_filter.set_filter_text(text)

    def set_field_types_filter(self, types: List[str]) -> None:
        """设置字段类型过滤"""
        self.field_filter.set_field_types(types)

    def set_show_updated_only(self, show: bool, min_updates: int = 1) -> None:
        """设置只显示更新的字段"""
        self.field_filter.set_show_updated_only(show)
        self.field_filter.min_update_count = min_updates

    def get_filtered_tree_data(self) -> List[Dict[str, Any]]:
        """获取过滤后的树形数据"""
        result = []

        for protocol_name, root in self.root_nodes.items():
            protocol_data = self._process_node(root, 0)
            if protocol_data["children"]:
                result.append({"protocol_name": protocol_name, "root": protocol_data})

        return result

    def _process_node(self, node: FieldTreeNode, depth: int) -> Dict[str, Any]:
        """处理节点为显示数据"""
        # 检查过滤条件
        if not self.field_filter.matches_filter(node):
            return {"name": node.name, "children": [], "visible": False}

        # 处理子节点
        children = []
        if node.children:
            # 自动展开前几层
            is_expanded = (
                depth < self.auto_expand_depth or node.name in self.expanded_nodes
            )

            for child in node.children:
                child_data = self._process_node(child, depth + 1)
                if child_data["visible"]:
                    children.append(child_data)

        return {
            "name": node.name,
            "value": node.get_display_value(),
            "type": node.field_type,
            "color": node.get_color(),
            "description": node.description if self.show_descriptions else "",
            "update_count": node.update_count,
            "last_update": node.last_update_time,
            "min_value": node.min_value,
            "max_value": node.max_value,
            "children": children,
            "visible": True,
            "expanded": node.name in self.expanded_nodes,
            "path": node.get_path(),
        }

    def toggle_node_expansion(self, node_path: str) -> None:
        """切换节点展开状态"""
        if node_path in self.expanded_nodes:
            self.expanded_nodes.remove(node_path)
        else:
            self.expanded_nodes.add(node_path)

    def expand_all(self) -> None:
        """展开所有节点"""
        self.expanded_nodes.clear()
        self._collect_all_paths(self.expanded_nodes)

    def collapse_all(self) -> None:
        """折叠所有节点"""
        self.expanded_nodes.clear()
        self.expanded_nodes.add("root")  # 保持根节点展开

    def _collect_all_paths(self, path_set: set) -> None:
        """收集所有节点路径"""
        for root in self.root_nodes.values():
            self._collect_paths_recursive(root, "", path_set)

    def _collect_paths_recursive(
        self, node: FieldTreeNode, current_path: str, path_set: set
    ) -> None:
        """递归收集节点路径"""
        full_path = f"{current_path}.{node.name}" if current_path else node.name
        path_set.add(full_path)

        for child in node.children:
            self._collect_paths_recursive(child, full_path, path_set)

    def find_node(self, path: str) -> Optional[FieldTreeNode]:
        """查找指定路径的节点"""
        # 解析协议名
        if "." in path:
            protocol_name, node_path = path.split(".", 1)
        else:
            return None

        if protocol_name not in self.root_nodes:
            return None

        root = self.root_nodes[protocol_name]
        return self._find_node_recursive(root, node_path)

    def _find_node_recursive(
        self, node: FieldTreeNode, path: str
    ) -> Optional[FieldTreeNode]:
        """递归查找节点"""
        if not path:
            return node

        if "." not in path:
            return node.find_child(path)

        first_part, remaining_path = path.split(".", 1)
        child = node.find_child(first_part)

        if not child:
            return None

        return self._find_node_recursive(child, remaining_path)

    def get_field_statistics(self) -> Dict[str, Any]:
        """获取字段统计信息"""
        total_fields = 0
        type_counts = defaultdict(int)
        update_counts = defaultdict(int)

        for root in self.root_nodes.values():
            stats = self._collect_node_statistics(root)
            total_fields += stats["total_fields"]

            for field_type, count in stats["type_counts"].items():
                type_counts[field_type] += count

            for update_count in stats["update_counts"].values():
                update_counts["total_updates"] += update_count
                if update_count > 0:
                    update_counts["updated_fields"] += 1

        return {
            "total_fields": total_fields,
            "type_distribution": dict(type_counts),
            "update_statistics": dict(update_counts),
            "protocol_count": len(self.root_nodes),
        }

    def _collect_node_statistics(self, node: FieldTreeNode) -> Dict[str, Any]:
        """收集节点统计信息"""
        stats = {
            "total_fields": 1,
            "type_counts": defaultdict(int),
            "update_counts": defaultdict(int),
        }

        stats["type_counts"][node.field_type] += 1
        stats["update_counts"][node.update_count] = node.update_count

        for child in node.children:
            child_stats = self._collect_node_statistics(child)
            stats["total_fields"] += child_stats["total_fields"]

            for field_type, count in child_stats["type_counts"].items():
                stats["type_counts"][field_type] += count

            for update_count in child_stats["update_counts"].items():
                stats["update_counts"][update_count] += update_count

        return stats

    def export_field_structure(
        self, filename: str, protocol_name: Optional[str] = None
    ) -> bool:
        """导出字段结构"""
        try:
            import json

            export_data = {}

            protocols_to_export = (
                [protocol_name] if protocol_name else list(self.root_nodes.keys())
            )

            for proto_name in protocols_to_export:
                if proto_name in self.root_nodes:
                    root = self.root_nodes[proto_name]
                    export_data[proto_name] = self._node_to_dict(root)

            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Field structure exported to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to export field structure: {e}")
            return False

    def _node_to_dict(self, node: FieldTreeNode) -> Dict[str, Any]:
        """将节点转换为字典"""
        result = {
            "name": node.name,
            "type": node.field_type,
            "description": node.description,
            "update_count": node.update_count,
            "last_update": node.last_update_time,
            "children": [],
        }

        if node.value is not None:
            result["value"] = node.get_display_value()

        if node.min_value is not None:
            result["min_value"] = node.min_value

        if node.max_value is not None:
            result["max_value"] = node.max_value

        for child in node.children:
            result["children"].append(self._node_to_dict(child))

        return result


# 工厂函数
def create_field_panel(width: int = 400, height: int = 600) -> FieldPanel:
    """创建字段面板"""
    return FieldPanel(width, height)


def create_field_filter() -> FieldFilter:
    """创建字段过滤器"""
    return FieldFilter()
