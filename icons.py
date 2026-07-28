"""
Metro Events — inline SVG icon set.
Hand-built, line-style icons (24x24 viewbox, round strokes) used in place
of emoji throughout the app. Registered as a Jinja global: {{ icon('name') }}
"""
from markupsafe import Markup

_ICONS = {
    "bolt": '<path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z"/>',
    "home": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9.5 21v-6h5v6"/>',
    "party": '<path d="M4 21 9 9l6 6-9 5-2 1Z"/><path d="M9 9l6 6M14 4l1.5 1.5M18 8l1.5 1.5M11 2.5 12.5 4"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 20c0-3.3 2.6-5.8 5.8-5.8s5.8 2.5 5.8 5.8"/><path d="M16 8.2a3 3 0 1 1 3.6 2.9"/><path d="M15.8 14.3c2.7.4 4.7 2.6 4.7 5.7"/>',
    "user": '<circle cx="12" cy="8" r="3.4"/><path d="M5.5 20c0-3.6 2.9-6.3 6.5-6.3s6.5 2.7 6.5 6.3"/>',
    "star": '<path d="M12 3.5 14.6 9l6 .9-4.3 4.2 1 6-5.3-2.8-5.3 2.8 1-6L3.4 9.9l6-.9Z"/>',
    "box": '<path d="M3.5 7.5 12 3l8.5 4.5V16l-8.5 4.5L3.5 16Z"/><path d="M3.5 7.5 12 12l8.5-4.5"/><path d="M12 12v8.5"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.2"/><path d="M3.5 9.5h17"/><path d="M8 3v4M16 3v4"/>',
    "handshake": '<path d="M2.5 12 6 8.5l3 2 3.5-3 3 1.5 3-2 3 3.5-3 3-2.7-1.4-3.5 3-2.6-1.6"/><path d="M8.5 15.3 11 17.6l2-1.7 2 1.9 2-1.7"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12 19 4"/><path d="M16 7l2.5 2.5M19 4l2 2"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "settings": '<circle cx="12" cy="12" r="3.1"/><path d="M12 3.5v2.4M12 18.1v2.4M20.5 12h-2.4M5.9 12H3.5M17.7 6.3l-1.7 1.7M8 16l-1.7 1.7M17.7 17.7 16 16M8 8 6.3 6.3"/>',
    "logout": '<path d="M9 21H5.5A2.5 2.5 0 0 1 3 18.5v-13A2.5 2.5 0 0 1 5.5 3H9"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    "menu": '<path d="M4 6.5h16M4 12h16M4 17.5h16"/>',
    "wallet": '<path d="M3.5 7.5A2 2 0 0 1 5.5 5.5h12A2 2 0 0 1 19.5 7.5v2"/><path d="M3.5 7.5v9a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-6.5a2 2 0 0 0-2-2H7"/><circle cx="16" cy="13" r="1.3"/>',
    "coins": '<circle cx="9" cy="9" r="5.5"/><path d="M14.5 9.8a5.5 5.5 0 1 1 0 9.7"/><path d="M9 6.5V11.5M6.8 9H11.2"/>',
    "trash": '<path d="M4.5 7h15"/><path d="M9.5 7V4.8c0-.7.5-1.3 1.2-1.3h2.6c.7 0 1.2.6 1.2 1.3V7"/><path d="M6.5 7l.8 12a2 2 0 0 0 2 1.9h5.4a2 2 0 0 0 2-1.9L17.5 7"/><path d="M10 11v6M14 11v6"/>',
    "clipboard": '<rect x="5" y="4.5" width="14" height="17" rx="2"/><rect x="8.5" y="3" width="7" height="3.2" rx="1"/><path d="M8.5 11h7M8.5 14.7h7M8.5 18.4h4"/>',
    "edit": '<path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3Z"/><path d="M13.5 7.5l3 3"/>',
    "check": '<path d="M4.5 12.5 9 17l10.5-10.5"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12.3l2.7 2.7L16.3 9"/>',
    "arrow-right": '<path d="M4.5 12h15M13.5 5.5 20 12l-6.5 6.5"/>',
    "arrow-left": '<path d="M19.5 12h-15M10.5 5.5 4 12l6.5 6.5"/>',
    "pin": '<path d="M12 21s-6.5-6.1-6.5-11A6.5 6.5 0 0 1 18.5 10c0 4.9-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>',
    "alert": '<path d="M12 3.5 21.5 20h-19Z"/><path d="M12 9.5v4.5"/><circle cx="12" cy="17" r="0.9" fill="currentColor" stroke="none"/>',
    "palette": '<path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.1 0 1.8-.9 1.8-1.9 0-.5-.2-.9-.5-1.3-.3-.4-.5-.8-.5-1.3 0-1 .8-1.8 1.8-1.8h2A4 4 0 0 0 21 10.4C21 6.5 17 3.5 12 3.5Z"/><circle cx="7.3" cy="11" r="1.1" fill="currentColor" stroke="none"/><circle cx="9.8" cy="7.3" r="1.1" fill="currentColor" stroke="none"/><circle cx="14.5" cy="7" r="1.1" fill="currentColor" stroke="none"/><circle cx="17" cy="10.8" r="1.1" fill="currentColor" stroke="none"/>',
    "message": '<path d="M4 5.5h16v10.5H9.5L5 20v-4H4Z"/>',
    "mail": '<rect x="3.5" y="5.5" width="17" height="13" rx="2"/><path d="M4.5 7 12 12.5 19.5 7"/>',
    "phone": '<path d="M7 3.5h3l1.3 4.3-2 1.6a11.5 11.5 0 0 0 5.3 5.3l1.6-2 4.3 1.3v3a2 2 0 0 1-2.2 2A17.5 17.5 0 0 1 5 5.7 2 2 0 0 1 7 3.5Z"/>',
    "building": '<rect x="4.5" y="3.5" width="10" height="17" rx="1"/><path d="M14.5 9.5h5v11h-5"/><path d="M7.5 7h1.2M11 7h1.2M7.5 10.5h1.2M11 10.5h1.2M7.5 14h1.2M11 14h1.2M17 13h1.5M17 16.5h1.5"/>',
    "bar-chart": '<path d="M4 20V10.5M11 20V4M18 20v-7"/><path d="M2.5 20h19"/>',
    "gift": '<rect x="4" y="9.5" width="16" height="11" rx="1"/><path d="M4 13.5h16"/><path d="M12 9.5V21"/><path d="M12 9.5c-1-3.2-3-4.5-4.3-3.6-1.3.9-.4 3.6 4.3 3.6Z"/><path d="M12 9.5c1-3.2 3-4.5 4.3-3.6 1.3.9.4 3.6-4.3 3.6Z"/>',
    "award": '<circle cx="12" cy="8.5" r="5"/><path d="M9 12.8 7.5 21l4.5-2.4L16.5 21 15 12.8"/>',
    "gem": '<path d="M5 8.5 8.5 4h7L19 8.5 12 20.5Z"/><path d="M5 8.5h14M9.5 4l-1.8 4.5L12 20.5M14.5 4l1.8 4.5L12 20.5"/>',
    "heart": '<path d="M12 20.3S3.5 15 3.5 9a4.7 4.7 0 0 1 8.5-2.7A4.7 4.7 0 0 1 20.5 9c0 6-8.5 11.3-8.5 11.3Z"/>',
    "bell": '<path d="M6 17v-5.5a6 6 0 0 1 12 0V17l1.8 2.3H4.2Z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    "dot": '<circle cx="12" cy="12" r="5" fill="currentColor" stroke="none"/>',
    "x": '<path d="M5.5 5.5l13 13M18.5 5.5l-13 13"/>',
    "refresh": '<path d="M4.5 12a7.5 7.5 0 0 1 12.6-5.4L19.5 9"/><path d="M19.5 4.5V9H15"/><path d="M19.5 12a7.5 7.5 0 0 1-12.6 5.4L4.5 15"/><path d="M4.5 19.5V15H9"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M19.5 19.5 15.2 15.2"/>',
    "file": '<path d="M6.5 3.5h8l4 4V20a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z"/><path d="M14 3.5V8h4"/>',
    "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.2 2.3 3.4 5.3 3.4 8.5s-1.2 6.2-3.4 8.5c-2.2-2.3-3.4-5.3-3.4-8.5S9.8 5.8 12 3.5Z"/>',
    "truck": '<rect x="2.5" y="7" width="12" height="9.5" rx="1"/><path d="M14.5 10h4l3 3.3V16.5h-7Z"/><circle cx="7" cy="18" r="1.7"/><circle cx="17.5" cy="18" r="1.7"/>',
    "inbox": '<path d="M3.5 12h5l1.8 3h3.4l1.8-3h5"/><path d="M6 5h12l2.5 7v6.5a1.5 1.5 0 0 1-1.5 1.5h-14A1.5 1.5 0 0 1 3.5 18.5V12Z"/>',
    "save": '<path d="M5 3.5h11L20 8v11.5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-15a1 1 0 0 1 1-1Z"/><path d="M7.5 3.5V9h7V3.5"/><path d="M7.5 14h9v6.5h-9Z"/>',
    "image": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="10" r="1.7"/><path d="M4 18l5.5-5.5 3 3L18.5 10 20.5 12"/>',
    "smile": '<circle cx="12" cy="12" r="8.5"/><path d="M8.3 14.3c1 1.3 2.3 2 3.7 2s2.7-.7 3.7-2"/><path d="M9 9.5h.01M15 9.5h.01"/>',
    "megaphone": '<path d="M3.5 10.5v3l4-.3v3.6a1.4 1.4 0 0 0 1.4 1.4h.4a1.4 1.4 0 0 0 1.4-1.6l-.4-3.6 9.3-3.4V6.3L7.5 10.8Z"/><path d="M9.9 16.5l.7 4"/>',
    "sparkle": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>',
}

def icon(name: str, size: int = 18, cls: str = "", stroke_width: float = 1.75) -> Markup:
    """Render an inline SVG icon by name. Falls back to a small circle if unknown."""
    inner = _ICONS.get(name, '<circle cx="12" cy="12" r="8"/>')
    classes = f"me-icon {cls}".strip()
    return Markup(
        f'<svg class="{classes}" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{inner}</svg>'
    )

ICON_NAMES = set(_ICONS.keys())
