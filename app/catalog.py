"""What the appearance settings can choose from. Everything here ships inside the container."""

THEMES = {
    "midnight": {"en": "Midnight", "de": "Mitternacht"},
    "glass": {"en": "Glass", "de": "Glas"},
    "sunrise": {"en": "Sunrise", "de": "Morgenrot"},
    "playful": {"en": "Playful", "de": "Verspielt"},
    "paper": {"en": "Paper", "de": "Papier"},
}

FONTS = {
    "inter": {"label": "Inter", "family": "'Inter Variable'"},
    "nunito": {"label": "Nunito", "family": "'Nunito Variable'"},
    "fredoka": {"label": "Fredoka", "family": "'Fredoka Variable'"},
    "playfair-display": {
        "label": "Playfair Display",
        "family": "'Playfair Display Variable'",
    },
    "jetbrains-mono": {
        "label": "JetBrains Mono",
        "family": "'JetBrains Mono Variable'",
    },
}

# Drawn in CSS, no image file behind them.
PATTERNS = {
    "aurora-gradient": {"en": "Aurora gradient", "de": "Polarlicht-Verlauf"},
    "sunset-gradient": {"en": "Sunset gradient", "de": "Abendrot-Verlauf"},
    "bubbles": {"en": "Bubbles", "de": "Seifenblasen"},
    "waves": {"en": "Waves", "de": "Wellen"},
}

PHOTOS = {
    "aurora": {"en": "Northern lights", "de": "Nordlicht"},
    "alpine-lake": {"en": "Alpine lake", "de": "Bergsee"},
    "forest-fog": {"en": "Forest in fog", "de": "Nebelwald"},
    "dunes": {"en": "Dunes", "de": "Dünen"},
    "autumn": {"en": "Autumn leaves", "de": "Herbstlaub"},
    "beach-sunset": {"en": "Beach at sunset", "de": "Strand am Abend"},
    "starry-night": {"en": "Starry night", "de": "Sternennacht"},
}

BACKGROUND_KINDS = ("none", "pattern", "photo", "upload")
LANGUAGES = ("auto", "en", "de")


def is_valid_background(kind: str, value: str, uploads: list[str]) -> bool:
    if kind == "none":
        return True
    if kind == "pattern":
        return value in PATTERNS
    if kind == "photo":
        return value in PHOTOS
    if kind == "upload":
        return value in uploads
    return False
