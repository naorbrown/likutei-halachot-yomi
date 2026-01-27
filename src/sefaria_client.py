"""
Sefaria API client for fetching Likutei Halachot texts.
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


@dataclass
class SefariaText:
    """Represents text fetched from Sefaria."""
    ref: str
    he_ref: str
    hebrew_text: List[str]
    english_text: List[str] = field(default_factory=list)
    sefaria_url: str = ""

    @property
    def hebrew_combined(self) -> str:
        """Get combined Hebrew text as a single string."""
        return "\n\n".join(self._flatten_text(self.hebrew_text))

    @property
    def english_combined(self) -> str:
        """Get combined English text as a single string."""
        return "\n\n".join(self._flatten_text(self.english_text))

    def _flatten_text(self, text_data: Any) -> List[str]:
        """Flatten nested text arrays into a list of strings."""
        if isinstance(text_data, str):
            return [self._strip_html(text_data)] if text_data.strip() else []
        elif isinstance(text_data, list):
            result = []
            for item in text_data:
                result.extend(self._flatten_text(item))
            return result
        return []

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text."""
        clean = re.compile(r'<.*?>')
        return re.sub(clean, '', text)


class SefariaClient:
    """Client for interacting with Sefaria API."""

    BASE_URL = "https://www.sefaria.org/api"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LikuteiHalachotYomiBot/1.0"
        })

    def get_text(self, ref: str, context: int = 0) -> Optional[SefariaText]:
        """
        Fetch text from Sefaria by reference.

        Args:
            ref: Sefaria reference (e.g., "Likutei_Halakhot,_Orach_Chaim,_Laws_of_Morning_Conduct.1.1")
            context: Number of surrounding sections to include

        Returns:
            SefariaText object or None if fetch failed
        """
        # Clean and encode the reference
        clean_ref = ref.replace(" ", "_")
        encoded_ref = quote(clean_ref, safe="_,.")

        url = f"{self.BASE_URL}/texts/{encoded_ref}"
        params = {"context": context}

        logger.debug(f"Fetching from Sefaria: {url}")

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.error(f"Sefaria API error: {data['error']}")
                return None

            return SefariaText(
                ref=data.get("ref", ref),
                he_ref=data.get("heRef", ""),
                hebrew_text=data.get("he", []),
                english_text=data.get("text", []),
                sefaria_url=f"https://www.sefaria.org/{clean_ref}"
            )

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {ref} from Sefaria")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {ref} from Sefaria: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Sefaria response for {ref}: {e}")
            return None

    def get_index(self, text_name: str = "Likutei_Halakhot") -> Optional[Dict[str, Any]]:
        """
        Fetch the index/structure of a text.

        Args:
            text_name: Name of the text

        Returns:
            Index data dictionary or None if fetch failed
        """
        url = f"{self.BASE_URL}/index/{text_name}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching index for {text_name}: {e}")
            return None

    def validate_ref(self, ref: str) -> bool:
        """
        Validate that a reference exists and has content.

        Args:
            ref: Sefaria reference to validate

        Returns:
            True if reference is valid and has content
        """
        text = self.get_text(ref)
        return text is not None and (text.hebrew_text or text.english_text)

    def get_all_sections(self) -> List[Dict[str, str]]:
        """
        Get all sections of Likutei Halachot.

        Returns:
            List of section dictionaries with title, heTitle, and ref format
        """
        index = self.get_index()
        if not index:
            return []

        sections = []
        self._extract_sections(index.get("schema", {}), sections, [])
        return sections

    def _extract_sections(
        self,
        node: Dict[str, Any],
        sections: List[Dict[str, str]],
        parent_path: List[str]
    ):
        """Recursively extract sections from index schema."""
        title = node.get("title", "")
        he_title = node.get("heTitle", "")

        if "nodes" in node:
            current_path = parent_path + [title] if title else parent_path
            for child in node["nodes"]:
                self._extract_sections(child, sections, current_path)
        elif title:
            # This is a leaf node (actual section)
            # Build the Sefaria reference format
            path_parts = parent_path + [title]
            # Skip the first element if it's "Likutei Halakhot"
            if path_parts and path_parts[0] == "Likutei Halakhot":
                path_parts = path_parts[1:]

            ref_parts = ["Likutei_Halakhot"] + [p.replace(" ", "_") for p in path_parts]
            ref = ",_".join(ref_parts)

            sections.append({
                "title": title,
                "heTitle": he_title,
                "ref_base": ref,
                "path": " > ".join(parent_path) if parent_path else ""
            })


# Singleton instance
_client: Optional[SefariaClient] = None


def get_sefaria_client() -> SefariaClient:
    """Get or create the Sefaria client singleton."""
    global _client
    if _client is None:
        _client = SefariaClient()
    return _client
