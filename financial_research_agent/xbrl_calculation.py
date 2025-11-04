"""
XBRL Calculation Linkbase Parser

Lightweight parser for SEC XBRL calculation linkbase files (_cal.xml) to extract
parent-child relationships and validate financial statement aggregations.

This approach uses the official SEC calculation linkbases instead of custom
aggregation logic, ensuring consistency with XBRL taxonomy standards.
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CalculationRelationship:
    """Represents a parent-child calculation relationship in XBRL."""
    parent_concept: str
    child_concept: str
    weight: float  # +1 for addition, -1 for subtraction
    order: float  # Presentation order


class XBRLCalculationParser:
    """Parse XBRL calculation linkbase files to extract parent-child relationships."""

    # XBRL namespaces
    NAMESPACES = {
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xbrli': 'http://www.xbrl.org/2003/instance',
    }

    def __init__(self):
        self.relationships: Dict[str, List[CalculationRelationship]] = {}
        self.locators: Dict[str, str] = {}  # Maps locator labels to concept names

    def parse_from_url(self, filing_url: str) -> bool:
        """
        Download and parse calculation linkbase from SEC filing URL.

        Args:
            filing_url: URL to the XBRL instance file or direct _cal.xml URL

        Returns:
            True if successful, False otherwise
        """
        # If URL already points to _cal.xml, use it directly
        if '_cal.xml' in filing_url:
            cal_urls = [filing_url]
        else:
            # Try to construct _cal.xml URL from instance URL
            cal_urls = self._get_calculation_urls(filing_url)

        # SEC requires User-Agent header
        headers = {
            'User-Agent': 'FinancialResearchAgent/1.0 (contact@example.com)',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }

        for cal_url in cal_urls:
            try:
                logger.info(f"Attempting to fetch calculation linkbase: {cal_url}")
                response = requests.get(cal_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    self.parse_from_xml(response.content)
                    logger.info(f"Successfully parsed calculation linkbase from {cal_url}")
                    return True
                else:
                    logger.debug(f"Failed to fetch {cal_url}: HTTP {response.status_code}")
            except Exception as e:
                logger.debug(f"Error fetching {cal_url}: {e}")
                continue

        logger.warning(f"Could not fetch calculation linkbase from any URL")
        return False

    def _get_calculation_urls(self, filing_url: str) -> List[str]:
        """Generate possible calculation linkbase URLs from filing URL."""
        urls = []

        # Common patterns:
        # 1. Replace _htm.xml with _cal.xml
        if '_htm.xml' in filing_url:
            urls.append(filing_url.replace('_htm.xml', '_cal.xml'))

        # 2. Replace .xml with _cal.xml
        if filing_url.endswith('.xml'):
            base = filing_url[:-4]
            urls.append(f"{base}_cal.xml")

        # 3. If it's an instance file like tsla-20250930.xml -> tsla-20250930_cal.xml
        if '.xml' in filing_url and '_cal' not in filing_url:
            urls.append(filing_url.replace('.xml', '_cal.xml'))

        return urls

    def parse_from_xml(self, xml_content: bytes):
        """
        Parse calculation linkbase XML content.

        Args:
            xml_content: Raw XML bytes from _cal.xml file
        """
        try:
            tree = ET.fromstring(xml_content)

            # First pass: Extract all locators (label -> concept mappings)
            self._extract_locators(tree)

            # Second pass: Extract calculation arcs (parent-child relationships)
            self._extract_calculation_arcs(tree)

            logger.info(f"Parsed {len(self.relationships)} parent concepts with calculation relationships")

        except ET.ParseError as e:
            logger.error(f"Failed to parse calculation XML: {e}")
            raise

    def _extract_locators(self, tree: ET.Element):
        """Extract locator elements that map labels to concept names."""
        for loc in tree.findall('.//link:loc', self.NAMESPACES):
            label = loc.get('{http://www.w3.org/1999/xlink}label')
            href = loc.get('{http://www.w3.org/1999/xlink}href')

            if label and href:
                # Extract concept name from href (e.g., "#us-gaap_Assets" -> "us-gaap:Assets")
                concept = href.split('#')[-1].replace('_', ':')
                self.locators[label] = concept

    def _extract_calculation_arcs(self, tree: ET.Element):
        """Extract calculation arcs that define parent-child relationships."""
        for calc_link in tree.findall('.//link:calculationLink', self.NAMESPACES):
            for arc in calc_link.findall('.//link:calculationArc', self.NAMESPACES):
                from_label = arc.get('{http://www.w3.org/1999/xlink}from')
                to_label = arc.get('{http://www.w3.org/1999/xlink}to')
                weight = float(arc.get('weight', '1.0'))
                order = float(arc.get('order', '1.0'))

                # Map labels to concepts
                parent_concept = self.locators.get(from_label)
                child_concept = self.locators.get(to_label)

                if parent_concept and child_concept:
                    rel = CalculationRelationship(
                        parent_concept=parent_concept,
                        child_concept=child_concept,
                        weight=weight,
                        order=order
                    )

                    if parent_concept not in self.relationships:
                        self.relationships[parent_concept] = []

                    self.relationships[parent_concept].append(rel)

    def get_children(self, concept: str) -> List[CalculationRelationship]:
        """
        Get child concepts for a given parent concept.

        Args:
            concept: Parent concept name (e.g., "us-gaap:Assets")

        Returns:
            List of CalculationRelationship objects, sorted by order
        """
        # Try exact match first
        if concept in self.relationships:
            return sorted(self.relationships[concept], key=lambda x: x.order)

        # Try with different namespace separators (: vs _)
        alt_concept = concept.replace(':', '_')
        if alt_concept in self.relationships:
            return sorted(self.relationships[alt_concept], key=lambda x: x.order)

        alt_concept = concept.replace('_', ':')
        if alt_concept in self.relationships:
            return sorted(self.relationships[alt_concept], key=lambda x: x.order)

        return []

    def calculate_parent_value(self, child_values: Dict[str, float], parent_concept: str) -> Optional[float]:
        """
        Calculate parent concept value from child values using calculation linkbase.

        Args:
            child_values: Dict mapping concept names to their values
            parent_concept: Parent concept to calculate

        Returns:
            Calculated value, or None if calculation not possible
        """
        children = self.get_children(parent_concept)

        if not children:
            return None

        total = 0.0
        missing_concepts = []

        for rel in children:
            child_value = child_values.get(rel.child_concept)

            # Also try alternate namespace separators
            if child_value is None:
                alt_concept = rel.child_concept.replace(':', '_')
                child_value = child_values.get(alt_concept)

            if child_value is None:
                alt_concept = rel.child_concept.replace('_', ':')
                child_value = child_values.get(alt_concept)

            if child_value is not None:
                total += child_value * rel.weight
            else:
                missing_concepts.append(rel.child_concept)

        if missing_concepts:
            logger.debug(f"Missing child concepts for {parent_concept}: {missing_concepts}")
            # Return None if we're missing required components
            if len(missing_concepts) == len(children):
                return None

        return total

    def validate_calculation(
        self,
        concept_values: Dict[str, float],
        parent_concept: str,
        tolerance: float = 0.01
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        """
        Validate a parent concept value against its calculated value from children.

        Args:
            concept_values: Dict mapping concept names to their values
            parent_concept: Parent concept to validate
            tolerance: Allowed difference as fraction (default 1%)

        Returns:
            Tuple of (is_valid, reported_value, calculated_value)
        """
        reported_value = concept_values.get(parent_concept)

        if reported_value is None:
            return (False, None, None)

        calculated_value = self.calculate_parent_value(concept_values, parent_concept)

        if calculated_value is None:
            # Cannot calculate - missing children
            return (False, reported_value, None)

        # Check if values match within tolerance
        if abs(reported_value) < 1.0:
            # For very small values, use absolute tolerance
            is_valid = abs(reported_value - calculated_value) < tolerance
        else:
            # For larger values, use relative tolerance
            relative_diff = abs(reported_value - calculated_value) / abs(reported_value)
            is_valid = relative_diff < tolerance

        return (is_valid, reported_value, calculated_value)

    def get_all_parent_concepts(self) -> List[str]:
        """Get list of all parent concepts in the calculation linkbase."""
        return list(self.relationships.keys())

    def print_calculation_tree(self, parent_concept: str, indent: int = 0):
        """
        Print calculation tree for a given parent concept (for debugging).

        Args:
            parent_concept: Parent concept to print tree for
            indent: Indentation level (for recursion)
        """
        children = self.get_children(parent_concept)

        if not children:
            return

        print("  " * indent + f"{parent_concept}:")
        for rel in children:
            sign = "+" if rel.weight > 0 else "-"
            print("  " * (indent + 1) + f"{sign} {rel.child_concept}")
            # Recursively print children
            self.print_calculation_tree(rel.child_concept, indent + 2)


def get_calculation_parser_for_filing(filing_url: str) -> Optional[XBRLCalculationParser]:
    """
    Convenience function to get a calculation parser for a given filing URL.

    Args:
        filing_url: URL to the XBRL instance file

    Returns:
        XBRLCalculationParser instance if successful, None otherwise
    """
    parser = XBRLCalculationParser()

    if parser.parse_from_url(filing_url):
        return parser

    return None


# Example usage
if __name__ == "__main__":
    # Test with Apple Q4 2024 filing
    filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928_htm.xml"

    parser = get_calculation_parser_for_filing(filing_url)

    if parser:
        print("\n=== Parent Concepts ===")
        for concept in parser.get_all_parent_concepts()[:10]:
            print(f"  {concept}")

        print("\n=== Assets Calculation Tree ===")
        parser.print_calculation_tree("us-gaap:Assets")

        # Example validation
        concept_values = {
            "us-gaap:Assets": 364980000000.0,
            "us-gaap:AssetsCurrent": 143566000000.0,
            "us-gaap:AssetsNoncurrent": 221414000000.0,
        }

        is_valid, reported, calculated = parser.validate_calculation(
            concept_values,
            "us-gaap:Assets"
        )

        print(f"\n=== Validation Example ===")
        print(f"Concept: us-gaap:Assets")
        print(f"Reported: ${reported/1e9:.2f}B")
        print(f"Calculated: ${calculated/1e9:.2f}B")
        print(f"Valid: {is_valid}")
