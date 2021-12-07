from news_data_handling import news_api_request
from news_data_handling import update_news


def test_news_api_request():
    assert news_api_request()
    assert news_api_request('Covid COVID-19 coronavirus') == news_api_request()


def test_update_news():
    update_news(10, 'test')
