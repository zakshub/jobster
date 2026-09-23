from jobster.settings import SearchConfig


def test_search_config_has_safe_defaults():
    config = SearchConfig()
    assert config.cycle_minutes >= 15
    assert config.sources.remoteok.enabled is True
    assert config.sources.google_jobs.enabled is False
