from sqlalchemy import Index

from .relationships import Relationship

object_predicate = Index("ix_relationships_object_predicate", Relationship.object_uri, Relationship.predicate_uri)
predicate = Index("ix_relationships_predicate", Relationship.predicate_uri)
