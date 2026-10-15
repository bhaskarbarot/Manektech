import argparse
import json

from ..factory import open_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete a whole dataset, or records matching metadata filters")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dataset", help="dataset id, e.g. competency-sample@1.0.0")
    group.add_argument("--filters", help='json filters, e.g. \'{"metadata": {"source": "seed"}}\'')
    args = parser.parse_args()
    store = open_store()
    if args.dataset:
        deleted = store.delete_dataset(args.dataset)
    else:
        deleted = store.delete_by_metadata(json.loads(args.filters))
    print(f"deleted {deleted} records")


if __name__ == "__main__":
    main()
