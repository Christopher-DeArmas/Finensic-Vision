"""Static reference data used by the synthetic generator.

Kept separate from the generator logic so locations, merchant categories, and
occupations can be tuned without touching generation code.
"""

from __future__ import annotations

# --- Locations -------------------------------------------------------------
# (city -> (country, latitude, longitude))
LOCATIONS: dict[str, tuple[str, float, float]] = {
    # United States (domestic)
    "New York": ("United States", 40.7128, -74.0060),
    "Miami": ("United States", 25.7617, -80.1918),
    "Los Angeles": ("United States", 34.0522, -118.2437),
    "Chicago": ("United States", 41.8781, -87.6298),
    "Houston": ("United States", 29.7604, -95.3698),
    # Major international financial hubs (lower risk)
    "London": ("United Kingdom", 51.5074, -0.1278),
    "Frankfurt": ("Germany", 50.1109, 8.6821),
    "Zurich": ("Switzerland", 47.3769, 8.5417),
    "Dubai": ("United Arab Emirates", 25.2048, 55.2708),
    "Singapore": ("Singapore", 1.3521, 103.8198),
    "Hong Kong": ("Hong Kong", 22.3193, 114.1694),
    "Tokyo": ("Japan", 35.6762, 139.6503),
    "San Francisco": ("United States", 37.7749, -122.4194),
    "Seattle": ("United States", 47.6062, -122.3321),
    "Boston": ("United States", 42.3601, -71.0589),
    "Denver": ("United States", 39.7392, -104.9903),
    "Atlanta": ("United States", 33.7490, -84.3880),
    "Dallas": ("United States", 32.7767, -96.7970),
    "Phoenix": ("United States", 33.4484, -112.0740),
    "Toronto": ("Canada", 43.6532, -79.3832),
    "Mexico City": ("Mexico", 19.4326, -99.1332),
    "Sao Paulo": ("Brazil", -23.5505, -46.6333),
    "Paris": ("France", 48.8566, 2.3522),
    "Amsterdam": ("Netherlands", 52.3676, 4.9041),
    "Madrid": ("Spain", 40.4168, -3.7038),
    "Berlin": ("Germany", 52.5200, 13.4050),
    "Milan": ("Italy", 45.4642, 9.1900),
    "Stockholm": ("Sweden", 59.3293, 18.0686),
    "Mumbai": ("India", 19.0760, 72.8777),
    "Seoul": ("South Korea", 37.5665, 126.9780),
    "Shanghai": ("China", 31.2304, 121.4737),
    "Sydney": ("Australia", -33.8688, 151.2093),
    "Johannesburg": ("South Africa", -26.2041, 28.0473),
    # Higher-risk / offshore jurisdictions (for the high-risk rule)
    "Panama City": ("Panama", 8.9824, -79.5199),
    "George Town": ("Cayman Islands", 19.2866, -81.3744),
    "Valletta": ("Malta", 35.8989, 14.5146),
    "Nicosia": ("Cyprus", 35.1856, 33.3823),
    "Lagos": ("Nigeria", 6.5244, 3.3792),
    "Moscow": ("Russia", 55.7558, 37.6173),
}

US_CITIES = [
    "New York", "Miami", "Los Angeles", "Chicago", "Houston",
    "San Francisco", "Seattle", "Boston", "Denver", "Atlanta", "Dallas", "Phoenix",
]
INTL_CITIES = [
    "London", "Frankfurt", "Zurich", "Dubai", "Singapore", "Hong Kong", "Tokyo",
    "Toronto", "Mexico City", "Sao Paulo", "Paris", "Amsterdam", "Madrid", "Berlin",
    "Milan", "Stockholm", "Mumbai", "Seoul", "Shanghai", "Sydney", "Johannesburg",
]
HIGH_RISK_CITIES = [
    "Panama City",
    "George Town",
    "Valletta",
    "Nicosia",
    "Lagos",
    "Moscow",
]

# Countries flagged as high-risk jurisdictions for scoring.
HIGH_RISK_COUNTRIES = {
    "Panama",
    "Cayman Islands",
    "Malta",
    "Cyprus",
    "Nigeria",
    "Russia",
}


# --- Merchant catalog ------------------------------------------------------
# (category, mcc, is_high_risk)
MERCHANT_CATEGORIES: list[tuple[str, str, bool]] = [
    ("grocery", "5411", False),
    ("restaurant", "5812", False),
    ("retail", "5999", False),
    ("utilities", "4900", False),
    ("travel", "4722", False),
    ("electronics", "5732", False),
    ("healthcare", "8062", False),
    ("fuel", "5541", False),
    ("subscription", "5968", False),
    ("education", "8220", False),
    # High-risk categories
    ("crypto_exchange", "6051", True),
    ("casino", "7995", True),
    ("money_transfer", "4829", True),
    ("precious_metals", "5944", True),
    ("art_dealer", "5971", True),
]

# Themed merchant name fragments per category for believable names.
MERCHANT_NAME_HINTS: dict[str, list[str]] = {
    "grocery": ["Market", "Grocers", "Fresh Foods", "Provisions"],
    "restaurant": ["Bistro", "Grill", "Kitchen", "Trattoria"],
    "retail": ["Emporium", "Outfitters", "Goods", "Depot"],
    "utilities": ["Power & Light", "Energy", "Utilities", "Waterworks"],
    "travel": ["Airways", "Travel", "Voyages", "Getaways"],
    "electronics": ["Electronics", "Tech", "Gadgets", "Circuit"],
    "healthcare": ["Clinic", "Pharmacy", "Medical", "Health"],
    "fuel": ["Fuel", "Petroleum", "Gas & Go", "Energy Stop"],
    "subscription": ["Media", "Stream", "Cloud", "Digital"],
    "education": ["Academy", "Institute", "Learning", "College"],
    "crypto_exchange": ["Coin", "Crypto", "Chain", "Ledger", "Digital Assets"],
    "casino": ["Casino", "Palace", "Royale", "Fortune Gaming"],
    "money_transfer": ["Remit", "Money Transfer", "Wire Express", "SendCash"],
    "precious_metals": ["Bullion", "Gold Exchange", "Precious Metals", "Mint"],
    "art_dealer": ["Fine Art", "Gallery", "Auction House", "Collections"],
}


# --- Occupations -----------------------------------------------------------
OCCUPATIONS: list[tuple[str, float]] = [
    # (title, approximate annual income USD)
    ("Software Engineer", 130_000),
    ("Registered Nurse", 85_000),
    ("Teacher", 62_000),
    ("Accountant", 78_000),
    ("Marketing Manager", 98_000),
    ("Construction Worker", 55_000),
    ("Retail Associate", 38_000),
    ("Small Business Owner", 120_000),
    ("Physician", 240_000),
    ("Attorney", 165_000),
    ("Financial Analyst", 95_000),
    ("Truck Driver", 58_000),
    ("Electrician", 66_000),
    ("Graphic Designer", 60_000),
    ("Restaurant Owner", 110_000),
    ("Real Estate Agent", 92_000),
    ("Consultant", 140_000),
    ("Import/Export Trader", 135_000),
    ("Jewelry Dealer", 105_000),
    ("Art Dealer", 115_000),
]
