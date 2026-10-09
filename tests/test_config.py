from pathlib import Path

from mcpSuunto.config import AppConfig


def test_config_loads_relative_paths(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[paths]\nonedrive_dir = "OneDrive/fit"\ninbox_dir = "inbox"\n',
        encoding="utf-8",
    )

    config = AppConfig.load(config_file)

    assert config.onedrive_dir.name == "fit"
    assert config.inbox_dir.name == "inbox"
