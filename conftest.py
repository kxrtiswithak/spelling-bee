import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that hit the live Free Dictionary API (may be slow)",
    )
