"""
Semantic Scholar paper search for AlcoWatch Related Work section.
Searches for papers across 6 thematic areas and exports BibTeX entries.

Usage:
    python scripts/search_papers.py [--api-key YOUR_KEY] [--output papers_found.json]

Without API key: shared rate limit (~100 req/5min)
With API key: 1 req/sec (get free key at https://www.semanticscholar.org/product/api)
"""

import requests
import time
import json
import argparse
import re
import sys
from pathlib import Path


BASE_URL = "https://api.semanticscholar.org/graph/v1"

# Search queries organized by Related Work subsection
SEARCH_QUERIES = {
    "alcohol_detection": [
        '"blood alcohol content" estimation wearable sensor',
        'transdermal alcohol monitoring smartwatch',
        'SCRAM ankle monitor alcohol detection accuracy',
        'non-invasive alcohol detection physiological signals',
    ],
    "sensor_fusion": [
        'PPG EDA sensor fusion physiological monitoring',
        'multimodal wearable biosensor health monitoring',
        'photoplethysmography electrodermal activity fusion',
    ],
    "ml_bac_estimation": [
        'LSTM attention physiological signal classification',
        'deep learning BAC blood alcohol estimation',
        'machine learning alcohol impairment detection wearable',
        'recurrent neural network biosignal time series',
    ],
    "vehicle_interlock": [
        'ignition interlock system drunk driving prevention',
        'vehicle safety IoT wearable integration',
        'alcohol vehicle lockout system embedded',
    ],
    "edge_ai": [
        'TFLite wearable inference edge AI health',
        'TinyML health monitoring wearable deployment',
        'model compression quantization wearable device',
    ],
    "ble_security": [
        'BLE security safety-critical IoT automotive',
        'Bluetooth Low Energy protocol vehicle safety',
    ],
}

FIELDS = "title,year,abstract,citationCount,authors,journal,externalIds,publicationTypes,url"


def search_papers(query, headers, year_range="2018-", limit=30):
    """Search Semantic Scholar for papers matching query."""
    url = f"{BASE_URL}/paper/search"
    params = {
        "query": query,
        "fields": FIELDS,
        "year": year_range,
        "limit": min(limit, 100),
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        if resp.status_code == 429:
            print("  Rate limited, waiting 60s...")
            time.sleep(60)
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"  Error searching '{query[:50]}...': {e}")
        return []


def get_paper_references(paper_id, headers):
    """Get references of a specific paper (snowball search)."""
    url = f"{BASE_URL}/paper/{paper_id}/references"
    params = {"fields": FIELDS, "limit": 50}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return [ref["citedPaper"] for ref in resp.json().get("data", [])
                if ref.get("citedPaper", {}).get("title")]
    except requests.exceptions.RequestException:
        return []


def make_bibtex_key(paper):
    """Generate a BibTeX citation key from paper metadata."""
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    if authors:
        first_author = authors[0].get("name", "unknown").split()[-1].lower()
        first_author = re.sub(r'[^a-z]', '', first_author)
    else:
        first_author = "unknown"
    return f"{first_author}{year}"


def to_bibtex(paper, key=None):
    """Convert a paper dict to BibTeX entry."""
    if key is None:
        key = make_bibtex_key(paper)

    authors = " and ".join([a["name"] for a in paper.get("authors", [])[:6]])
    if len(paper.get("authors", [])) > 6:
        authors += " and others"

    doi = paper.get("externalIds", {}).get("DOI", "")
    journal = paper.get("journal", {})
    journal_name = journal.get("name", "") if journal else ""
    year = paper.get("year", "")
    title = paper.get("title", "")
    volume = journal.get("volume", "") if journal else ""

    entry_type = "article"
    pub_types = paper.get("publicationTypes", []) or []
    if "Conference" in pub_types:
        entry_type = "inproceedings"

    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  author = {{{authors}}},")
    lines.append(f"  title = {{{title}}},")
    if journal_name:
        field = "booktitle" if entry_type == "inproceedings" else "journal"
        lines.append(f"  {field} = {{{journal_name}}},")
    if volume:
        lines.append(f"  volume = {{{volume}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
        lines.append(f"  url = {{https://doi.org/{doi}}},")
    lines.append("}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search Semantic Scholar for AlcoWatch Related Work papers")
    parser.add_argument("--api-key", default=None, help="Semantic Scholar API key (optional, recommended)")
    parser.add_argument("--output", default="scripts/papers_found.json", help="Output JSON file")
    parser.add_argument("--bibtex", default="scripts/new_references.bib", help="Output BibTeX file")
    parser.add_argument("--min-citations", type=int, default=3, help="Minimum citation count filter")
    parser.add_argument("--max-papers", type=int, default=60, help="Max papers to keep after filtering")
    args = parser.parse_args()

    headers = {}
    if args.api_key:
        headers["x-api-key"] = args.api_key
        delay = 1.1  # 1 req/sec with key
    else:
        delay = 3.0  # conservative without key
        print("No API key provided. Using shared rate limit (slower).")
        print("Get a free key at: https://www.semanticscholar.org/product/api\n")

    all_papers = {}
    section_papers = {}

    for section, queries in SEARCH_QUERIES.items():
        print(f"\n{'='*60}")
        print(f"Section: {section}")
        print(f"{'='*60}")
        section_papers[section] = []

        for query in queries:
            print(f"\n  Searching: {query[:60]}...")
            papers = search_papers(query, headers)
            new_count = 0
            for p in papers:
                pid = p.get("paperId")
                if pid and pid not in all_papers:
                    p["_section"] = section
                    p["_query"] = query
                    all_papers[pid] = p
                    section_papers[section].append(pid)
                    new_count += 1
            print(f"  Found {len(papers)} results, {new_count} new unique papers")
            time.sleep(delay)

    print(f"\n{'='*60}")
    print(f"Total unique papers found: {len(all_papers)}")
    print(f"{'='*60}")

    # Filter by citation count and recency
    filtered = []
    for pid, paper in all_papers.items():
        citations = paper.get("citationCount", 0) or 0
        year = paper.get("year", 0) or 0
        # Keep if: enough citations OR very recent (2024+)
        if citations >= args.min_citations or year >= 2024:
            paper["_score"] = citations + (10 if year >= 2024 else 0) + (5 if year >= 2023 else 0)
            filtered.append(paper)

    # Sort by relevance score
    filtered.sort(key=lambda x: x.get("_score", 0), reverse=True)
    filtered = filtered[:args.max_papers]

    print(f"\nAfter filtering (min {args.min_citations} citations or 2024+): {len(filtered)} papers")

    # Print summary per section
    for section in SEARCH_QUERIES:
        count = sum(1 for p in filtered if p.get("_section") == section)
        print(f"  {section}: {count} papers")

    # Save full results as JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(filtered, f, indent=2, default=str)
    print(f"\nFull results saved to: {output_path}")

    # Generate BibTeX
    bibtex_path = Path(args.bibtex)
    used_keys = set()
    bibtex_entries = []

    for paper in filtered:
        key = make_bibtex_key(paper)
        # Handle duplicate keys
        orig_key = key
        counter = 1
        while key in used_keys:
            key = f"{orig_key}{chr(96 + counter)}"  # a, b, c...
            counter += 1
        used_keys.add(key)

        bibtex_entries.append(to_bibtex(paper, key))

    with open(bibtex_path, 'w') as f:
        f.write(f"% Auto-generated BibTeX from Semantic Scholar search\n")
        f.write(f"% Date: {time.strftime('%Y-%m-%d')}\n")
        f.write(f"% Papers: {len(bibtex_entries)}\n\n")
        f.write("\n\n".join(bibtex_entries))

    print(f"BibTeX saved to: {bibtex_path}")

    # Print top 10 most cited
    print(f"\n{'='*60}")
    print("Top 10 most cited papers found:")
    print(f"{'='*60}")
    for i, p in enumerate(filtered[:10], 1):
        authors = p.get("authors", [{}])
        first = authors[0].get("name", "?") if authors else "?"
        print(f"  {i:2d}. [{p.get('citationCount', 0):4d} cites] {first} ({p.get('year', '?')})")
        print(f"      {p.get('title', '?')[:80]}")
        print(f"      Section: {p.get('_section', '?')}")


if __name__ == "__main__":
    main()
