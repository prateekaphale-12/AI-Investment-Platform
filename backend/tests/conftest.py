"""Pytest loads this before tests; tell the app not to start schedulers during TestClient lifespan."""

import os

os.environ.setdefault("PYTEST_RUNNING", "1")
