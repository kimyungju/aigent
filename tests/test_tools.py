from unittest.mock import MagicMock, patch
from aigent.tools.search_product import search_product


def test_search_product_returns_formatted_string():
    mock_results = [
        {"url": "https://example.com/headphones", "content": "Best wireless headphones - Sony WH-1000XM5 for $349"},
        {"url": "https://example.com/buds", "content": "AirPods Pro 2 - $249 great noise cancellation"},
    ]

    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_results

    with patch("aigent.tools.search_product._get_tavily", return_value=mock_instance):
        result = search_product.invoke({"query": "wireless headphones", "max_results": 2})
        assert isinstance(result, str)
        assert "Sony" in result or "headphones" in result
