"""Extractor registry for managing data extractors."""

from typing import Any, Dict, List, Optional

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractionResult,
)


class ExtractorRegistry:
    """Central registry for all data extractors.

    The registry manages the collection of extractors and provides
    methods to find and apply the best extractor for a given value.

    Usage:
        registry = ExtractorRegistry()
        registry.register(ListExtractor())
        registry.register(DictExtractor())

        result = registry.extract(my_value, context)
    """

    def __init__(self):
        self._extractors: Dict[str, BaseExtractor] = {}

    def register(self, extractor: BaseExtractor) -> None:
        """Register an extractor with the registry.

        If an extractor with the same ID already exists, it will be replaced.

        Args:
            extractor: The extractor to register
        """
        self._extractors[extractor.id] = extractor

    def unregister(self, extractor_id: str) -> bool:
        """Remove an extractor from the registry.

        Args:
            extractor_id: The ID of the extractor to remove

        Returns:
            True if an extractor was removed, False if not found
        """
        if extractor_id in self._extractors:
            del self._extractors[extractor_id]
            return True
        return False

    def get_extractor(self, extractor_id: str) -> Optional[BaseExtractor]:
        """Get an extractor by ID.

        Args:
            extractor_id: The ID of the extractor

        Returns:
            The extractor, or None if not found
        """
        return self._extractors.get(extractor_id)

    def list_extractors(self) -> List[BaseExtractor]:
        """Get all registered extractors.

        Returns:
            List of all registered extractors
        """
        return list(self._extractors.values())

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        """Get all applicable extractions for a value.

        Queries all registered extractors and collects candidates
        that can handle the value.

        Args:
            value: The Python value to extract
            context: Extraction context with constraints

        Returns:
            List of extraction candidates, sorted by priority (highest first)
        """
        candidates: List[ExtractionCandidate] = []

        for extractor in self._extractors.values():
            try:
                if extractor.can_extract(value, context):
                    extractor_candidates = extractor.get_extractions(value, context)
                    candidates.extend(extractor_candidates)
            except Exception:
                # Log but don't fail - other extractors may work
                # In a real implementation, we'd use proper logging
                pass

        # Sort by priority (highest first)
        candidates.sort(key=lambda c: c.priority, reverse=True)
        return candidates

    def extract(
        self,
        value: Any,
        context: ExtractionContext
    ) -> Optional[ExtractionResult]:
        """Extract visualization data using the best available extractor.

        If a preferred extractor is specified in the context and is available,
        it will be used. Otherwise, the highest priority extractor is used.

        Args:
            value: The Python value to extract
            context: Extraction context with constraints

        Returns:
            ExtractionResult if successful, None if no extractor could handle the value
        """
        candidates = self.get_extractions(value, context)

        if not candidates:
            return None

        # Use preferred extractor if specified and available
        if context.preferred_extractor_id:
            for candidate in candidates:
                if candidate.extractor_id == context.preferred_extractor_id:
                    return self._execute_extraction(candidate)

        # Otherwise use highest priority
        return self._execute_extraction(candidates[0])

    def _execute_extraction(self, candidate: ExtractionCandidate) -> ExtractionResult:
        """Execute an extraction candidate and return the result.

        Args:
            candidate: The extraction candidate to execute

        Returns:
            ExtractionResult with the visualization data
        """
        data = candidate.extract()
        return ExtractionResult(
            extractor_id=candidate.extractor_id,
            extractor_name=candidate.extractor_name,
            priority=candidate.priority,
            data=data
        )


# Global registry instance
_global_registry: Optional[ExtractorRegistry] = None


def get_registry() -> ExtractorRegistry:
    """Get the global extractor registry.

    Creates the registry on first access (lazy initialization).

    Returns:
        The global ExtractorRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ExtractorRegistry()
    return _global_registry


def register_extractor(extractor: BaseExtractor) -> None:
    """Register an extractor with the global registry.

    Convenience function for registering extractors without
    directly accessing the registry.

    Args:
        extractor: The extractor to register
    """
    get_registry().register(extractor)
