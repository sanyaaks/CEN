import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from app.scraping.base import BaseScraper
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SourceMetadata:
    source_name: str
    source_type: str  # AGGREGATOR, OTA, BROWSER, MODEL
    scraper_class: Type[BaseScraper]
    enabled: bool = True
    priority: int = 1
    supported_routes: List[str] = field(default_factory=lambda: ["DEL-BOM", "BLR-DEL", "HYD-MAA", "DEL-MAA", "BOM-BLR", "DEL-CCU"])
    supported_features: List[str] = field(default_factory=lambda: ["ONE_WAY", "DIRECT_FLIGHTS"])
    compliance_status: str = "COMPLIANT_ROBOTS_TXT"
    description: str = ""
    is_fallback_model: bool = False


class SourceRegistry:
    """
    Central Registry for multi-source scraper management.
    Enables pluggable data sources, dynamic prioritization, and source capability inspection.
    """

    def __init__(self):
        self._sources: Dict[str, SourceMetadata] = {}

    def register(self, metadata: SourceMetadata):
        """Registers a data source adapter into the registry."""
        self._sources[metadata.source_name] = metadata
        logger.debug(f"Registered data source: {metadata.source_name} (Priority {metadata.priority})")

    def unregister(self, source_name: str):
        """Removes a source from the registry."""
        if source_name in self._sources:
            del self._sources[source_name]

    def get_source_metadata(self, source_name: str) -> Optional[SourceMetadata]:
        return self._sources.get(source_name)

    def get_scraper_instance(self, source_name: str, **kwargs) -> Optional[BaseScraper]:
        meta = self.get_source_metadata(source_name)
        if not meta or not meta.enabled:
            return None
        return meta.scraper_class(**kwargs)

    def get_enabled_sources_by_priority(self) -> List[SourceMetadata]:
        """Returns enabled sources sorted by priority (lowest integer = highest priority)."""
        enabled = [meta for meta in self._sources.values() if meta.enabled]
        return sorted(enabled, key=lambda s: s.priority)

    def list_all_sources(self) -> List[Dict[str, Any]]:
        """Returns diagnostic list of all registered sources."""
        return [
            {
                "source_name": meta.source_name,
                "source_type": meta.source_type,
                "enabled": meta.enabled,
                "priority": meta.priority,
                "compliance_status": meta.compliance_status,
                "is_fallback_model": meta.is_fallback_model,
                "description": meta.description
            }
            for meta in self._sources.values()
        ]


# Global Registry Instance
registry = SourceRegistry()
