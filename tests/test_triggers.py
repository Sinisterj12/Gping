from pathlib import Path

from gping_next.triggers import read_triggers


def test_sendnow_and_unlock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "SENDNOW").write_text("")
    (tmp_path / "UNLOCK_demo").write_text("")
    state = read_triggers()
    assert state.send_now is True
    assert state.unlocked_token == "demo"
    assert not (tmp_path / "SENDNOW").exists()
