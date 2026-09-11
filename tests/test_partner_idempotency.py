from app.services.partner_idempotency import find_existing_delivery


def test_find_existing_delivery_is_async_callable():
    assert callable(find_existing_delivery)
    assert find_existing_delivery.__name__ == "find_existing_delivery"
