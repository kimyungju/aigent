from unittest.mock import MagicMock, patch
from pricewise.tools.check_availability import check_availability


def test_check_availability_returns_formatted_string():
    mock_response = {
        "results": [
            {
                "url": "https://bestbuy.com/product",
                "content": "PlayStation 5 - In Stock at Best Buy, ready for pickup",
                "score": 0.95,
            },
            {
                "url": "https://amazon.com/product",
                "content": "PS5 Console - Currently out of stock",
                "score": 0.9,
            },
        ],
    }

    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response

    with patch("pricewise.tools.check_availability.get_tavily", return_value=mock_instance):
        result = check_availability.invoke({"product_name": "PlayStation 5", "max_sources": 2})
        assert isinstance(result, str)
        assert "In Stock" in result or "out of stock" in result


def test_check_availability_handles_no_results():
    mock_response = {"results": []}
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response

    with patch("pricewise.tools.check_availability.get_tavily", return_value=mock_instance):
        result = check_availability.invoke({"product_name": "nonexistent product"})
        assert "No availability information found" in result
