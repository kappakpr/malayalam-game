import math
import random
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy, QWidget
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF, QRadialGradient

_BUTTON_PALETTE = {
    "orange": ("#FF8C42", "#F27424", "8px 14px"),
    "green": ("#2D6A4F", "#1B4332", "8px 16px"),
}

FROST_CARD_STYLE = """
    QPushButton#WordCard, QFrame#FrostCard {
        background-color: rgba(255, 255, 255, 165);
        color: #1B4332;
        border: 2px solid rgba(149, 213, 178, 195);
        border-radius: 16px;
    }
    QPushButton#WordCard:hover {
        background-color: rgba(244, 251, 247, 210);
        border-color: #40916C;
    }
    QPushButton#WordCard:pressed {
        background-color: rgba(232, 248, 240, 225);
        border-color: #1B4332;
    }
"""


def make_translucent_widget(widget: QWidget, with_border: bool = False) -> QWidget:
    """Make a container, header bar, or scroll wrapper transparent so painted backdrops show through."""
    widget.setAttribute(Qt.WA_TranslucentBackground, True)
    border_rule = "" if with_border else "border: none;"
    widget.setStyleSheet(f"background: transparent; {border_rule}")
    return widget


def style_frosted_panel(
    panel: QWidget,
    object_name: str = "FrostedBanner",
    alpha: int = 125,
    radius: int = 18,
) -> QWidget:
    """Style a wide banner or container with a soft translucent tint so stars blend through."""
    clamped_alpha = max(40, min(230, alpha))
    panel.setObjectName(object_name)
    panel.setAttribute(Qt.WA_TranslucentBackground, True)
    panel.setStyleSheet(
        f"QWidget#{object_name}, QFrame#{object_name} {{"
        f"  background-color: rgba(255, 255, 255, {clamped_alpha});"
        f"  border-radius: {radius}px;"
        f"  border: 1.5px solid rgba(149, 213, 178, 180);"
        f"}}"
    )
    return panel

def make_action_button(
    text: str,
    on_click,
    variant: str = "orange",
    min_height: int = 34,
    parent=None,
) -> QPushButton:
    """Create a styled action button with explicit high-contrast colors."""
    bg, hover_bg, padding = _BUTTON_PALETTE.get(variant, _BUTTON_PALETTE["orange"])
    if min_height <= 32:
        padding = "5px 10px"
        font_size = 12
    else:
        font_size = 13

    btn = QPushButton(text, parent)
    btn.setMinimumHeight(min_height)
    btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
    btn.setStyleSheet(
        f"QPushButton {{"
        f"  background-color: {bg};"
        f"  color: #FFFFFF;"
        f"  border: none;"
        f"  border-radius: 11px;"
        f"  padding: {padding};"
        f"  font-size: {font_size}px;"
        f"  font-weight: bold;"
        f"}}"
        f"QPushButton:hover {{"
        f"  background-color: {hover_bg};"
        f"  color: #FFFFFF;"
        f"}}"
    )
    btn.clicked.connect(on_click)
    return btn


def _draw_plus(painter: QPainter, cx: float, cy: float, arm: float, color: QColor) -> None:
    pen = QPen(color, 2.5, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
    painter.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))


def draw_four_point_star(
    painter: QPainter,
    cx: float,
    cy: float,
    outer_r: float,
    inner_r: float,
    color: QColor,
    glow_strength: float = 0.0,
) -> None:
    """Draw a crisp 4-point star centered at (cx, cy) with an optional radial glow."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)

    clamped_glow = max(0.0, min(1.0, glow_strength))
    if clamped_glow > 0.02:
        center = QPointF(cx, cy)
        glow_radius = outer_r * (1.8 + 1.1 * clamped_glow)
        gradient = QRadialGradient(center, glow_radius)

        core_alpha = int(min(130, 28 + 85 * clamped_glow))
        mid_alpha = int(min(70, 10 + 40 * clamped_glow))

        gradient.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), core_alpha))
        gradient.setColorAt(0.45, QColor(color.red(), color.green(), color.blue(), mid_alpha))
        gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))

        painter.setBrush(gradient)
        painter.drawEllipse(center, glow_radius, glow_radius)

    points = []
    for i in range(8):
        angle = i * (math.pi / 4.0) - (math.pi / 2.0)
        radius = outer_r if i % 2 == 0 else inner_r
        points.append(QPointF(cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    painter.setBrush(color)
    painter.drawPolygon(QPolygonF(points))
    painter.restore()


def make_kid_pattern_tile(tile_size: int = 128) -> QPixmap:
    """Generate a more visible, non-copyrighted geometric tile with dots and pluses."""
    tile = QPixmap(tile_size, tile_size)
    tile.fill(Qt.transparent)

    painter = QPainter(tile)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)

    dots = [
        (20, 22, 7.5, QColor(255, 183, 77, 95)),    # warm sunny amber
        (96, 24, 6.5, QColor(129, 212, 250, 95)),  # sky blue
        (54, 68, 7.5, QColor(255, 138, 165, 90)),  # soft coral pink
        (24, 104, 6.5, QColor(116, 198, 157, 95)), # soft mint
        (98, 102, 7.5, QColor(255, 209, 102, 95)), # soft gold
    ]
    for cx, cy, radius, color in dots:
        painter.setBrush(color)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    _draw_plus(painter, cx=58, cy=24, arm=5.0, color=QColor(82, 183, 136, 105))
    _draw_plus(painter, cx=104, cy=66, arm=4.5, color=QColor(244, 162, 97, 105))

    painter.end()
    return tile


def create_twinkling_stars(width: int, height: int, count: int = 22) -> list[dict]:
    """Create randomized star descriptors positioned across the window."""
    rng = random.Random()
    palette = [
        (255, 193, 7),    # warm star gold
        (255, 140, 66),   # bright tangerine
        (64, 169, 255),   # sky sparkle
        (155, 114, 255),  # soft violet star
        (45, 106, 79),    # deep emerald accent
    ]
    stars = []
    for _ in range(count):
        r, g, b = rng.choice(palette)
        base_r = rng.uniform(6.5, 11.5)
        stars.append({
            "x_ratio": rng.uniform(0.03, 0.97),
            "y_ratio": rng.uniform(0.04, 0.96),
            "outer_r": base_r,
            "inner_r": base_r * 0.34,
            "rgb": (r, g, b),
            "phase": rng.uniform(0.0, 2.0 * math.pi),
            "speed": rng.uniform(1.4, 3.6),
            "min_alpha": rng.randint(45, 95),
            "max_alpha": rng.randint(175, 235),
        })
    return stars