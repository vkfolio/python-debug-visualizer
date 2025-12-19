"""Built-in type extractors for Python's standard types."""

from typing import Any, Dict, List, Set, Tuple

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractorPriority,
)


class ListExtractor(BaseExtractor):
    """Extractor for Python lists.

    Provides multiple visualization options:
    - Tree view (default): Hierarchical display of nested structures
    - Table view: For lists of dictionaries (records)
    - Grid view: For lists of lists (2D arrays)
    """

    @property
    def id(self) -> str:
        return "builtin.list"

    @property
    def name(self) -> str:
        return "List"

    @property
    def priority(self) -> int:
        return ExtractorPriority.MEDIUM

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        return isinstance(value, list)

    def get_extractions(
        self,
        value: list,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        candidates = []

        # Table view for list of dicts (records)
        if value and all(isinstance(item, dict) for item in value[:10]):
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.table",
                extractor_name="List as Table",
                priority=self.priority + 50,
                extract=lambda v=value: self._extract_as_table(v, context)
            ))

        # Grid view for list of lists (2D array-like)
        if value and all(isinstance(item, (list, tuple)) for item in value[:10]):
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.grid",
                extractor_name="List as Grid",
                priority=self.priority + 40,
                extract=lambda v=value: self._extract_as_grid(v, context)
            ))

        # Array view for 1D arrays (supports index markers for two-pointer algorithms)
        if value and not all(isinstance(item, (list, tuple, dict)) for item in value[:10]):
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.array",
                extractor_name="List as Array (pointer-friendly)",
                priority=self.priority + 60,  # Higher priority for simple lists
                extract=lambda v=value: self._extract_as_array(v, context)
            ))

        # Default tree view
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.tree",
            extractor_name="List as Tree",
            priority=self.priority,
            extract=lambda v=value: self._extract_as_tree(v, context)
        ))

        return candidates

    def _extract_as_array(self, value: list, context: ExtractionContext) -> Dict:
        """Extract list as an array visualization (supports index markers).

        This visualization is optimized for two-pointer algorithms where
        you want to highlight elements by their index position.
        """
        items = value[:context.max_items]
        elements = []

        for i, item in enumerate(items):
            elements.append({
                "index": i,
                "value": self._format_cell(item),
                "rawValue": item
            })

        # Add truncation indicator
        truncated = len(value) > context.max_items

        return {
            "kind": {"array": True},
            "elements": elements,
            "length": len(value),
            "truncated": truncated
        }

    def _extract_as_table(self, value: list, context: ExtractionContext) -> Dict:
        """Extract list of dicts as a table."""
        rows = value[:context.max_items]
        return {
            "kind": {"table": True},
            "rows": rows
        }

    def _extract_as_grid(self, value: list, context: ExtractionContext) -> Dict:
        """Extract list of lists as a grid."""
        rows = []
        max_cols = 0

        for i, row in enumerate(value[:context.max_items]):
            if isinstance(row, (list, tuple)):
                cols = [{"content": self._format_cell(cell)} for cell in row[:context.max_items]]
                max_cols = max(max_cols, len(cols))
                rows.append({
                    "label": str(i),
                    "columns": cols
                })

        return {
            "kind": {"grid": True},
            "rows": rows,
            "columnLabels": [{"label": str(j)} for j in range(max_cols)]
        }

    def _extract_as_tree(self, value: list, context: ExtractionContext) -> Dict:
        """Extract list as a tree structure."""
        return {
            "kind": {"tree": True},
            "root": self._build_tree_node(value, f"list[{len(value)}]", context, depth=0)
        }

    def _build_tree_node(
        self,
        value: Any,
        label: str,
        context: ExtractionContext,
        depth: int
    ) -> Dict:
        """Recursively build a tree node for the value."""
        if depth > context.max_depth:
            return {
                "items": [{"text": f"{label}: ...", "emphasis": "style3"}],
                "children": []
            }

        node = {
            "items": [{"text": label, "emphasis": "style1"}],
            "children": []
        }

        if isinstance(value, list):
            for i, item in enumerate(value[:context.max_items]):
                child_label = f"[{i}]"
                if isinstance(item, (list, dict, set, tuple)):
                    child = self._build_tree_node(item, child_label, context, depth + 1)
                else:
                    child = {
                        "items": [
                            {"text": child_label, "emphasis": "style2"},
                            {"text": f": {self._format_value(item)}"}
                        ],
                        "children": []
                    }
                node["children"].append(child)

            if len(value) > context.max_items:
                node["children"].append({
                    "items": [{"text": f"... and {len(value) - context.max_items} more items"}],
                    "children": []
                })

        elif isinstance(value, dict):
            for key, val in list(value.items())[:context.max_items]:
                child_label = str(key)
                if isinstance(val, (list, dict, set, tuple)):
                    child = self._build_tree_node(val, child_label, context, depth + 1)
                else:
                    child = {
                        "items": [
                            {"text": child_label, "emphasis": "style2"},
                            {"text": f": {self._format_value(val)}"}
                        ],
                        "children": []
                    }
                node["children"].append(child)

        elif isinstance(value, (set, frozenset)):
            for i, item in enumerate(list(value)[:context.max_items]):
                child = {
                    "items": [{"text": self._format_value(item)}],
                    "children": []
                }
                node["children"].append(child)

        elif isinstance(value, tuple):
            for i, item in enumerate(value[:context.max_items]):
                child_label = f"({i})"
                if isinstance(item, (list, dict, set, tuple)):
                    child = self._build_tree_node(item, child_label, context, depth + 1)
                else:
                    child = {
                        "items": [
                            {"text": child_label, "emphasis": "style2"},
                            {"text": f": {self._format_value(item)}"}
                        ],
                        "children": []
                    }
                node["children"].append(child)

        else:
            node["items"].append({"text": f": {self._format_value(value)}"})

        return node

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, str):
            if len(value) > 100:
                return f'"{value[:100]}..."'
            return f'"{value}"'
        return repr(value)

    def _format_cell(self, value: Any) -> str:
        """Format a cell value for grid display."""
        if isinstance(value, float):
            return f"{value:.6g}"
        if isinstance(value, str) and len(value) > 20:
            return f"{value[:20]}..."
        return str(value)


class DictExtractor(BaseExtractor):
    """Extractor for Python dictionaries.

    Provides multiple visualization options:
    - Direct passthrough: If dict is already visualization data
    - Tree view: Hierarchical display of nested structures
    - Table view: For dict of dicts (nested records)
    - Graph view: For object relationships
    """

    @property
    def id(self) -> str:
        return "builtin.dict"

    @property
    def name(self) -> str:
        return "Dictionary"

    @property
    def priority(self) -> int:
        return ExtractorPriority.MEDIUM

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        return isinstance(value, dict)

    def get_extractions(
        self,
        value: dict,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        candidates = []

        # Check if it's already visualization data (has 'kind' dict)
        if "kind" in value and isinstance(value.get("kind"), dict):
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.passthrough",
                extractor_name="Direct Visualization Data",
                priority=ExtractorPriority.OVERRIDE,
                extract=lambda v=value: v
            ))
            return candidates  # Return early - this is explicit visualization data

        # Table view for dict of dicts
        if value and all(isinstance(v, dict) for v in list(value.values())[:10]):
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.table",
                extractor_name="Dict as Table",
                priority=self.priority + 30,
                extract=lambda v=value: self._extract_as_table(v, context)
            ))

        # Tree view (default)
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.tree",
            extractor_name="Dict as Tree",
            priority=self.priority,
            extract=lambda v=value: self._extract_as_tree(v, context)
        ))

        # Key-value table view
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.kv_table",
            extractor_name="Dict as Key-Value Table",
            priority=self.priority - 10,
            extract=lambda v=value: self._extract_as_kv_table(v, context)
        ))

        return candidates

    def _extract_as_table(self, value: dict, context: ExtractionContext) -> Dict:
        """Extract dict of dicts as a table."""
        rows = []
        for key, val in list(value.items())[:context.max_items]:
            if isinstance(val, dict):
                row = {"_key": str(key), **val}
                rows.append(row)
        return {
            "kind": {"table": True},
            "rows": rows
        }

    def _extract_as_kv_table(self, value: dict, context: ExtractionContext) -> Dict:
        """Extract dict as a key-value table."""
        rows = []
        for key, val in list(value.items())[:context.max_items]:
            rows.append({
                "key": str(key),
                "value": self._format_value(val),
                "type": type(val).__name__
            })
        return {
            "kind": {"table": True},
            "rows": rows
        }

    def _extract_as_tree(self, value: dict, context: ExtractionContext) -> Dict:
        """Extract dict as a tree structure."""
        # Reuse list extractor's tree building logic
        list_extractor = ListExtractor()
        return {
            "kind": {"tree": True},
            "root": list_extractor._build_tree_node(
                value,
                f"dict[{len(value)}]",
                context,
                depth=0
            )
        }

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, str):
            if len(value) > 50:
                return f'"{value[:50]}..."'
            return f'"{value}"'
        if isinstance(value, (list, dict, set, tuple)):
            type_name = type(value).__name__
            return f"<{type_name}[{len(value)}]>"
        return repr(value)


class SetExtractor(BaseExtractor):
    """Extractor for Python sets and frozensets."""

    @property
    def id(self) -> str:
        return "builtin.set"

    @property
    def name(self) -> str:
        return "Set"

    @property
    def priority(self) -> int:
        return ExtractorPriority.MEDIUM

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        return isinstance(value, (set, frozenset))

    def get_extractions(
        self,
        value: Set,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        candidates = []

        # Grid view (default for sets)
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.grid",
            extractor_name="Set as Grid",
            priority=self.priority,
            extract=lambda v=value: self._extract_as_grid(v, context)
        ))

        # Tree view
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.tree",
            extractor_name="Set as Tree",
            priority=self.priority - 10,
            extract=lambda v=value: self._extract_as_tree(v, context)
        ))

        return candidates

    def _extract_as_grid(self, value: Set, context: ExtractionContext) -> Dict:
        """Extract set as a single-row grid."""
        items = list(value)[:context.max_items]
        columns = [{"content": self._format_value(item)} for item in items]

        type_name = "frozenset" if isinstance(value, frozenset) else "set"
        return {
            "kind": {"grid": True},
            "rows": [{
                "label": f"{type_name}[{len(value)}]",
                "columns": columns
            }]
        }

    def _extract_as_tree(self, value: Set, context: ExtractionContext) -> Dict:
        """Extract set as a tree structure."""
        type_name = "frozenset" if isinstance(value, frozenset) else "set"
        items = list(value)[:context.max_items]

        children = []
        for item in items:
            children.append({
                "items": [{"text": self._format_value(item)}],
                "children": []
            })

        if len(value) > context.max_items:
            children.append({
                "items": [{"text": f"... and {len(value) - context.max_items} more items"}],
                "children": []
            })

        return {
            "kind": {"tree": True},
            "root": {
                "items": [{"text": f"{type_name}[{len(value)}]", "emphasis": "style1"}],
                "children": children
            }
        }

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, str):
            if len(value) > 30:
                return f'"{value[:30]}..."'
            return f'"{value}"'
        return repr(value)


class TupleExtractor(BaseExtractor):
    """Extractor for Python tuples."""

    @property
    def id(self) -> str:
        return "builtin.tuple"

    @property
    def name(self) -> str:
        return "Tuple"

    @property
    def priority(self) -> int:
        return ExtractorPriority.MEDIUM

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        return isinstance(value, tuple)

    def get_extractions(
        self,
        value: Tuple,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        candidates = []

        # Grid view (default for tuples)
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.grid",
            extractor_name="Tuple as Grid",
            priority=self.priority,
            extract=lambda v=value: self._extract_as_grid(v, context)
        ))

        # Tree view
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.tree",
            extractor_name="Tuple as Tree",
            priority=self.priority - 10,
            extract=lambda v=value: self._extract_as_tree(v, context)
        ))

        return candidates

    def _extract_as_grid(self, value: Tuple, context: ExtractionContext) -> Dict:
        """Extract tuple as a single-row grid."""
        items = value[:context.max_items]
        columns = [{"content": self._format_value(item)} for item in items]

        return {
            "kind": {"grid": True},
            "columnLabels": [{"label": str(i)} for i in range(len(items))],
            "rows": [{
                "label": f"tuple[{len(value)}]",
                "columns": columns
            }]
        }

    def _extract_as_tree(self, value: Tuple, context: ExtractionContext) -> Dict:
        """Extract tuple as a tree structure."""
        list_extractor = ListExtractor()
        return {
            "kind": {"tree": True},
            "root": list_extractor._build_tree_node(
                value,
                f"tuple[{len(value)}]",
                context,
                depth=0
            )
        }

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, str):
            if len(value) > 30:
                return f'"{value[:30]}..."'
            return f'"{value}"'
        if isinstance(value, float):
            return f"{value:.6g}"
        return repr(value)


class StringExtractor(BaseExtractor):
    """Extractor for Python strings."""

    @property
    def id(self) -> str:
        return "builtin.str"

    @property
    def name(self) -> str:
        return "String"

    @property
    def priority(self) -> int:
        return ExtractorPriority.LOW  # Lower priority - usually repr is fine

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        return isinstance(value, str)

    def get_extractions(
        self,
        value: str,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        candidates = []

        # Array view (highest priority for algorithm visualization)
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.array",
            extractor_name="String as Array (for pointer tracking)",
            priority=self.priority + 100,
            extract=lambda v=value: self._extract_as_array(v, context)
        ))

        # Text view
        candidates.append(ExtractionCandidate(
            extractor_id=f"{self.id}.text",
            extractor_name="String as Text",
            priority=self.priority,
            extract=lambda v=value: self._extract_as_text(v, context)
        ))

        # Try to parse as JSON
        if self._looks_like_json(value):
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.json",
                extractor_name="String as JSON",
                priority=self.priority + 50,
                extract=lambda v=value: self._extract_as_json(v, context)
            ))

        return candidates

    def _extract_as_array(self, value: str, context: ExtractionContext) -> Dict:
        """Extract string as array visualization for pointer tracking."""
        chars = list(value[:context.max_items])
        elements = []
        for i, char in enumerate(chars):
            elements.append({
                "index": i,
                "value": repr(char),  # Show with quotes like '1' or '0'
                "rawValue": char
            })
        return {
            "kind": {"array": True},
            "elements": elements,
            "length": len(value),
            "truncated": len(value) > context.max_items
        }

    def _extract_as_text(self, value: str, context: ExtractionContext) -> Dict:
        """Extract string as text visualization."""
        # Detect if it might be code based on content
        file_name = None
        if "def " in value or "class " in value or "import " in value:
            file_name = "code.py"
        elif "function " in value or "const " in value or "let " in value:
            file_name = "code.js"
        elif "{" in value and "}" in value and ":" in value:
            file_name = "data.json"

        result = {
            "kind": {"text": True},
            "text": value
        }
        if file_name:
            result["fileName"] = file_name

        return result

    def _extract_as_json(self, value: str, context: ExtractionContext) -> Dict:
        """Extract string as parsed JSON."""
        import json
        try:
            parsed = json.loads(value)
            # Recursively extract the parsed JSON
            if isinstance(parsed, dict):
                extractor = DictExtractor()
                if extractor.can_extract(parsed, context):
                    extractions = extractor.get_extractions(parsed, context)
                    if extractions:
                        return extractions[0].extract()
            elif isinstance(parsed, list):
                extractor = ListExtractor()
                if extractor.can_extract(parsed, context):
                    extractions = extractor.get_extractions(parsed, context)
                    if extractions:
                        return extractions[0].extract()

            # Fallback to formatted JSON text
            return {
                "kind": {"text": True},
                "text": json.dumps(parsed, indent=2),
                "fileName": "data.json"
            }
        except json.JSONDecodeError:
            return {
                "kind": {"text": True},
                "text": value
            }

    def _looks_like_json(self, value: str) -> bool:
        """Check if string looks like it might be JSON."""
        value = value.strip()
        return (
            (value.startswith("{") and value.endswith("}")) or
            (value.startswith("[") and value.endswith("]"))
        )


class FallbackExtractor(BaseExtractor):
    """Fallback extractor that uses repr() for any value.

    This is the lowest priority extractor that will match any value,
    ensuring there's always some visualization available.
    """

    @property
    def id(self) -> str:
        return "builtin.fallback"

    @property
    def name(self) -> str:
        return "Fallback (repr)"

    @property
    def priority(self) -> int:
        return ExtractorPriority.FALLBACK

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        return True  # Matches anything

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name=f"repr({type(value).__name__})",
            priority=self.priority,
            extract=lambda v=value: {
                "kind": {"text": True},
                "text": repr(v)
            }
        )]


class MazeExtractor(BaseExtractor):
    """Extractor for maze/grid algorithm visualization.

    Supports:
    - Plain 2D array of 0s (path) and 1s (wall)
    - Dict format: {"maze": [[...]], "path": [...], "visited": set(), "current": (r,c)}

    Visualizes with colors:
    - Walls: dark gray (#333333)
    - Paths: white (#e8e8e8)
    - Visited cells: light blue (#90caf9)
    - Current path: green (#4caf50)
    - Current position: yellow with animation (#ffc107)
    """

    @property
    def id(self) -> str:
        return "builtin.maze"

    @property
    def name(self) -> str:
        return "Maze Visualizer"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH  # Higher priority for maze-like data

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        # Check for dict format with "maze" key
        if isinstance(value, dict) and "maze" in value:
            maze = value.get("maze")
            if isinstance(maze, list) and maze and isinstance(maze[0], list):
                return True

        # Check for plain 2D array of 0s and 1s
        if isinstance(value, list) and value and isinstance(value[0], list):
            first_row = value[0]
            if first_row and all(v in (0, 1) for v in first_row[:20]):
                return True

        return False

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        candidates = []

        candidates.append(ExtractionCandidate(
            extractor_id=self.id,
            extractor_name="Maze Grid",
            priority=self.priority,
            extract=lambda v=value: self._extract_maze(v, context)
        ))

        return candidates

    def _extract_maze(self, value: Any, context: ExtractionContext) -> Dict:
        """Extract maze data into grid visualization format."""
        # Parse input - either dict with maze key or plain 2D array
        if isinstance(value, dict) and "maze" in value:
            maze = value["maze"]
            path = value.get("path", [])
            visited = value.get("visited", set())
            current = value.get("current", None)
            start = value.get("start", None)
            end = value.get("end", None) or value.get("goal", None)
        else:
            maze = value
            path = []
            visited = set()
            current = None
            start = None
            end = None

        # Convert visited to set if it's a list
        if isinstance(visited, list):
            visited = set(tuple(v) if isinstance(v, list) else v for v in visited)

        # Convert path elements to tuples if they're lists
        if path:
            path = [tuple(p) if isinstance(p, list) else p for p in path]
        path_set = set(path)

        # Convert start and end to tuples
        if start and isinstance(start, list):
            start = tuple(start)
        if end and isinstance(end, list):
            end = tuple(end)

        # Build grid rows with colors
        rows = []
        markers = []

        for row_idx, row in enumerate(maze[:context.max_items]):
            columns = []
            for col_idx, cell in enumerate(row[:context.max_items]):
                pos = (row_idx, col_idx)

                # Determine cell color and content based on state
                if cell == 1:
                    # Wall
                    color = "#333333"
                    content = "█"
                elif pos == start:
                    # Start position - bright green
                    color = "#4caf50"
                    content = "S"
                elif pos == end:
                    # Goal position - bright red/orange
                    color = "#ff5722"
                    content = "G"
                elif pos in path_set:
                    # In current path - green trail
                    color = "#81c784"
                    content = "○"
                elif pos in visited:
                    # Visited but not in path - light blue
                    color = "#64b5f6"
                    content = "·"
                else:
                    # Open path - light
                    color = "#e8e8e8"
                    content = ""

                columns.append({
                    "content": content,
                    "color": color
                })

            rows.append({
                "label": str(row_idx),
                "columns": columns
            })

        # Add marker for start position
        if start:
            markers.append({
                "id": "start",
                "row": start[0],
                "column": start[1],
                "color": "#4caf50",
                "label": "S"
            })

        # Add marker for goal/end position
        if end:
            markers.append({
                "id": "goal",
                "row": end[0],
                "column": end[1],
                "color": "#ff5722",
                "label": "G"
            })

        # Add marker for current position (takes priority visually)
        if current:
            current = tuple(current) if isinstance(current, list) else current
            markers.append({
                "id": "current",
                "row": current[0],
                "column": current[1],
                "color": "#ffc107",
                "label": "→"
            })

        # Add path step numbers (skip start and end as they have their own labels)
        for i, pos in enumerate(path):
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                pos_tuple = (pos[0], pos[1])
                # Skip start and end positions - they already have labels
                if pos_tuple == start or pos_tuple == end:
                    continue
                row, col = pos[0], pos[1]
                if row < len(maze) and col < len(maze[0]):
                    markers.append({
                        "id": f"path_{i}",
                        "row": row,
                        "column": col,
                        "color": "#81c784",
                        "label": str(i + 1) if i < 15 else ""  # Show step numbers for first 15
                    })

        return {
            "kind": {"grid": True},
            "rows": rows,
            "columnLabels": [{"label": str(j)} for j in range(len(maze[0]) if maze else 0)],
            "markers": markers
        }


class SudokuExtractor(BaseExtractor):
    """Extractor for Sudoku/number board visualization.

    Supports:
    - 2D array of numbers (4x4, 9x9, etc.)
    - Dict format: {"board": [[...]], "current": (r,c), "original": [[...]], "trying": num}

    Visualizes with colors:
    - Empty cells (0): light gray
    - Original numbers: bold, dark
    - Filled numbers: blue
    - Current cell: yellow highlight
    - Invalid placement: red
    """

    @property
    def id(self) -> str:
        return "builtin.sudoku"

    @property
    def name(self) -> str:
        return "Sudoku/Board Visualizer"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        # Check for dict format with "board" key
        if isinstance(value, dict) and "board" in value:
            board = value.get("board")
            if isinstance(board, list) and board and isinstance(board[0], list):
                return True

        # Check for 2D array of numbers (not just 0s and 1s like maze)
        if isinstance(value, list) and value and isinstance(value[0], list):
            first_row = value[0]
            if first_row:
                # Check if it contains numbers beyond just 0 and 1 (sudoku has 0-9)
                sample = [v for row in value[:4] for v in row[:4] if isinstance(v, int)]
                if sample and any(v > 1 for v in sample):
                    return True

        return False

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        candidates = []

        candidates.append(ExtractionCandidate(
            extractor_id=self.id,
            extractor_name="Sudoku Board",
            priority=self.priority,
            extract=lambda v=value: self._extract_sudoku(v, context)
        ))

        return candidates

    def _extract_sudoku(self, value: Any, context: ExtractionContext) -> Dict:
        """Extract sudoku board into grid visualization format."""
        # Parse input
        if isinstance(value, dict) and "board" in value:
            board = value["board"]
            original = value.get("original", None)
            current = value.get("current", None)
            trying = value.get("trying", None)
        else:
            board = value
            original = None
            current = None
            trying = None

        # If no original provided, treat non-zero values as original
        if original is None:
            original = [[cell if cell != 0 else 0 for cell in row] for row in board]

        # Convert current to tuple
        if current and isinstance(current, list):
            current = tuple(current)

        # Determine grid size for subgrid highlighting
        size = len(board)
        subgrid_size = int(size ** 0.5)  # 2 for 4x4, 3 for 9x9

        # Build grid rows
        rows = []
        markers = []

        for row_idx, row in enumerate(board):
            columns = []
            for col_idx, cell in enumerate(row):
                is_original = original[row_idx][col_idx] != 0
                is_empty = cell == 0
                is_current = current and (row_idx, col_idx) == current

                # Determine cell color, text color, and content
                if is_current:
                    # Currently being filled - yellow
                    if trying is not None:
                        color = "#fff3cd"  # Light yellow
                        text_color = "#333333"  # Dark text
                        content = str(trying) if trying > 0 else "?"
                    else:
                        color = "#ffc107"
                        text_color = "#333333"
                        content = str(cell) if cell > 0 else "?"
                elif is_empty:
                    # Empty cell - light gray
                    color = "#f5f5f5"
                    text_color = "#999999"  # Muted for empty
                    content = "·"
                elif is_original:
                    # Original number - darker background, bold dark text
                    color = "#e0e0e0"
                    text_color = "#1a1a1a"  # Very dark for original numbers
                    content = str(cell)
                else:
                    # Filled by algorithm - blue tint with dark text
                    color = "#bbdefb"
                    text_color = "#1565c0"  # Dark blue text
                    content = str(cell)

                # Add subgrid border effect via slightly different shade
                subgrid_row = row_idx // subgrid_size
                subgrid_col = col_idx // subgrid_size
                if (subgrid_row + subgrid_col) % 2 == 1:
                    # Alternate subgrid - slightly different shade
                    if color == "#f5f5f5":
                        color = "#eeeeee"
                    elif color == "#e0e0e0":
                        color = "#d5d5d5"
                    elif color == "#bbdefb":
                        color = "#90caf9"

                columns.append({
                    "content": content,
                    "color": color,
                    "textColor": text_color
                })

            rows.append({
                "label": str(row_idx),
                "columns": columns
            })

        # Add marker for current cell
        if current:
            markers.append({
                "id": "current",
                "row": current[0],
                "column": current[1],
                "color": "#ffc107",
                "label": f"→{trying}" if trying else "→"
            })

        return {
            "kind": {"grid": True},
            "rows": rows,
            "columnLabels": [{"label": str(j)} for j in range(len(board[0]) if board else 0)],
            "markers": markers
        }
