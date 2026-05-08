"""Test bootstrap. Set env flags BEFORE any app imports."""
import os

os.environ.setdefault("COACH_TEST_NO_SCHEMA", "1")
