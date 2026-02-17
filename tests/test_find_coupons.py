from unittest.mock import MagicMock, patch
from pricewise.tools.find_coupons import find_coupons


def test_find_coupons_returns_formatted_string():
    mock_response = {
        "results": [
            {
                "url": "https://retailmenot.com/example",
                "content": "Save 20% on Sony headphones with code SAVE20",
                "score": 0.95,
            },
            {
                "url": "https://slickdeals.net/example",
                "content": "Sony WH-1000XM5 on sale for $299, reg $349",
                "score": 0.9,
            },
        ],
    }

    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response

    with patch("pricewise.tools.find_coupons.get_tavily", return_value=mock_instance):
        result = find_coupons.invoke({"product_or_retailer": "Sony headphones", "max_results": 2})
        assert isinstance(result, str)
        assert "20%" in result or "Sony" in result


def test_find_coupons_handles_no_results():
    mock_response = {"results": []}
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response

    with patch("pricewise.tools.find_coupons.get_tavily", return_value=mock_instance):
        result = find_coupons.invoke({"product_or_retailer": "obscure product xyz"})
        assert "No active coupons" in result
