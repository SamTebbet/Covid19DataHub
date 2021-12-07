"""
This module is for handling the covid news data
"""
from requests import get
from json import load
from sched import scheduler
import time
import logging

news_scheduler = scheduler(time.time, time.sleep)


def news_api_request(covid_terms: str = "Covid Covid-19 coronavirus") -> dict:
    """
    Requests data from the covid news api for python

    :param covid_terms: string of the api query
    :type: str

    :return: list of news articles
    :rtype: list
    """

    with open('config.json', 'r') as f:
        cfg = load(f)
        api_key = cfg['key']
    endpoint = 'https://newsapi.org/v2/everything?'
    sort_by = 'relevancy'
    sources = 'bbc-news'
    language = 'en'

    covid_terms = covid_terms.lower()
    covid_terms_arr = covid_terms.split(" ")
    news_arr = []
    fin_arr = []
    for i in covid_terms_arr:
        temp_article = get(f'{endpoint}q={i}&sources={sources}&language={language}&sortBy={sort_by}&apiKey={api_key}')
        if temp_article.status_code >= 400:
            logging.error(f'Request failed: {temp_article.text}')
            raise RuntimeError(f'Request failed: {temp_article.text}')
        news_arr.append(temp_article.json())
    for i in news_arr:
        for j in i["articles"]:
            fin_arr.append(j)

    arr = list(remove_duplicates(fin_arr))
    new_dictionary = {'articles': arr}
    return new_dictionary


def remove_duplicates(arr: list) -> list:
    """
    Removes duplicates from the list of news articles

    :param arr: list of news articles
    :type: list

    :returns: news article if it's not seen already
    :rtype: list
    """
    seen_already = []
    for x in arr:
        if x not in seen_already:
            yield x
            seen_already.append(x)


def update_news(update_time: float = 84600.0, update_title: str = None) -> None:
    """
    Adds an event to update the news articles at a specified time

    :param update_time: time of the update in seconds
    :type: float
    :param update_title: The title of the update
    :type: str

    :rtype: None
    """
    from main import dump_news
    news_scheduler.enter(update_time, priority=1, action=dump_news, argument=(update_title,))
