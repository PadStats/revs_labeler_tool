from __future__ import annotations

import os
import requests
from typing import Any

# Default endpoint; override via env var if needed.
ENDPOINT = os.getenv("BB_RESOLVER_ENDPOINT", "https://fetch-image-urls-lmy27ronba-uc.a.run.app/fetch-image-urls")

# Debug: Check what the endpoint value is
print(f"DEBUG: BB_RESOLVER_ENDPOINT env var: {repr(os.getenv('BB_RESOLVER_ENDPOINT'))}")
print(f"DEBUG: ENDPOINT value: {repr(ENDPOINT)}")


class BackblazeResolverError(RuntimeError):
    """Raised when fetching a signed URL fails."""


def resolve_bb_path(bb_url: str, endpoint: str | None = None) -> str:
    """Return a public URL for *bb_url* using the Cloud Run resolver service."""

    ep = endpoint or ENDPOINT
    if not ep:
        raise BackblazeResolverError(f"BB_RESOLVER_ENDPOINT is empty or not set. Please check your environment configuration.")
    
    try:
        print(f"DEBUG: Resolving bb_url: {bb_url}")
        print(f"DEBUG: Using endpoint: {ep}")
        
        r = requests.post(ep, json={"row_prefixes": [bb_url]}, timeout=10)
        print(f"DEBUG: API response status: {r.status_code}")
        print(f"DEBUG: API response text: {r.text}")
        
        r.raise_for_status()
        data: Any = r.json()
        print(f"DEBUG: API response JSON: {data}")
        
        # Fix: Access the correct structure based on actual API response
        if "images" in data and data["images"]:
            # API returns: {"images": [{"row_prefix": "...", "signed_urls": ["url"]}]}
            signed_url = data["images"][0]["signed_urls"][0]
        elif "signed_urls" in data:
            # Fallback for old API format: {"signed_urls": {"path": "url"}}
            signed_url = data["signed_urls"][bb_url]
        else:
            raise BackblazeResolverError(f"Unexpected API response structure: {data}")
        
        print(f"DEBUG: Resolved signed_url: {signed_url}")
        
        if not signed_url:
            raise BackblazeResolverError(f"API returned empty signed URL for {bb_url}")
            
        return signed_url
    except Exception as exc:  # noqa: BLE001
        raise BackblazeResolverError(f"Failed to resolve {bb_url}: {exc}") from exc 