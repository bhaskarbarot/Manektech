from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from .models import CanonicalEntity, CanonicalRelationship, DatasetManifest, ImportResult

Record = dict[str, Any]


class OntologyStore(ABC):
    @abstractmethod
    def get_entity(self, uri: str) -> Record | None: ...

    @abstractmethod
    def query_entities(self, filters: dict | None = None, limit: int | None = None) -> list[Record]: ...

    @abstractmethod
    def count_entities(self, filters: dict | None = None) -> int: ...

    @abstractmethod
    def browse_entities(self, page_number: int, page_size: int, filters: dict | None = None) -> list[Record]: ...

    @abstractmethod
    def query_relationships(self, filters: dict | None = None, limit: int | None = None) -> list[Record]: ...

    @abstractmethod
    def count_relationships(self, filters: dict | None = None) -> int: ...

    @abstractmethod
    def get_neighbours(self, uri: str, predicates: list[str] | None = None, direction: str = "both") -> list[Record]: ...

    @abstractmethod
    def get_linked_entities(
        self, uri: str, predicates: list[str] | None = None, direction: str = "out", filters: dict | None = None
    ) -> list[Record]: ...

    @abstractmethod
    def literal_search(self, query: str, filters: dict | None = None, limit: int = 10) -> list[Record]: ...

    @abstractmethod
    def vector_search(self, query: str, filters: dict | None = None, limit: int = 10) -> list[Record]: ...

    @abstractmethod
    def register_dataset(self, manifest: DatasetManifest) -> str: ...

    @abstractmethod
    def import_entities(
        self, records: Iterable[CanonicalEntity], dataset_id: str | None = None, prune: bool = False
    ) -> ImportResult: ...

    @abstractmethod
    def import_relationships(
        self,
        records: Iterable[CanonicalRelationship],
        dataset_id: str | None = None,
        check_entities_exist: bool = True,
        prune: bool = False,
    ) -> ImportResult: ...

    @abstractmethod
    def rebuild_embeddings(self, uris: Iterable[str] | None = None, force: bool = False) -> int: ...

    @abstractmethod
    def embedded_text(self, uri: str) -> str | None: ...

    @abstractmethod
    def refresh_dataset_counts(self, dataset_id: str) -> dict[str, int]: ...

    @abstractmethod
    def delete_by_metadata(self, filters: dict) -> int: ...

    @abstractmethod
    def delete_dataset(self, dataset_id: str) -> int: ...

    @abstractmethod
    def list_datasets(self) -> list[Record]: ...

    @abstractmethod
    def export_dataset(
        self, dataset_id: str
    ) -> tuple[DatasetManifest, list[CanonicalEntity], list[CanonicalRelationship]]: ...
