from services.catalog.search_codec import decode_search_document


def test_catalog_document() -> None:
    assert decode_search_document('{"id":"p-1"}') == {"id": "p-1"}

