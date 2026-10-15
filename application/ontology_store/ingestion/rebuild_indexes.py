import argparse

from ..factory import open_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or refresh embeddings and the vector index for one embedding model")
    parser.add_argument("--model", help="embedding model: hashing, st or st:<name>")
    parser.add_argument("--force", action="store_true", help="re-embed everything, not only changed text")
    args = parser.parse_args()
    store = open_store(args.model)
    updated = store.rebuild_embeddings(force=args.force)
    model = store.vectors.model
    print(f"{updated} embeddings updated for {model.name} {model.version} (dim {model.dim})")


if __name__ == "__main__":
    main()
