"""Pandas DataFrame and Series extractor.

Provides visualization for Pandas DataFrames and Series:
- DataFrame: Table view (default), plot view for numeric data
- Series: Table view (default)
"""

from typing import Any, Dict, List

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractorPriority,
)


class PandasExtractor(BaseExtractor):
    """Extractor for Pandas DataFrames and Series.

    Provides visualization options:
    - DataFrame: Table (default), line plot for numeric columns
    - Series: Table (default)
    """

    @property
    def id(self) -> str:
        return "datascience.pandas"

    @property
    def name(self) -> str:
        return "Pandas"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        if not HAS_PANDAS:
            return False
        return isinstance(value, (pd.DataFrame, pd.Series))

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        if not HAS_PANDAS:
            return []

        candidates = []

        if isinstance(value, pd.DataFrame):
            # Table view (default)
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.dataframe.table",
                extractor_name="DataFrame as Table",
                priority=self.priority + 20,
                extract=lambda v=value: self._extract_dataframe_table(v, context)
            ))

            # Plot view for numeric columns
            numeric_cols = value.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 1:
                candidates.append(ExtractionCandidate(
                    extractor_id=f"{self.id}.dataframe.plot",
                    extractor_name="DataFrame as Line Plot",
                    priority=self.priority,
                    extract=lambda v=value: self._extract_dataframe_plot(v, context)
                ))

            # Info view
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.dataframe.info",
                extractor_name="DataFrame Info",
                priority=self.priority - 10,
                extract=lambda v=value: self._extract_dataframe_info(v, context)
            ))

        elif isinstance(value, pd.Series):
            # Table view (default)
            candidates.append(ExtractionCandidate(
                extractor_id=f"{self.id}.series.table",
                extractor_name="Series as Table",
                priority=self.priority + 10,
                extract=lambda v=value: self._extract_series_table(v, context)
            ))

            # Plot view for numeric series
            if pd.api.types.is_numeric_dtype(value):
                candidates.append(ExtractionCandidate(
                    extractor_id=f"{self.id}.series.plot",
                    extractor_name="Series as Line Plot",
                    priority=self.priority,
                    extract=lambda v=value: self._extract_series_plot(v, context)
                ))

        return candidates

    def _extract_dataframe_table(self, df: "pd.DataFrame", context: ExtractionContext) -> Dict:
        """Extract DataFrame as a table."""
        # Limit rows
        display_df = df.head(context.max_items)

        # Convert to list of dicts for table visualization
        rows = []
        for idx, row in display_df.iterrows():
            row_dict = {"_index": str(idx)}
            for col in display_df.columns:
                val = row[col]
                row_dict[str(col)] = self._format_value(val)
            rows.append(row_dict)

        return {
            "kind": {"table": True},
            "rows": rows
        }

    def _extract_dataframe_plot(self, df: "pd.DataFrame", context: ExtractionContext) -> Dict:
        """Extract DataFrame numeric columns as a line plot."""
        numeric_df = df.select_dtypes(include=['number']).head(context.max_items)

        traces = []
        for col in list(numeric_df.columns)[:10]:  # Limit to 10 columns
            values = numeric_df[col].tolist()
            # Replace NaN with None for JSON
            values = [None if pd.isna(v) else float(v) for v in values]
            traces.append({
                "type": "scatter",
                "mode": "lines",
                "name": str(col),
                "y": values
            })

        return {
            "kind": {"plotly": True},
            "data": traces,
            "layout": {
                "title": f"DataFrame ({df.shape[0]} rows x {df.shape[1]} cols)"
            }
        }

    def _extract_dataframe_info(self, df: "pd.DataFrame", context: ExtractionContext) -> Dict:
        """Extract DataFrame as info text."""
        # Build column info
        col_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].notna().sum()
            col_info.append(f"  - **{col}**: {dtype} ({non_null} non-null)")

        # Memory usage
        mem_usage = df.memory_usage(deep=True).sum()
        if mem_usage > 1e9:
            mem_str = f"{mem_usage / 1e9:.2f} GB"
        elif mem_usage > 1e6:
            mem_str = f"{mem_usage / 1e6:.2f} MB"
        else:
            mem_str = f"{mem_usage / 1e3:.2f} KB"

        info = f"""# DataFrame

**Shape:** {df.shape[0]} rows x {df.shape[1]} columns
**Memory:** {mem_str}
**Index:** {type(df.index).__name__} ({df.index.dtype})

## Columns
{chr(10).join(col_info)}

## Head (first 5 rows)
```
{df.head().to_string()}
```
"""
        return {
            "kind": {"text": True},
            "text": info,
            "fileName": "dataframe_info.md"
        }

    def _extract_series_table(self, series: "pd.Series", context: ExtractionContext) -> Dict:
        """Extract Series as a table."""
        display_series = series.head(context.max_items)
        rows = [
            {
                "index": str(idx),
                "value": self._format_value(val)
            }
            for idx, val in display_series.items()
        ]

        return {
            "kind": {"table": True},
            "rows": rows
        }

    def _extract_series_plot(self, series: "pd.Series", context: ExtractionContext) -> Dict:
        """Extract numeric Series as a line plot."""
        display_series = series.head(context.max_items)
        values = display_series.tolist()
        # Replace NaN with None for JSON
        values = [None if pd.isna(v) else float(v) for v in values]

        return {
            "kind": {"plotly": True},
            "data": [{
                "type": "scatter",
                "mode": "lines",
                "y": values,
                "name": str(series.name) if series.name else "Series"
            }],
            "layout": {
                "title": f"Series ({len(series)} values)",
                "xaxis": {"title": "Index"},
                "yaxis": {"title": str(series.name) if series.name else "Value"}
            }
        }

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if pd.isna(value):
            return "NaN"
        if isinstance(value, float):
            return f"{value:.6g}"
        if isinstance(value, str) and len(value) > 50:
            return f"{value[:50]}..."
        return str(value)
