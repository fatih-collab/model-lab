"""Fixture pytest: model kecil berbobot acak (lihat tests/tiny_models.py)."""
import os

os.environ.setdefault("GLOWMATCH_LOAD_MODELS", "0")

import pytest

from tests import tiny_models as tm
from tests.tiny_models import PARSER_LABELS, fake_label_map, fake_parse, tiny_segformer  # noqa: F401 (dipakai test)


@pytest.fixture(scope="session")
def undertone_dir(tmp_path_factory):
    return tm.build_undertone_dir(tmp_path_factory.mktemp("undertone"))


@pytest.fixture(scope="session")
def undertone_model(undertone_dir):
    return tm.load_undertone(undertone_dir)


@pytest.fixture(scope="session")
def season_bundle():
    return tm.build_season_bundle()


@pytest.fixture(scope="session")
def season_dir(tmp_path_factory, season_bundle):
    return tm.build_season_dir(tmp_path_factory.mktemp("season"), season_bundle)


@pytest.fixture(scope="session")
def season_model(season_dir):
    return tm.load_season(season_dir)
