from aigent.schemas import ProductQuery, Receipt


def test_product_query_defaults():
    q = ProductQuery(query="headphones")
    assert q.query == "headphones"
    assert q.max_results == 3


def test_product_query_custom_max():
    q = ProductQuery(query="laptop", max_results=5)
    assert q.max_results == 5


def test_receipt_defaults():
    r = Receipt(product_name="AirPods", price=199.99)
    assert r.product_name == "AirPods"
    assert r.price == 199.99
    assert r.currency == "USD"


def test_receipt_custom_currency():
    r = Receipt(product_name="Sony WH-1000XM5", price=349.99, currency="EUR")
    assert r.currency == "EUR"
