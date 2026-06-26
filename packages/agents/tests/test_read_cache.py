from agents.tools.read_cache import ReadCache


def test_invalidate_workspace_listing_clears_list_file_only() -> None:
    cache = ReadCache()
    cache.set("list_file", {}, '[{"name": "memory.md"}]')
    cache.set("read_file", {"path": "spec.md"}, "content")
    cache.set("list_file", {"prefix": "x"}, "other")

    cache.invalidate_workspace_listing()

    assert cache.get("list_file", {}) is None
    assert cache.get("list_file", {"prefix": "x"}) is None
    assert cache.get("read_file", {"path": "spec.md"}) == "content"


def test_invalidate_path_does_not_clear_list_file_cache() -> None:
    cache = ReadCache()
    cache.set("list_file", {}, '[{"name": "memory.md"}]')

    cache.invalidate_path("spec.md")

    assert cache.get("list_file", {}) == '[{"name": "memory.md"}]'
