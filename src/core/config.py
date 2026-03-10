"""
Global configuration: selectors, timeouts, regex patterns, and constants.
"""

import re

# ─── Timeouts (ms) ───────────────────────────────────────────────────────────
PAGE_TIMEOUT = 60_000
NAVIGATION_TIMEOUT = 30_000
ELEMENT_TIMEOUT = 10_000
SCROLL_PAUSE = 1_500  # ms between scrolls in Maps results panel

# ─── Google Maps ─────────────────────────────────────────────────────────────
MAPS_BASE_URL = "https://www.google.com/maps"
MAPS_SEARCH_URL = "https://www.google.com/maps/search/{query}"

# CSS selectors for the Maps results feed
MAPS_SELECTORS = {
    "results_container": 'div[role="feed"]',
    "result_item": 'div[role="feed"] > div > div[jsaction]',
    "result_link": "a[href*='/maps/place/']",
    # Inside a place detail panel
    "place_name": "h1",
    "place_phone": 'button[data-item-id*="phone"] .Io6YTe, '
                   'button[aria-label*="Phone"] .Io6YTe, '
                   '[data-tooltip="Copy phone number"]',
    "place_website": 'a[data-item-id="authority"], '
                     'a[aria-label*="Website"], '
                     'a[data-item-id*="website"]',
    "place_address": 'button[data-item-id="address"] .Io6YTe, '
                     'button[aria-label*="Address"] .Io6YTe',
    "place_rating": 'div.F7nice span[aria-hidden="true"]',
    "place_reviews": 'div.F7nice span[aria-label*="reviews"], '
                     'div.F7nice span[aria-label*="reseñas"]',
    "place_category": 'button[jsaction*="category"], '
                      '[class*="DkEaL"]',
    "place_hours": '[aria-label*="Hours"], '
                   '[aria-label*="Horario"], '
                   '.o7FIHb',
    "place_description": '[class*="WeS02d"], '
                         'div.PYvSYb span',
    "place_price_level": 'span[aria-label*="Price"], '
                         'span[aria-label*="Precio"]',
    "place_plus_code": 'button[data-item-id="oloc"] .Io6YTe',
    "back_button": 'button[aria-label="Back"], button[aria-label="Atrás"]',
}

# ─── Regex patterns ──────────────────────────────────────────────────────────
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

SOCIAL_PATTERNS = {
    "instagram": re.compile(
        r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)/?", re.IGNORECASE
    ),
    "tiktok": re.compile(
        r"https?://(?:www\.)?tiktok\.com/@([a-zA-Z0-9_.]+)/?", re.IGNORECASE
    ),
    "facebook": re.compile(
        r"https?://(?:www\.|m\.)?facebook\.com/([a-zA-Z0-9.]+)/?", re.IGNORECASE
    ),
}

# Domains to skip when extracting emails (common false positives)
EMAIL_BLACKLIST_DOMAINS = {
    "example.com",
    "sentry.io",
    "wixpress.com",
    "nccdn.net",
    "w3.org",
    "schema.org",
    "googleapis.com",
    "cloudflare.com",
    "domain.com",
    "yourdomain.com",
}

# Social profile paths to skip (generic / not a business page)
SOCIAL_BLACKLIST_HANDLES = {
    "instagram",
    "tiktok",
    "facebook",
    "share",
    "sharer",
    "intent",
    "p",
    "explore",
    "reel",
    "reels",
    "stories",
    "hashtag",
    "login",
    "signup",
}

# ─── Output defaults ────────────────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_MAX_RESULTS = 20
