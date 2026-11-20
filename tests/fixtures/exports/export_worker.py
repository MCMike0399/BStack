import argparse
from pathlib import Path


def export(export_id, output):
    with output.open("a", encoding="utf-8") as stream:
        stream.write(export_id + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("export_id")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.export_id, args.output)
