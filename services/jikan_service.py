import requests
import time
from datetime import datetime
from typing import Optional


JIKAN_BASE_URL = "https://api.jikan.moe/v4"
REQUEST_DELAY  = 0.6   # seconds between requests (Jikan rate limit: 3 req/sec)

# Jikan v4 genre IDs for manga
GENRE_IDS = {
    "Action":        1,
    "Adventure":     2,
    "Comedy":        4,
    "Mystery":       7,
    "Drama":         8,
    "Fantasy":      10,
    "Horror":       14,
    "Romance":      22,
    "Sci-Fi":       24,
    "Sports":       30,
    "Slice of Life":36,
    "Supernatural": 37,
    "Avant Garde":   5,
    "Gourmet":      47,
    # Award Winning has no direct Jikan genre ID — skip
}


class JikanService:
    """Handles all communication with the Jikan API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        url = f"{JIKAN_BASE_URL}/{endpoint}"
        try:
            time.sleep(REQUEST_DELAY)
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[JikanService] Request failed: {e}")
            return None

    def search_manga(self, query: str, page: int = 1, limit: int = 20) -> list[dict]:
        """Search manga by keyword."""
        params = {"q": query, "page": page, "limit": limit, "type": "manga"}
        data = self._get("manga", params=params)
        if not data or "data" not in data:
            return []
        return [self._clean_manga(item) for item in data["data"]]

    def search_by_genres(
        self,
        genre_names: list[str],
        status: str = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Search manga by genre(s) using Jikan genre IDs.
        genre_names: list of genre strings matching GENRE_IDS keys.
        """
        # Map genre names → IDs, skip unknown
        ids = [str(GENRE_IDS[g]) for g in genre_names if g in GENRE_IDS]
        if not ids:
            return []

        params = {
            "genres": ",".join(ids),
            "limit":  limit,
            "type":   "manga",
            "order_by": "score",
            "sort":     "desc",
        }
        # Jikan status values: "publishing", "complete", "hiatus"
        if status:
            status_map = {
                "Publishing": "publishing",
                "Finished":   "complete",
                "On Hiatus":  "hiatus",
            }
            jikan_status = status_map.get(status)
            if jikan_status:
                params["status"] = jikan_status

        data = self._get("manga", params=params)
        if not data or "data" not in data:
            return []
        return [self._clean_manga(item) for item in data["data"]]

    def get_manga_by_id(self, mal_id: int) -> Optional[dict]:
        """Get full manga detail by MAL ID."""
        data = self._get(f"manga/{mal_id}")
        if not data or "data" not in data:
            return None
        return self._clean_manga(data["data"])

    def get_top_manga(self, limit: int = 8) -> list[dict]:
        """Get top manga from MAL."""
        params = {"limit": limit, "type": "manga"}
        data = self._get("top/manga", params=params)
        if not data or "data" not in data:
            return []
        return [self._clean_manga(item) for item in data["data"]]

    def get_manga_recommendations(self, mal_id: int) -> list[dict]:
        """Get manga recommendations based on a manga."""
        data = self._get(f"manga/{mal_id}/recommendations")
        if not data or "data" not in data:
            return []
        results = []
        for item in data["data"][:5]:
            entry = item.get("entry", {})
            results.append({
                "mal_id":    entry.get("mal_id"),
                "title":     entry.get("title", "Unknown"),
                "cover_url": entry.get("images", {}).get("jpg", {}).get("image_url"),
            })
        return results

    def _clean_manga(self, raw: dict) -> dict:
        """Normalize and clean raw API data."""
        images    = raw.get("images", {}).get("jpg", {})
        cover_url = images.get("large_image_url") or images.get("image_url")

        authors      = raw.get("authors", [])
        author_names = ", ".join([a.get("name", "") for a in authors if a.get("name")])

        genres       = raw.get("genres", []) + raw.get("themes", [])
        genre_names  = ", ".join([g.get("name", "") for g in genres if g.get("name")])

        published = raw.get("published", {})
        year      = None
        if published.get("from"):
            try:
                year = int(published["from"][:4])
            except (ValueError, TypeError):
                pass

        status_map = {
            "Publishing":   "Publishing",
            "Finished":     "Finished",
            "On Hiatus":    "On Hiatus",
            "Discontinued": "Finished",
        }
        status = status_map.get(raw.get("status", ""), raw.get("status", ""))

        return {
            "mal_id":     raw.get("mal_id"),
            "title":      raw.get("title") or "Unknown Title",
            "title_en":   raw.get("title_english") or "",
            "synopsis":   raw.get("synopsis") or "",
            "cover_url":  cover_url or "",
            "authors":    author_names,
            "genres":     genre_names,
            "status":     status,
            "score":      raw.get("score"),
            "chapters":   raw.get("chapters"),
            "year":       year,
            "is_manual":  False,
            "fetched_at": datetime.now(),
        }
