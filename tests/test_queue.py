from gping_next.telemetry import QueueStorage


def test_queue_dedupes(tmp_path):
    storage = QueueStorage(tmp_path)
    storage._save_sync("health", {"x": 1}, "id-123")
    storage._save_sync("health", {"x": 1}, "id-123")
    items = storage._load_sync()
    assert len(items) == 1
