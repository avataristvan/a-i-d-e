import pytest
import os
import tempfile
import shutil

@pytest.fixture
def temp_dir():
    """Creates a temporary directory for tests that require a real file system."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)
