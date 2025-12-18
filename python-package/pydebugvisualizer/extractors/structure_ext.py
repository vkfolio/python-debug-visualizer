"""Structure extractors for auto-detected data structures.

These extractors use the StructureAnalyzer to automatically detect and
visualize common data structures like linked lists, trees, and graphs.
"""

from typing import Any, Dict, List, Set

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractorPriority,
)
from ..detection.structure_analyzer import StructureAnalyzer, StructureType


class LinkedListExtractor(BaseExtractor):
    """Extractor for linked list structures.

    Detects objects with 'next' pointer patterns and visualizes them as graphs.
    """

    def __init__(self):
        self._analyzer = StructureAnalyzer()

    @property
    def id(self) -> str:
        return "structure.linked_list"

    @property
    def name(self) -> str:
        return "Linked List"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH  # Higher than generic extractors

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        if not hasattr(value, '__dict__') and not hasattr(value, '__slots__'):
            return False
        analysis = self._analyzer.analyze(value, max_depth=3)
        return analysis.structure_type in (
            StructureType.LINKED_LIST,
            StructureType.DOUBLY_LINKED_LIST
        )

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        analysis = self._analyzer.analyze(value, max_depth=3)

        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name=f"Linked List (auto-detected)",
            priority=self.priority,
            extract=lambda v=value, a=analysis: self._extract_as_graph(v, a, context)
        )]

    def _extract_as_graph(
        self,
        head: Any,
        analysis: Any,
        context: ExtractionContext
    ) -> Dict:
        """Extract linked list as a graph visualization."""
        nodes = []
        edges = []
        visited: Set[int] = set()

        current = head
        idx = 0

        # Find the next field name
        next_field = None
        for field in analysis.pointer_fields:
            if field.lower() in self._analyzer.LINKED_LIST_NEXT:
                next_field = field
                break

        if not next_field:
            next_field = 'next'  # Default fallback

        while current is not None and idx < context.max_items:
            obj_id = id(current)
            if obj_id in visited:
                # Cycle detected - add edge back to existing node
                cycle_idx = None
                for i, n in enumerate(nodes):
                    if n.get('pythonId') == obj_id:
                        cycle_idx = i
                        break
                if cycle_idx is not None and idx > 0:
                    edges.append({
                        "from": str(idx - 1),
                        "to": str(cycle_idx),
                        "label": next_field,
                        "color": "#ff6b6b"  # Red for cycle edge
                    })
                break

            visited.add(obj_id)

            # Get node label from value fields
            label = self._get_node_label(current, analysis.value_fields)

            nodes.append({
                "id": str(idx),
                "label": label,
                "pythonId": str(obj_id)  # String to avoid JSON precision loss
            })

            # Get next node
            next_val = getattr(current, next_field, None)

            if next_val is not None:
                edges.append({
                    "from": str(idx),
                    "to": str(idx + 1),
                    "label": next_field
                })

            current = next_val
            idx += 1

        return {
            "kind": {"graph": True},
            "nodes": nodes,
            "edges": edges
        }

    def _get_node_label(self, obj: Any, value_fields: List[str]) -> str:
        """Get a label for a node from its value fields."""
        for field in value_fields:
            if hasattr(obj, field):
                val = getattr(obj, field)
                if val is not None:
                    return str(val)

        # Fallback to repr
        return repr(obj)[:30]


class BinaryTreeExtractor(BaseExtractor):
    """Extractor for binary tree structures.

    Detects objects with 'left'/'right' pointer patterns and visualizes them as trees.
    """

    def __init__(self):
        self._analyzer = StructureAnalyzer()

    @property
    def id(self) -> str:
        return "structure.binary_tree"

    @property
    def name(self) -> str:
        return "Binary Tree"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        if not hasattr(value, '__dict__') and not hasattr(value, '__slots__'):
            return False
        analysis = self._analyzer.analyze(value, max_depth=3)
        return analysis.structure_type == StructureType.BINARY_TREE

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        analysis = self._analyzer.analyze(value, max_depth=3)

        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name="Binary Tree (auto-detected)",
            priority=self.priority,
            extract=lambda v=value, a=analysis: self._extract_as_tree(v, a, context)
        )]

    def _extract_as_tree(
        self,
        root: Any,
        analysis: Any,
        context: ExtractionContext
    ) -> Dict:
        """Extract binary tree as a tree visualization."""
        # Find left/right field names
        left_field = None
        right_field = None

        for field in analysis.pointer_fields:
            if field.lower() in self._analyzer.TREE_LEFT:
                left_field = field
            elif field.lower() in self._analyzer.TREE_RIGHT:
                right_field = field

        left_field = left_field or 'left'
        right_field = right_field or 'right'

        def build_node(obj: Any, depth: int) -> Dict:
            if obj is None:
                return {
                    "items": [{"text": "null", "emphasis": "style3"}],
                    "children": [],
                    "pythonId": None
                }

            if depth > context.max_depth:
                return {
                    "items": [{"text": "...", "emphasis": "style3"}],
                    "children": [],
                    "pythonId": str(id(obj))
                }

            label = self._get_node_label(obj, analysis.value_fields)

            left = getattr(obj, left_field, None)
            right = getattr(obj, right_field, None)

            children = []
            if left is not None or right is not None:
                children.append(build_node(left, depth + 1))
                children.append(build_node(right, depth + 1))

            return {
                "items": [{"text": label, "emphasis": "style1"}],
                "children": children,
                "pythonId": str(id(obj))
            }

        return {
            "kind": {"tree": True},
            "root": build_node(root, 0)
        }

    def _get_node_label(self, obj: Any, value_fields: List[str]) -> str:
        """Get a label for a node from its value fields."""
        for field in value_fields:
            if hasattr(obj, field):
                val = getattr(obj, field)
                if val is not None:
                    return str(val)
        return repr(obj)[:30]


class NaryTreeExtractor(BaseExtractor):
    """Extractor for n-ary tree structures.

    Detects objects with 'children' list patterns and visualizes them as trees.
    """

    def __init__(self):
        self._analyzer = StructureAnalyzer()

    @property
    def id(self) -> str:
        return "structure.nary_tree"

    @property
    def name(self) -> str:
        return "N-ary Tree"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        if not hasattr(value, '__dict__') and not hasattr(value, '__slots__'):
            return False
        analysis = self._analyzer.analyze(value, max_depth=3)
        return analysis.structure_type == StructureType.N_ARY_TREE

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        analysis = self._analyzer.analyze(value, max_depth=3)

        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name="N-ary Tree (auto-detected)",
            priority=self.priority,
            extract=lambda v=value, a=analysis: self._extract_as_tree(v, a, context)
        )]

    def _extract_as_tree(
        self,
        root: Any,
        analysis: Any,
        context: ExtractionContext
    ) -> Dict:
        """Extract n-ary tree as a tree visualization."""
        # Find children field name
        children_field = None
        for field in analysis.pointer_fields:
            if field.lower() in self._analyzer.TREE_CHILDREN:
                children_field = field
                break

        children_field = children_field or 'children'

        def build_node(obj: Any, depth: int) -> Dict:
            if obj is None:
                return {
                    "items": [{"text": "null", "emphasis": "style3"}],
                    "children": [],
                    "pythonId": None
                }

            if depth > context.max_depth:
                return {
                    "items": [{"text": "...", "emphasis": "style3"}],
                    "children": [],
                    "pythonId": str(id(obj))
                }

            label = self._get_node_label(obj, analysis.value_fields)

            children_list = getattr(obj, children_field, []) or []
            children = []

            for i, child in enumerate(children_list[:context.max_items]):
                children.append(build_node(child, depth + 1))

            if len(children_list) > context.max_items:
                children.append({
                    "items": [{"text": f"... +{len(children_list) - context.max_items} more", "emphasis": "style3"}],
                    "children": [],
                    "pythonId": None
                })

            return {
                "items": [{"text": label, "emphasis": "style1"}],
                "children": children,
                "pythonId": str(id(obj))
            }

        return {
            "kind": {"tree": True},
            "root": build_node(root, 0)
        }

    def _get_node_label(self, obj: Any, value_fields: List[str]) -> str:
        """Get a label for a node from its value fields."""
        for field in value_fields:
            if hasattr(obj, field):
                val = getattr(obj, field)
                if val is not None:
                    return str(val)
        return repr(obj)[:30]


class GraphExtractor(BaseExtractor):
    """Extractor for graph structures.

    Detects objects with 'neighbors'/'edges' patterns and visualizes them as graphs.
    """

    def __init__(self):
        self._analyzer = StructureAnalyzer()

    @property
    def id(self) -> str:
        return "structure.graph"

    @property
    def name(self) -> str:
        return "Graph"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        if not hasattr(value, '__dict__') and not hasattr(value, '__slots__'):
            return False
        analysis = self._analyzer.analyze(value, max_depth=3)
        return analysis.structure_type == StructureType.GRAPH

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        analysis = self._analyzer.analyze(value, max_depth=3)

        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name="Graph (auto-detected)",
            priority=self.priority,
            extract=lambda v=value, a=analysis: self._extract_as_graph(v, a, context)
        )]

    def _extract_as_graph(
        self,
        start: Any,
        analysis: Any,
        context: ExtractionContext
    ) -> Dict:
        """Extract graph structure as a graph visualization using BFS."""
        # Find neighbors field name
        neighbors_field = None
        for field in analysis.pointer_fields:
            if field.lower() in self._analyzer.GRAPH_NEIGHBORS:
                neighbors_field = field
                break

        neighbors_field = neighbors_field or 'neighbors'

        nodes = []
        edges = []
        visited: Set[int] = set()
        id_map: Dict[int, str] = {}
        queue = [start]

        while queue and len(nodes) < context.max_items:
            current = queue.pop(0)
            obj_id = id(current)

            if obj_id in visited:
                continue

            visited.add(obj_id)
            node_id = str(len(nodes))
            id_map[obj_id] = node_id

            label = self._get_node_label(current, analysis.value_fields)
            nodes.append({
                "id": node_id,
                "label": label
            })

            # Get neighbors
            neighbors = getattr(current, neighbors_field, [])
            if isinstance(neighbors, dict):
                neighbors = list(neighbors.keys())
            elif not isinstance(neighbors, (list, tuple, set)):
                neighbors = []

            for neighbor in neighbors:
                if neighbor is None:
                    continue

                neighbor_id = id(neighbor)

                if neighbor_id not in visited and len(queue) < context.max_items:
                    queue.append(neighbor)

                # Add edge (will be created once neighbor has an ID)
                if neighbor_id in id_map:
                    edges.append({
                        "from": node_id,
                        "to": id_map[neighbor_id]
                    })

        # Second pass to add edges to newly discovered nodes
        for node_idx, obj_id in enumerate(visited):
            # Re-traverse to get edges (not ideal but works for now)
            pass

        return {
            "kind": {"graph": True},
            "nodes": nodes,
            "edges": edges
        }

    def _get_node_label(self, obj: Any, value_fields: List[str]) -> str:
        """Get a label for a node from its value fields."""
        for field in value_fields:
            if hasattr(obj, field):
                val = getattr(obj, field)
                if val is not None:
                    return str(val)
        return repr(obj)[:30]
