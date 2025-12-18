"""NumPy array extractor.

Provides visualization for NumPy ndarrays with different views based on dimensions:
- 1D arrays: Line plot or grid
- 2D arrays: Heatmap or grid
- Higher dimensions: Info view with statistics
"""

from typing import Any, Dict, List

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractorPriority,
)


class NumpyExtractor(BaseExtractor):
    """Extractor for NumPy ndarrays.

    Provides multiple visualization options based on array dimensions:
    - 1D: Line plot (default), grid
    - 2D: Heatmap (default), grid
    - 3D+: Info view with statistics and first slice
    """

    @property
    def id(self) -> str:
        return "datascience.numpy"

    @property
    def name(self) -> str:
        return "NumPy Array"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        if not HAS_NUMPY:
            return False
        return isinstance(value, np.ndarray)

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        if not HAS_NUMPY:
            return []

        candidates = []
        arr = value
        ndim = arr.ndim

        # 1D arrays
        if ndim == 1:
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.plot",
                extractor_name="NumPy 1D as Line Plot",
                priority=self.priority + 10,
                extract=lambda a=arr: self._extract_1d_plot(a, context)
            ))
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.grid",
                extractor_name="NumPy 1D as Grid",
                priority=self.priority,
                extract=lambda a=arr: self._extract_1d_grid(a, context)
            ))

        # 2D arrays
        elif ndim == 2:
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.heatmap",
                extractor_name="NumPy 2D as Heatmap",
                priority=self.priority + 10,
                extract=lambda a=arr: self._extract_2d_heatmap(a, context)
            ))
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.grid",
                extractor_name="NumPy 2D as Grid",
                priority=self.priority,
                extract=lambda a=arr: self._extract_2d_grid(a, context)
            ))

        # Higher dimensions
        else:
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.info",
                extractor_name=f"NumPy {ndim}D Array Info",
                priority=self.priority,
                extract=lambda a=arr: self._extract_nd_info(a, context)
            ))

        # Always add info view as fallback
        if ndim <= 2:
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.info",
                extractor_name="NumPy Array Info",
                priority=self.priority - 20,
                extract=lambda a=arr: self._extract_nd_info(a, context)
            ))

        return candidates

    def _extract_1d_plot(self, arr: "np.ndarray", context: ExtractionContext) -> Dict:
        """Extract 1D array as a line plot."""
        # Sample if too large
        if len(arr) > context.max_items:
            indices = np.linspace(0, len(arr) - 1, context.max_items, dtype=int)
            sampled = arr[indices]
            x = indices.tolist()
        else:
            sampled = arr
            x = list(range(len(arr)))

        # Convert to Python types for JSON serialization
        y = [float(v) if np.isfinite(v) else None for v in sampled.flatten()]

        return {
            "kind": {"plotly": True},
            "data": [{
                "type": "scatter",
                "mode": "lines",
                "x": x,
                "y": y
            }],
            "layout": {
                "title": f"NumPy Array (shape={arr.shape}, dtype={arr.dtype})",
                "xaxis": {"title": "Index"},
                "yaxis": {"title": "Value"}
            }
        }

    def _extract_1d_grid(self, arr: "np.ndarray", context: ExtractionContext) -> Dict:
        """Extract 1D array as a single-row grid."""
        items = arr[:context.max_items]
        columns = [{"content": self._format_value(v)} for v in items]

        return {
            "kind": {"grid": True},
            "columnLabels": [{"label": str(i)} for i in range(len(columns))],
            "rows": [{
                "label": f"ndarray[{len(arr)}]",
                "columns": columns
            }]
        }

    def _extract_2d_heatmap(self, arr: "np.ndarray", context: ExtractionContext) -> Dict:
        """Extract 2D array as a heatmap."""
        # Sample if too large
        max_dim = int(context.max_items ** 0.5)

        if arr.shape[0] > max_dim or arr.shape[1] > max_dim:
            row_idx = np.linspace(0, arr.shape[0] - 1, min(max_dim, arr.shape[0]), dtype=int)
            col_idx = np.linspace(0, arr.shape[1] - 1, min(max_dim, arr.shape[1]), dtype=int)
            sampled = arr[np.ix_(row_idx, col_idx)]
        else:
            sampled = arr

        # Convert to Python types, handling non-finite values
        z = []
        for row in sampled:
            z_row = [float(v) if np.isfinite(v) else None for v in row]
            z.append(z_row)

        return {
            "kind": {"plotly": True},
            "data": [{
                "type": "heatmap",
                "z": z,
                "colorscale": "Viridis"
            }],
            "layout": {
                "title": f"NumPy Array (shape={arr.shape}, dtype={arr.dtype})"
            }
        }

    def _extract_2d_grid(self, arr: "np.ndarray", context: ExtractionContext) -> Dict:
        """Extract 2D array as a grid."""
        max_dim = int(context.max_items ** 0.5)
        rows = []

        for i, row in enumerate(arr[:max_dim]):
            rows.append({
                "label": str(i),
                "columns": [
                    {"content": self._format_value(v)}
                    for v in row[:max_dim]
                ]
            })

        return {
            "kind": {"grid": True},
            "columnLabels": [{"label": str(j)} for j in range(min(max_dim, arr.shape[1]))],
            "rows": rows
        }

    def _extract_nd_info(self, arr: "np.ndarray", context: ExtractionContext) -> Dict:
        """Extract N-dimensional array as info text."""
        # Compute statistics
        try:
            min_val = float(np.nanmin(arr))
            max_val = float(np.nanmax(arr))
            mean_val = float(np.nanmean(arr))
            std_val = float(np.nanstd(arr))
        except (TypeError, ValueError):
            # Non-numeric array
            min_val = max_val = mean_val = std_val = "N/A"

        # Format first slice
        first_slice = arr[0] if arr.ndim > 1 else arr
        slice_str = np.array2string(
            first_slice,
            max_line_width=80,
            threshold=50,
            precision=4
        )

        info = f"""# NumPy Array

**Shape:** {arr.shape}
**Dtype:** {arr.dtype}
**Size:** {arr.size:,} elements
**Memory:** {arr.nbytes:,} bytes

## Statistics
- **Min:** {min_val}
- **Max:** {max_val}
- **Mean:** {mean_val}
- **Std:** {std_val}

## First slice {"(arr[0])" if arr.ndim > 1 else ""}:
```
{slice_str}
```
"""
        return {
            "kind": {"text": True},
            "text": info,
            "fileName": "array_info.md"
        }

    def _format_value(self, value: Any) -> str:
        """Format a single value for display."""
        if isinstance(value, (np.floating, float)):
            if np.isnan(value):
                return "NaN"
            elif np.isinf(value):
                return "Inf" if value > 0 else "-Inf"
            return f"{value:.4g}"
        return str(value)
