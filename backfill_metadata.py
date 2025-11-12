#!/usr/bin/env python3
"""
Backfill metadata.json files for existing analyses.

This script scans all existing analysis directories and creates metadata.json
files by extracting information from the financial statements file.
"""

import json
import re
from pathlib import Path


def extract_metadata_from_statements(statements_file: Path) -> dict:
    """Extract metadata from financial statements file."""
    if not statements_file.exists():
        return {}

    content = statements_file.read_text()
    lines = content.split('\n')

    metadata = {}

    # Extract from first few lines which contain the header
    for line in lines[:30]:
        # Company name
        if '**Company:**' in line:
            metadata['company_name'] = line.split('**Company:**')[1].strip()

        # Ticker
        elif '**Ticker:**' in line:
            metadata['ticker'] = line.split('**Ticker:**')[1].strip()

        # CIK
        elif '**CIK:**' in line:
            cik = line.split('**CIK:**')[1].strip()
            # Remove any formatting
            metadata['cik'] = cik.replace('`', '').strip()

        # Form type
        elif '**Form Type:**' in line:
            metadata['form_type'] = line.split('**Form Type:**')[1].strip()

        # Fiscal year end
        elif '**Fiscal Year End:**' in line:
            metadata['fiscal_year_end'] = line.split('**Fiscal Year End:**')[1].strip()

        # Filing date
        elif '**Filing Date:**' in line:
            metadata['filing_date'] = line.split('**Filing Date:**')[1].strip()

    # Determine if foreign filer based on form type
    if 'form_type' in metadata:
        metadata['is_foreign_filer'] = '20-F' in metadata['form_type']

    return metadata


def backfill_metadata():
    """Backfill metadata.json files for all existing analyses."""
    output_dir = Path('financial_research_agent/output')

    if not output_dir.exists():
        print(f"Output directory not found: {output_dir}")
        return

    # Find all analysis directories (timestamp format: YYYYMMDD_HHMMSS)
    analysis_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir() and re.match(r'\d{8}_\d{6}', d.name)])

    print(f"Found {len(analysis_dirs)} analysis directories")
    print()

    created_count = 0
    skipped_count = 0
    error_count = 0

    for dir_path in analysis_dirs:
        metadata_file = dir_path / 'metadata.json'

        # Skip if metadata.json already exists
        if metadata_file.exists():
            print(f"⏭️  Skipping {dir_path.name} (metadata.json already exists)")
            skipped_count += 1
            continue

        # Look for financial statements file
        statements_file = dir_path / '03_financial_statements.md'

        if not statements_file.exists():
            print(f"⚠️  Skipping {dir_path.name} (no financial statements file)")
            error_count += 1
            continue

        # Extract metadata
        try:
            metadata = extract_metadata_from_statements(statements_file)

            if not metadata:
                print(f"⚠️  Skipping {dir_path.name} (could not extract metadata)")
                error_count += 1
                continue

            # Add analysis timestamp
            metadata['analysis_timestamp'] = dir_path.name

            # Write metadata.json
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            ticker = metadata.get('ticker', 'Unknown')
            company = metadata.get('company_name', 'Unknown')
            print(f"✅ Created metadata for {dir_path.name}: {company} ({ticker})")
            created_count += 1

        except Exception as e:
            print(f"❌ Error processing {dir_path.name}: {e}")
            error_count += 1

    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped (already exists): {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(analysis_dirs)}")
    print("=" * 60)


if __name__ == '__main__':
    backfill_metadata()
