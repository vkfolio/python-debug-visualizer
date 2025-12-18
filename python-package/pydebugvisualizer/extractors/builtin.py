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
