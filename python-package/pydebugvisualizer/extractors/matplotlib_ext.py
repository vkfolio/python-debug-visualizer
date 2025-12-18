"""Matplotlib figure extractor.

Provides visualization for Matplotlib figures and axes by converting
them to PNG images.
"""

import base64
import io
from typing import Any, Dict, List

try:
    import matplotlib.figure
    import matplotlib.axes
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractorPriority,
)


class MatplotlibExtractor(BaseExtractor):
    """Extractor for Matplotlib figures and axes.

    Converts Matplotlib figures to PNG images for visualization.
    Supports both Figure objects and Axes objects (extracts the figure).
    """

    @property
    def id(self) -> str:
        return "datascience.matplotlib"

    @property
    def name(self) -> str:
        return "Matplotlib"

    @property
    def priority(self) -> int:
        return ExtractorPriority.HIGH + 50  # Very high priority for figures

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        if not HAS_MATPLOTLIB:
            return False
        return isinstance(value, (matplotlib.figure.Figure, matplotlib.axes.Axes))

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        if not HAS_MATPLOTLIB:
            return []

        # Get the figure (from Axes if necessary)
        if isinstance(value, matplotlib.axes.Axes):
            fig = value.figure
        else:
            fig = value

        return [
            ExtractionCandidate(
                extractor_id=self.id,
                extractor_name="Matplotlib Figure",
                priority=self.priority,
                extract=lambda f=fig: self._extract_figure(f)
            ),
            ExtractionCandidate(
                extractor_id=f"{self.id}.svg",
                extractor_name="Matplotlib Figure (SVG)",
                priority=self.priority - 10,
                extract=lambda f=fig: self._extract_figure_svg(f)
            )
        ]

    def _extract_figure(self, fig: "matplotlib.figure.Figure") -> Dict:
        """Extract figure as a PNG image."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        return {
            "kind": {"imagePng": True},
            "base64Data": img_base64
        }

    def _extract_figure_svg(self, fig: "matplotlib.figure.Figure") -> Dict:
        """Extract figure as an SVG."""
        buf = io.BytesIO()
        fig.savefig(buf, format='svg', bbox_inches='tight')
        buf.seek(0)
        svg_text = buf.read().decode('utf-8')
        buf.close()

        return {
            "kind": {"svg": True},
            "text": svg_text
        }
