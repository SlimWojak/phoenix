"""Setup file for editable install with flat layout."""
from setuptools import find_packages, setup

# Find all packages with __init__.py
packages = find_packages(where=".", exclude=["tests", "tests.*"])

setup(
    name="phoenix",
    version="0.30.0",
    packages=packages,
    package_dir={"": "."},
)
