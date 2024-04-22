import pathlib
import csv
import argparse

from typing import Dict


def download(input_csv: pathlib.Path, output_dir: pathlib.Path, keys: Dict[str, str]):
    csv_dicts = []
    with open(input_csv) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            csv_dicts.append(row)

    print(csv_dicts)


def main():
    parser = argparse.ArgumentParser(description="Download papers from a CSV file")
    parser.add_argument("input_csv", type=pathlib.Path, help="Path to the input CSV file")
    parser.add_argument("output_dir", type=pathlib.Path, help="Path to the output directory")
    parser.add_argument("--title", required=False, type=str, help="Title key in the CSV file")
    parser.add_argument("--authors", required=False, type=str, help="Authors key in the CSV file")
    parser.add_argument("--doi", required=False, type=str, help="DOI key in the CSV file")

    args = parser.parse_args()

    download(args.input_csv, args.output_dir, {"doi": args.title, "authors": args.authors, "title": args.doi})


if __name__ == "__main__":
    main()
