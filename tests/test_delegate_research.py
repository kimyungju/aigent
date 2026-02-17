from unittest.mock import MagicMock, patch
from pricewise.tools.delegate_research import delegate_research, _research_one
from pricewise.schemas import ProductResearchItem


def test_delegate_research_multiple_products():
    mock_responses = [
        {
            "results": [
                {
                    "url": "https://laptop.com",
                    "content": "Dell XPS 15 - $1299 with Intel i7",
                    "score": 0.9,
                }
            ]
        },
        {
            "results": [
                {
                    "url": "https://monitor.com",
                    "content": "LG UltraWide 34\" - $599",
                    "score": 0.85,
                }
            ]
        },
    ]

    mock_instance = MagicMock()
    mock_instance.invoke.side_effect = mock_responses

    with patch("pricewise.tools.delegate_research.get_tavily", return_value=mock_instance):
        result = delegate_research.invoke({
            "products": [
                {"product_name": "laptop", "budget": 1500.0},
                {"product_name": "monitor", "budget": 700.0},
            ],
            "total_budget": 2000.0,
        })

        assert isinstance(result, str)
        assert "Multi-Product Research" in result
        assert "2 items" in result


def test_delegate_research_handles_error():
    mock_response = {"error": "API error"}
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response

    with patch("pricewise.tools.delegate_research.get_tavily", return_value=mock_instance):
        result = delegate_research.invoke({
            "products": [{"product_name": "test product"}],
        })

        assert "Could not find results" in result


def test_research_one_success():
    mock_response = {
        "results": [
            {"url": "https://example.com", "content": "Great laptop $999", "score": 0.9}
        ]
    }
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response

    with patch("pricewise.tools.delegate_research.get_tavily", return_value=mock_instance):
        result = _research_one(ProductResearchItem(product_name="laptop"))
        assert result["success"] is True
        assert result["product"] == "laptop"


def test_research_one_no_results():
    mock_response = {"results": []}
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response

    with patch("pricewise.tools.delegate_research.get_tavily", return_value=mock_instance):
        result = _research_one(ProductResearchItem(product_name="nothing"))
        assert result["success"] is False
