import json

from gping_next.web_local import LocalUIBridge


def test_ui_locked_state(tmp_path, monkeypatch):
    monkeypatch.setattr("gping_next.web_local.UI_DIR", tmp_path)
    bridge = LocalUIBridge()
    status_file = tmp_path / "status.json"
    data = json.loads(status_file.read_text())
    assert data["locked"] is True
    bridge.unlock("token")
    bridge.publish("green", None, None, {"gateway": "up"})
    data = json.loads(status_file.read_text())
    assert data["locked"] is False
    assert data["summary"]["gateway"] == "up"
