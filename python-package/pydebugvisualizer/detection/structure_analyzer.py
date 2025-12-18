"""Structure analyzer for detecting data structure patterns.

This module provides automatic detection of common data structure patterns
like linked lists, binary trees, n-ary trees, and graphs.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class StructureType(Enum):
    """Types of data structures that can be detected."""
    LINKED_LIST = "linked_list"
    DOUBLY_LINKED_LIST = "doubly_linked_list"
    BINARY_TREE = "binary_tree"
    N_ARY_TREE = "n_ary_tree"
    GRAPH = "graph"
    UNKNOWN = "unknown"


@dataclass
class StructureAnalysis:
    """Result of structure analysis.

    Attributes:
        structure_type: The detected structure type
        confidence: Confidence score from 0.0 to 1.0
        pointer_fields: Fields that point to other nodes
        value_fields: Fields that contain values
    """
    structure_type: StructureType
    confidence: float
    pointer_fields: List[str]
    value_fields: List[str]


class StructureAnalyzer:
    """Analyzes objects to detect common data structure patterns.

    The analyzer uses heuristic field name analysis combined with
    structural verification to identify data structures.

    Example:
        analyzer = StructureAnalyzer()
        analysis = analyzer.analyze(my_linked_list_node)
        if analysis.structure_type == StructureType.LINKED_LIST:
            print("It's a linked list!")
    """

    # Common field names for different structures
    LINKED_LIST_NEXT = {'next', 'next_node', 'successor', 'link', 'tail', '_next'}
    LINKED_LIST_PREV = {'prev', 'previous', 'prev_node', 'predecessor', '_prev'}
    TREE_CHILDREN = {'children', 'child_nodes', 'kids', '_children'}
    TREE_LEFT = {'left', 'left_child', 'lchild', 'l', '_left'}
    TREE_RIGHT = {'right', 'right_child', 'rchild', 'r', '_right'}
    TREE_PARENT = {'parent', 'parent_node', 'p', '_parent'}
    GRAPH_NEIGHBORS = {'neighbors', 'adjacent', 'edges', 'connections', 'adjacency_list', '_neighbors'}
    VALUE_FIELDS = {'val', 'value', 'data', 'key', 'item', 'name', 'label', '_value', '_data'}

    def analyze(self, obj: Any, max_depth: int = 5) -> StructureAnalysis:
        """Analyze an object to determine its structure type.

        Args:
            obj: The object to analyze
            max_depth: Maximum depth to traverse for verification

        Returns:
            StructureAnalysis with detected type and metadata
        """
        if not self._has_attributes(obj):
            return StructureAnalysis(
                structure_type=StructureType.UNKNOWN,
                confidence=0.0,
                pointer_fields=[],
                value_fields=[]
            )

        fields = self._get_fields(obj)
        field_names = set(f.lower() for f in fields.keys())

        # Check for linked list pattern
        if self._is_doubly_linked_list(obj, fields, field_names, max_depth):
            next_fields = [f for f in fields if f.lower() in self.LINKED_LIST_NEXT]
            prev_fields = [f for f in fields if f.lower() in self.LINKED_LIST_PREV]
            pointer_fields = next_fields + prev_fields
            value_fields = [f for f in fields if f not in pointer_fields]
            return StructureAnalysis(
                structure_type=StructureType.DOUBLY_LINKED_LIST,
                confidence=0.9,
                pointer_fields=pointer_fields,
                value_fields=value_fields
            )

        if self._is_linked_list(obj, fields, field_names, max_depth):
            pointer_fields = [f for f in fields if f.lower() in self.LINKED_LIST_NEXT]
            value_fields = [f for f in fields if f not in pointer_fields]
            return StructureAnalysis(
                structure_type=StructureType.LINKED_LIST,
                confidence=0.9,
                pointer_fields=pointer_fields,
                value_fields=value_fields
            )

        # Check for binary tree pattern
        if self._is_binary_tree(obj, fields, field_names, max_depth):
            pointer_fields = [f for f in fields if f.lower() in self.TREE_LEFT | self.TREE_RIGHT | self.TREE_PARENT]
            value_fields = [f for f in fields if f not in pointer_fields]
            return StructureAnalysis(
                structure_type=StructureType.BINARY_TREE,
                confidence=0.9,
                pointer_fields=pointer_fields,
                value_fields=value_fields
            )

        # Check for n-ary tree pattern
        if self._is_nary_tree(obj, fields, field_names, max_depth):
            pointer_fields = [f for f in fields if f.lower() in self.TREE_CHILDREN | self.TREE_PARENT]
            value_fields = [f for f in fields if f not in pointer_fields]
            return StructureAnalysis(
                structure_type=StructureType.N_ARY_TREE,
                confidence=0.8,
                pointer_fields=pointer_fields,
                value_fields=value_fields
            )

        # Check for graph pattern
        if self._is_graph(obj, fields, field_names):
            pointer_fields = [f for f in fields if f.lower() in self.GRAPH_NEIGHBORS]
            value_fields = [f for f in fields if f not in pointer_fields]
            return StructureAnalysis(
                structure_type=StructureType.GRAPH,
                confidence=0.7,
                pointer_fields=pointer_fields,
                value_fields=value_fields
            )

        return StructureAnalysis(
            structure_type=StructureType.UNKNOWN,
            confidence=0.0,
            pointer_fields=[],
            value_fields=list(fields.keys())
        )

    def _has_attributes(self, obj: Any) -> bool:
        """Check if object has attributes to analyze."""
        return hasattr(obj, '__dict__') or hasattr(obj, '__slots__')

    def _get_fields(self, obj: Any) -> Dict[str, Any]:
        """Get all fields of an object."""
        fields = {}

        # Get __dict__ attributes
        if hasattr(obj, '__dict__'):
            fields.update(obj.__dict__)

        # Get __slots__ attributes
        if hasattr(obj, '__slots__'):
            for slot in obj.__slots__:
                if hasattr(obj, slot):
                    fields[slot] = getattr(obj, slot)

        return fields

    def _is_linked_list(
        self,
        obj: Any,
        fields: Dict[str, Any],
        field_names: Set[str],
        max_depth: int
    ) -> bool:
        """Check if object follows linked list pattern."""
        # Must have a 'next' field
        next_fields = field_names & self.LINKED_LIST_NEXT
        if not next_fields:
            return False

        # The next field should point to same type or None
        for field_name in fields:
            if field_name.lower() in next_fields:
                next_val = fields[field_name]
                if next_val is not None and type(next_val) != type(obj):
                    return False

        # Verify it's a linear chain (no branching)
        next_field = next(f for f in fields if f.lower() in next_fields)
        return self._verify_linear_chain(obj, next_field, max_depth)

    def _is_doubly_linked_list(
        self,
        obj: Any,
        fields: Dict[str, Any],
        field_names: Set[str],
        max_depth: int
    ) -> bool:
        """Check if object follows doubly linked list pattern."""
        # Must have both next and prev fields
        has_next = bool(field_names & self.LINKED_LIST_NEXT)
        has_prev = bool(field_names & self.LINKED_LIST_PREV)

        if not (has_next and has_prev):
            return False

        # Both should point to same type or None
        for field_name in fields:
            if field_name.lower() in self.LINKED_LIST_NEXT | self.LINKED_LIST_PREV:
                val = fields[field_name]
                if val is not None and type(val) != type(obj):
                    return False

        return True

    def _is_binary_tree(
        self,
        obj: Any,
        fields: Dict[str, Any],
        field_names: Set[str],
        max_depth: int
    ) -> bool:
        """Check if object follows binary tree pattern."""
        # Must have both left and right fields
        has_left = bool(field_names & self.TREE_LEFT)
        has_right = bool(field_names & self.TREE_RIGHT)

        if not (has_left and has_right):
            return False

        # Both should point to same type or None
        for field_name in fields:
            if field_name.lower() in self.TREE_LEFT | self.TREE_RIGHT:
                child = fields[field_name]
                if child is not None and type(child) != type(obj):
                    return False

        return True

    def _is_nary_tree(
        self,
        obj: Any,
        fields: Dict[str, Any],
        field_names: Set[str],
        max_depth: int
    ) -> bool:
        """Check if object follows n-ary tree pattern."""
        children_fields = field_names & self.TREE_CHILDREN
        if not children_fields:
            return False

        for field_name in fields:
            if field_name.lower() in children_fields:
                children = fields[field_name]
                if isinstance(children, (list, tuple)):
                    # All children should be same type as parent (or None)
                    if children:
                        valid_children = [c for c in children if c is not None]
                        if valid_children and all(type(c) == type(obj) for c in valid_children):
                            return True

        return False

    def _is_graph(self, obj: Any, fields: Dict[str, Any], field_names: Set[str]) -> bool:
        """Check if object follows graph pattern."""
        neighbor_fields = field_names & self.GRAPH_NEIGHBORS
        if not neighbor_fields:
            return False

        for field_name in fields:
            if field_name.lower() in neighbor_fields:
                neighbors = fields[field_name]
                if isinstance(neighbors, (list, tuple, set)):
                    # Neighbors should be same type
                    if neighbors:
                        valid_neighbors = [n for n in neighbors if n is not None]
                        if valid_neighbors and all(type(n) == type(obj) for n in valid_neighbors):
                            return True
                elif isinstance(neighbors, dict):
                    # Adjacency dict: {node: weight} or {node: edge_data}
                    if neighbors:
                        return True

        return False

    def _verify_linear_chain(
        self,
        obj: Any,
        next_field: str,
        max_depth: int
    ) -> bool:
        """Verify the structure forms a linear chain (no cycles within depth)."""
        visited: Set[int] = set()
        current = obj
        depth = 0

        while current is not None and depth < max_depth:
            obj_id = id(current)
            if obj_id in visited:
                return True  # Cycle detected - still a linked list (circular)
            visited.add(obj_id)

            fields = self._get_fields(current)
            current = fields.get(next_field)
            depth += 1

        return True
