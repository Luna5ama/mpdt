import concurrent.futures
import multiprocessing.pool
import os
import pathlib
import csv
import argparse
import sys
import time

import requests
import pypdf

from typing import Dict, List
from unpywall import Unpywall
from requests_html import HTMLSession
from unpywall.utils import UnpywallCredentials

spoofed_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
}

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def validate_pdf(file_path):
    valid = True
    try:
        pypdf.PdfReader(file_path, strict=False)
    except FileNotFoundError:
        valid = False
    except:
        os.remove(file_path)
        valid = False
    return valid


class Downloader:
    def __init__(self, input_csv: pathlib.Path, output_dir: pathlib.Path, keys: Dict[str, str], verbose: bool):
        self.input_csv = input_csv
        self.output_dir = output_dir
        self.keys = keys
        self.verbose = verbose

    def download_pdf(self, paper_id: int, pdf_link: str) -> bool:
        if pdf_link is None:
            return False

        response = requests.get(pdf_link, allow_redirects=True, timeout=15, headers=spoofed_headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_error:
            return False

        file_path = self.output_dir / f'{paper_id}.pdf'

        # Save pdf
        with open(file_path, 'wb') as f:
            f.write(response.content)

        if not validate_pdf(file_path):
            return False

        return True

    def download_by_doi(self, paper_id: int, doi: str) -> bool:
        unpaywall_result = Unpywall.get_json(doi=doi)
        if unpaywall_result is None:
            eprint(f'[Error] <{paper_id}>(https://doi.org/{doi}) Unpaywall API returned None')
            return False

        best_oa_location = unpaywall_result.get('best_oa_location', None)

        if best_oa_location is None:
            eprint(f'[Error] <{paper_id}>(https://doi.org/{doi}) Pdf link is not available')
            return False

        done = self.download_pdf(paper_id, best_oa_location['url_for_pdf'])

        if not done:
            # Try other OA locations
            for loc in unpaywall_result['oa_locations']:
                done = self.download_pdf(paper_id, loc['url_for_pdf'])
                if done:
                    break

        if not done:
            eprint(f'[Error] <{paper_id}>(https://doi.org/{doi}) Could not download pdf')
            return False

        if self.verbose:
            print(f"[INFO] <{paper_id}> Downloaded paper pdf")
        return True

    def download(self):
        csv_dicts: List[Dict[str, str]] = []
        with open(self.input_csv, encoding='UTF-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=self.keys['delim'])
            for row in reader:
                csv_dicts.append(row)

        for i, stuff in enumerate(csv_dicts):
            paper_id = i + 1
            if 'id' in self.keys:
                paper_id = int(stuff[self.keys['id']])

            if validate_pdf(self.output_dir / f'{paper_id}.pdf'):
                if self.verbose:
                    print(f'[INFO] <{paper_id}> Pdf already exists, skipping...')
                continue

            doi = None

            try:
                if 'doi' in self.keys:
                    key_doi = self.keys['doi']
                    doi = stuff[key_doi]
                    self.download_by_doi(paper_id, doi)
                else:
                    key_title = self.keys['title']
                    key_authors = self.keys['authors']

                    title = stuff[key_title]
                    authors = stuff[key_authors]

                    request_url = f'https://api.crossref.org/works?query.title={stuff[key_title]}&query.author={stuff[key_authors]}&select=DOI'
                    response = requests.get(request_url)
                    response.raise_for_status()
                    doi = response.json()['message']['items'][0]['DOI']

                    self.download_by_doi(paper_id, doi)
            except KeyboardInterrupt:
                eprint(f'Interrupted by user')
                sys.exit(1)
            except Exception as e:
                eprint(f'[Error] <{paper_id}>(https://doi.org/{doi})\n', e)
                continue


def main():
    parser = argparse.ArgumentParser(description='Download papers from a CSV file')
    parser.add_argument('input_csv', type=pathlib.Path, help='Path to the input CSV file')
    parser.add_argument('output_dir', type=pathlib.Path, help='Path to the output directory')
    parser.add_argument('--delim', required=False, type=str, help='Delimiter for the CSV file', default=',')
    parser.add_argument('--id', required=False, type=str, help='ID key in the CSV file', default=',')
    parser.add_argument('--title', required=False, type=str, help='Title key in the CSV file')
    parser.add_argument('--authors', required=False, type=str, help='Authors key in the CSV file')
    parser.add_argument('--doi', required=False, type=str, help='DOI key in the CSV file')
    parser.add_argument('--email', required=True, type=str, help='Email for Unpywall API')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose log')

    args = parser.parse_args()

    os.environ['UNPAYWALL_EMAIL'] = args.email

    keys = {'delim': args.delim}

    if args.doi is None:
        if args.title is None or args.authors is None:
            eprint('Please provide either a --doi or both --title and --authors')
            sys.exit(1)
        else:
            keys['title'] = args.title
            keys['authors'] = args.authors
    else:
        keys['doi'] = args.doi

    if args.id is not None:
        keys['id'] = args.id

    input_path = pathlib.Path(args.input_csv)
    output_path = pathlib.Path(args.output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    Downloader(input_path, output_path, keys, args.verbose).download()


if __name__ == '__main__':
    main()
