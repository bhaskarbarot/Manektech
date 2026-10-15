import hashlib
import re

from sqlalchemy import TextClause, text

HNSW_PREFIX = "ix_embeddings_hnsw_"
SAFE_VALUE = re.compile(r"^[\w.\-/:@]+$")


def hnsw_index_name(model_name: str, model_version: str, text_fields: str) -> str:
    key = f"{model_name}|{model_version}|{text_fields}"
    slug = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
    digest = hashlib.sha1(key.encode()).hexdigest()[:8]
    return f"{HNSW_PREFIX}{slug[:63 - len(HNSW_PREFIX) - 9]}_{digest}"


def hnsw_index_ddl(model_name: str, model_version: str, text_fields: str, dim: int) -> TextClause:
    for value in (model_name, model_version, text_fields.replace(",", "")):
        if not SAFE_VALUE.match(value):
            raise ValueError(f"unsafe value for index definition: {value!r}")
    name = hnsw_index_name(model_name, model_version, text_fields)
    return text(
        f"CREATE INDEX IF NOT EXISTS {name} ON embeddings "
        f"USING hnsw ((vector::vector({int(dim)})) vector_cosine_ops) "
        f"WHERE model_name = '{model_name}' AND model_version = '{model_version}' AND text_fields = '{text_fields}'"
    )
