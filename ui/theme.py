"""
theme.py
========
Modern dark "engineering tool" theme: Fusion palette + QSS, and small
runtime-drawn toolbar icons (no external icon assets / icon-font dependency).
"""
from __future__ import annotations

import math

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPalette, QColor, QIcon, QPixmap, QPainter, QPen, QPolygonF, QFont

BG_WINDOW = "#1b1e25"
BG_PANEL = "#22252e"
BG_FIELD = "#2a2e39"
BG_HOVER = "#333849"
BORDER = "#3a3f4d"
TEXT = "#e7eaf1"
TEXT_MUTED = "#94a0b3"
ACCENT = "#4f8cff"
ACCENT_HOVER = "#6ea0ff"
ACCENT_PRESSED = "#3d73d9"
DANGER = "#ef5350"
SUCCESS = "#3ecf8e"
WARNING = "#f5a623"


def apply_theme(app: QtWidgets.QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG_WINDOW))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base, QColor(BG_FIELD))
    pal.setColor(QPalette.AlternateBase, QColor(BG_PANEL))
    pal.setColor(QPalette.ToolTipBase, QColor(BG_PANEL))
    pal.setColor(QPalette.ToolTipText, QColor(TEXT))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.Button, QColor(BG_FIELD))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.BrightText, QColor(DANGER))
    pal.setColor(QPalette.Link, QColor(ACCENT))
    pal.setColor(QPalette.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#0d1016"))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor(TEXT_MUTED))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(TEXT_MUTED))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor(TEXT_MUTED))
    app.setPalette(pal)
    app.setStyleSheet(_QSS)
    app.setFont(QFont("Segoe UI", 9))


_QSS = f"""
QMainWindow, QDialog {{ background: {BG_WINDOW}; }}
QWidget {{ color: {TEXT}; }}

QGroupBox {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: {TEXT};
}}

QPushButton {{
    background: {BG_FIELD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 14px;
    color: {TEXT};
}}
QPushButton:hover {{ background: {BG_HOVER}; border-color: {ACCENT}; }}
QPushButton:pressed {{ background: {ACCENT_PRESSED}; color: white; }}
QPushButton:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER}; }}
QPushButton#PillButtonPrimary {{
    background: {ACCENT}; border: none; color: #0d1016; font-weight: 600;
}}
QPushButton#PillButtonPrimary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#DangerButton {{ border-color: {DANGER}; }}
QPushButton#DangerButton:hover {{ background: {DANGER}; color: white; }}

QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QPlainTextEdit,
QTableWidget, QListWidget {{
    background: {BG_FIELD};
    border: 1px solid {BORDER};
    border-radius: 5px;
    selection-background-color: {ACCENT};
    selection-color: #0d1016;
    padding: 3px 6px;
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QListWidget::item, QTableWidget::item {{ padding: 3px; }}
QListWidget::item:selected, QTableWidget::item:selected {{
    background: {ACCENT}; color: #0d1016;
}}
QHeaderView::section {{
    background: {BG_PANEL}; color: {TEXT_MUTED};
    border: none; border-bottom: 1px solid {BORDER}; padding: 4px;
}}

QCheckBox::indicator {{
    width: 15px; height: 15px; border-radius: 4px;
    border: 1px solid {BORDER}; background: {BG_FIELD};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QMenuBar {{ background: {BG_WINDOW}; }}
QMenuBar::item:selected {{ background: {BG_HOVER}; }}
QMenu {{ background: {BG_PANEL}; border: 1px solid {BORDER}; }}
QMenu::item:selected {{ background: {ACCENT}; color: #0d1016; }}

QStatusBar {{ background: {BG_WINDOW}; color: {TEXT_MUTED}; }}

QToolBar {{
    background: {BG_PANEL}; border: none; border-bottom: 1px solid {BORDER};
    padding: 4px; spacing: 4px;
}}
QToolButton {{
    background: transparent; border-radius: 6px; padding: 5px; color: {TEXT};
}}
QToolButton:hover {{ background: {BG_HOVER}; }}
QToolButton:checked {{ background: {ACCENT}; }}

QScrollBar:vertical {{ background: {BG_WINDOW}; width: 11px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar:horizontal {{ background: {BG_WINDOW}; height: 11px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}

QPlainTextEdit {{ font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; }}

#StatusPill {{
    background: rgba(34, 37, 46, 235);
    border: 1px solid {BORDER};
    border-radius: 16px;
}}
#StatusPillLabel {{ color: {TEXT}; font-weight: 500; }}
"""


def _blank_pixmap(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    return pm


def make_icon(kind: str, size: int = 18, color: str = TEXT) -> QIcon:
    pm = _blank_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 1.6)
    pen.setJoinStyle(Qt.RoundJoin)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    m = size * 0.18
    r = QRectF(m, m, size - 2 * m, size - 2 * m)

    if kind == "navigate":
        poly = QPolygonF([
            QPointF(size * 0.22, size * 0.15), QPointF(size * 0.22, size * 0.85),
            QPointF(size * 0.42, size * 0.66), QPointF(size * 0.55, size * 0.88),
            QPointF(size * 0.66, size * 0.82), QPointF(size * 0.52, size * 0.60),
            QPointF(size * 0.78, size * 0.55)])
        p.setBrush(QColor(color))
        p.drawPolygon(poly)
    elif kind == "limit":
        poly = QPolygonF([
            QPointF(r.left(), r.top()),
            QPointF(r.right(), r.top() + r.height() * 0.3),
            QPointF(r.right() - r.width() * 0.15, r.bottom()),
            QPointF(r.left() + r.width() * 0.1, r.bottom() - r.height() * 0.1)])
        p.drawPolygon(poly)
    elif kind == "point":
        p.setBrush(QColor(color))
        p.drawEllipse(r.center(), r.width() * 0.22, r.width() * 0.22)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(r)
    elif kind == "line":
        p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.top()))
        p.setBrush(QColor(color))
        p.drawEllipse(QPointF(r.left(), r.bottom()), 1.6, 1.6)
        p.drawEllipse(QPointF(r.right(), r.top()), 1.6, 1.6)
    elif kind == "polygon":
        poly = QPolygonF([
            QPointF(r.center().x(), r.top()), QPointF(r.right(), r.center().y()),
            QPointF(r.center().x(), r.bottom()), QPointF(r.left(), r.center().y())])
        p.drawPolygon(poly)
    elif kind == "finish":
        p.drawLine(QPointF(r.left(), r.center().y()),
                   QPointF(r.left() + r.width() * 0.4, r.bottom()))
        p.drawLine(QPointF(r.left() + r.width() * 0.4, r.bottom()),
                   QPointF(r.right(), r.top()))
    elif kind == "generate":
        p.drawEllipse(r)
        cx, cy, rad = r.center().x(), r.center().y(), r.width() / 2
        for i in range(8):
            a = i * math.pi / 4
            p.drawLine(QPointF(cx + rad * 0.8 * math.cos(a), cy + rad * 0.8 * math.sin(a)),
                       QPointF(cx + rad * 1.15 * math.cos(a), cy + rad * 1.15 * math.sin(a)))
    elif kind in ("zoom-in", "zoom-out"):
        rr = QRectF(r.left(), r.top(), r.width() * 0.75, r.height() * 0.75)
        p.drawEllipse(rr)
        p.drawLine(QPointF(rr.right() - 1, rr.bottom() - 1), QPointF(r.right(), r.bottom()))
        cx, cy, rad = rr.center().x(), rr.center().y(), rr.width() * 0.28
        p.drawLine(QPointF(cx - rad, cy), QPointF(cx + rad, cy))
        if kind == "zoom-in":
            p.drawLine(QPointF(cx, cy - rad), QPointF(cx, cy + rad))
    elif kind == "fit":
        w4 = r.width() * 0.28
        for (cx, cy, dx, dy) in [(r.left(), r.top(), 1, 1), (r.right(), r.top(), -1, 1),
                                  (r.left(), r.bottom(), 1, -1), (r.right(), r.bottom(), -1, -1)]:
            p.drawLine(QPointF(cx, cy), QPointF(cx + dx * w4, cy))
            p.drawLine(QPointF(cx, cy), QPointF(cx, cy + dy * w4))
    elif kind == "trash":
        body = QRectF(r.left(), r.top() + r.height() * 0.2, r.width(), r.height() * 0.75)
        p.drawRect(body)
        p.drawLine(QPointF(r.left() - 1, body.top()), QPointF(r.right() + 1, body.top()))
        p.drawLine(QPointF(r.center().x() - r.width() * 0.15, r.top()),
                   QPointF(r.center().x() + r.width() * 0.15, r.top()))
    elif kind == "void":
        p.drawRect(r)
        p.drawLine(QPointF(r.left(), r.top()), QPointF(r.right(), r.bottom()))
        p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.top()))
    elif kind == "measure":
        p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.top()))
        for t in (0.25, 0.5, 0.75):
            cx = r.left() + t * (r.right() - r.left())
            cy = r.bottom() + t * (r.top() - r.bottom())
            dx, dy = (r.right() - r.left()), (r.top() - r.bottom())
            length = (dx * dx + dy * dy) ** 0.5 or 1.0
            nx, ny = -dy / length, dx / length
            tick = size * 0.09
            p.drawLine(QPointF(cx - nx * tick, cy - ny * tick),
                       QPointF(cx + nx * tick, cy + ny * tick))
    p.end()
    return QIcon(pm)
