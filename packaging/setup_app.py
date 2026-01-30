"""
Phoenix App Packaging — py2app Setup
=====================================

Creates macOS .app bundle from Phoenix.

Usage:
    cd phoenix/packaging
    python setup_app.py py2app

The resulting .app will be in dist/Phoenix.app

S41 Track D: DMG Packaging (Current Phoenix)
"""

from setuptools import setup

# App configuration
APP = ["../widget/menu_bar.py"]  # Main entry point
DATA_FILES = [
    # Include narrator templates
    ("narrator/templates", [
        "../narrator/templates/alert.jinja2",
        "../narrator/templates/briefing.jinja2",
        "../narrator/templates/health.jinja2",
        "../narrator/templates/trade.jinja2",
    ]),
    # Include schemas
    ("schemas", [
        "../schemas/beads.yaml",
        "../schemas/cse_schema.yaml",
        "../schemas/orientation_bead.yaml",
    ]),
    # Include CSO knowledge
    ("cso/knowledge", [
        "../cso/knowledge/conditions.yaml",
    ]),
]

OPTIONS = {
    "argv_emulation": False,
    "iconfile": None,  # Add icon later
    "plist": {
        "CFBundleName": "Phoenix",
        "CFBundleDisplayName": "Phoenix Trading System",
        "CFBundleGetInfoString": "Constitutional Trading System",
        "CFBundleIdentifier": "io.warboar.phoenix",
        "CFBundleVersion": "0.41.0",
        "CFBundleShortVersionString": "0.41.0",
        "NSHighResolutionCapable": True,
        "LSUIElement": True,  # Menu bar app (no dock icon)
    },
    "packages": [
        "phoenix",
        "governance",
        "brokers",
        "cso",
        "cfp",
        "athena",
        "hunt",
        "validation",
        "orientation",
        "narrator",
        "notification",
        "widget",
        "daemons",
        "structlog",
        "pydantic",
        "yaml",
        "jinja2",
    ],
    "excludes": [
        # Exclude test packages
        "pytest",
        "mypy",
        "ruff",
        # Exclude dev dependencies
        "pre_commit",
        # Exclude unnecessary stdlib
        "tkinter",
        "turtle",
    ],
    "includes": [
        "rumps",  # Menu bar framework
        "telegram",  # Telegram bot
    ],
}

setup(
    name="Phoenix",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
