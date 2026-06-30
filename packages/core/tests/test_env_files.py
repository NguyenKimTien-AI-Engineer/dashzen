from pathlib import Path

from core.env_files import env_file_candidates, load_env_files, resolve_env_files


def test_env_file_candidates_include_production_and_render_paths() -> None:
    names = {p.name for p in env_file_candidates()}
    assert ".env" in names
    assert ".env.production" in names
    assert Path("/etc/secrets/.env.production") in env_file_candidates()


def test_load_env_files_respects_existing_os_environ(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=from-file\nDASHZEN_TEST_ENV_VAR=from-file\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("DATABASE_URL", "from-os")
    monkeypatch.delenv("DASHZEN_TEST_ENV_VAR", raising=False)
    monkeypatch.chdir(tmp_path)

    import core.env_files as mod

    monkeypatch.setattr(mod, "env_file_candidates", lambda: [env_file])

    loaded = load_env_files()
    assert loaded == [env_file]
    assert __import__("os").environ["DATABASE_URL"] == "from-os"
    assert __import__("os").environ["DASHZEN_TEST_ENV_VAR"] == "from-file"


def test_resolve_env_files_only_existing(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env.production"
    env_file.write_text("APP_ENV=production\n", encoding="utf-8")

    import core.env_files as mod

    monkeypatch.setattr(mod, "env_file_candidates", lambda: [tmp_path / ".env", env_file])

    assert resolve_env_files() == [env_file]
