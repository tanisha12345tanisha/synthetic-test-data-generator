from app.storage import LocalArtifactStorage

def test_storage_round_trip(tmp_path):
 storage=LocalArtifactStorage(tmp_path);stored=storage.write("user/run/file.json",b"hello");assert stored.size_bytes==5;assert storage.path(stored.object_path).read_bytes()==b"hello"
def test_storage_delete(tmp_path):
 storage=LocalArtifactStorage(tmp_path);stored=storage.write("x.txt",b"x");assert storage.delete(stored.object_path);assert not storage.delete(stored.object_path)
