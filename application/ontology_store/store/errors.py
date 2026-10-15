class OntologyStoreError(Exception):
    pass


class InvalidFilterError(OntologyStoreError, ValueError):
    pass


class DatasetValidationError(OntologyStoreError):
    pass
