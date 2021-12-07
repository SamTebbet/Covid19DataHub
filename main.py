"""
This module is the main module for the program and runs the website
"""

# Imports
from json import dump
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request
)
from covid_data_handling import *
from news_data_handling import *

# Main setup
FORMAT = '%(levelname)s: %(asctime)s %(message)s'
logging.basicConfig(filename='pysys.log', level=logging.INFO, format=FORMAT)

main_scheduler = scheduler(time.time, time.sleep)
app = Flask(__name__)


class Covid19DataHub:
    """Class for the Covid-19 Data Hub website"""

    def __init__(self):
        """Initialisation function for the class"""
        # Variables local to the class
        self.local_7day_cases = 0
        self.local_location = ""
        self.nat_7day_cases = 0
        self.hospital_cases = 0
        self.total_deaths = 0
        self.national_location = ""
        self.current_articles = []
        self.update_content = []
        self.deleted_titles = []
        self.time_arr = []

        # Updates the JSON files on initialisation
        dump_news()
        dump_data()

    def render_app(self) -> object:
        """
        Gets the covid data and news, also renders the website template with all the data

        :returns: Renders index.html to the host server
        :rtype: object
        """

        main_scheduler.run(blocking=False)
        data_scheduler.run(blocking=False)
        news_scheduler.run(blocking=False)

        # Gets the data and news variables
        self.get_data()
        self.get_news()

        # Renders the template of the website with all the data
        return render_template('index.html',
                               title='Covid19 DataHub',
                               local_7day_infections=self.local_7day_cases,
                               location=self.local_location,
                               nation_loaction=self.national_location,
                               national_7day_infections=self.nat_7day_cases,
                               hospital_cases=self.hospital_cases,
                               deaths_total=self.total_deaths,
                               news_articles=self.current_articles,
                               notification=self.current_articles,
                               updates=self.update_content,
                               alarm=self.update_content)

    def app_updates(self) -> object:
        """
        This function runs whenever the website refreshes and parses all the data

        :returns: The render_app() function
        :rtype: object
        """

        # Makes a dictionary of the update content
        update_dict = {"title": request.args.get("two"), "content": "", "alarm": request.args.get("update"),
                       "repeat": False, "data": False, "news": False, "already_repeated": True}
        repeat = request.args.get("repeat")
        data = request.args.get("covid-data")
        news = request.args.get('news')

        news_pop = request.args.get("notif")
        update_pop = request.args.get("update_item")

        if news is not None:
            update_dict["news"] = True
        if data is not None:
            update_dict["data"] = True
        if repeat is not None:
            update_dict["repeat"] = True
            update_dict["already_repeated"] = False

        update_dict["content"] = f"{update_dict['alarm']} {repeat} {data} {news}"

        # Adds the update to scheduler if there is a title in the content
        # There must be a title to the content or there shouldn't be an update
        if update_dict["title"] is not None:
            # Checks if the user submitted a time
            # If not it returns back to index
            if update_dict['alarm'] == '':
                logging.info("Invalid time submitted")
                return self.render_app()

            self.update_content.append(update_dict)
            self.update_scheduler(dict(update_dict))
            logging.info("Schedulers Updated")

        # Pops articles
        if news_pop is not None:
            self.pop_articles(news_pop)
            logging.info(f"News Article {news_pop} removed from list")

        # Pops updates
        if update_pop is not None:
            self.pop_updates(update_pop, True)
            logging.info(f"Update {update_pop} removed from scheduler")

        return self.render_app()

    def pop_updates(self, title: str, popping: bool = False) -> None:
        """
        This function is used to remove updates from the scheduler

        :param title: title of the update
        :type: str
        :param popping: Whether or not the user wants to completely remove the update
        :type: bool

        :rtype: None
        """
        # Loops through all the schedulers and deletes the events which match with the time and the title
        for i in self.time_arr:
            # i[0] is the time
            # i[1] is True if it's not a repeated time
            try:
                for k in data_scheduler.queue:
                    data_repeated = i[1]
                    if k[3][0] == title:
                        if popping:
                            data_scheduler.cancel(k)
                        else:
                            if k[0] == i[0] and data_repeated is True:
                                data_scheduler.cancel(k)
            except Exception as data_err:
                logging.error(f"{data_err}: Error when deleting data schedules")

            try:
                for k in news_scheduler.queue:
                    news_repeated = i[1]
                    if k[3][0] == title:
                        if popping:
                            news_scheduler.cancel(k)
                        else:
                            if k[0] == i[0] and news_repeated is True:
                                data_scheduler.cancel(k)
            except Exception as news_err:
                logging.error(f"{news_err}: Error when deleting news schedules")

            try:
                for k in main_scheduler.queue:
                    main_repeated = i[1]
                    if k[3][0] == title:
                        if popping:
                            main_scheduler.cancel(k)
                        else:
                            if k[0] == i[0] and main_repeated is True:
                                main_scheduler.cancel(k)
                            else:
                                # If the time is repeated, it sets i[1] to True
                                i[1] = True
            except Exception as main_err:
                logging.error(f"{main_err}: Error when deleting main schedules")

        # Pops the updates from the website column
        try:
            for i in self.update_content:
                if i['title'] == title:
                    if i['already_repeated'] or popping:
                        self.update_content.remove(i)
                    else:
                        i['already_repeated'] = True
        except Exception as update_err:
            logging.error(f"{update_err}: Error when deleting the update content")

    def pop_articles(self, title: str) -> None:
        """
        This function is used to remove news articles from the list

        :param title: title of the news article
        :type: str

        :rtype: None
        """
        with open('covid_news.json', 'r') as file:
            all_articles = load(file)

        for i in self.current_articles:
            if i['title'] == title:
                self.deleted_titles.append(i)
                all_articles.remove(i)
                # Adds the new articles to self.current_articles
                self.current_articles.clear()
                for j in range(4):
                    self.current_articles.append(all_articles[j])
                with open('covid_news.json', 'w') as file:
                    dump(all_articles, file)

    def update_scheduler(self, update_dictionary: dict) -> None:
        """
        This function adds new events to schedulers

        :param update_dictionary: dictionary of the update content
        :type: dict

        :rtype: None
        """

        # List of the functions used
        functions = []
        if update_dictionary['news']:
            functions.append(self.get_news)
        if update_dictionary['data']:
            functions.append(self.get_data)
        functions.append(self.pop_updates)

        if update_dictionary['repeat'] and not update_dictionary["already_repeated"]:
            # Adds the repeated time to the schedulers
            alarm_time = format_time(update_dictionary['alarm'], True)
            # Adds to schedulers depending on the function
            for i in functions:
                if i == self.pop_updates:
                    main_scheduler.enter(alarm_time, priority=1, action=i,
                                         argument=(update_dictionary['title'],))
                elif i == self.get_news:
                    update_news(alarm_time, update_dictionary['title'])
                else:
                    schedule_covid_updates(alarm_time, update_dictionary['title'])

            # Adds the alarm_time and the title to the time_arr
            # This is useful for popping the updates later
            self.time_arr.append([alarm_time, update_dictionary['already_repeated']])
            # Does the function again but this time it won't go through the repeated step
            update_dictionary['already_repeated'] = True

            logging.info(f"Update added at {alarm_time} with {functions}")
            self.update_scheduler(update_dictionary)
        else:
            alarm_time = format_time(update_dictionary['alarm'])
            # Adds to schedulers depending on the function
            for i in functions:
                if i == self.pop_updates:
                    main_scheduler.enter(alarm_time, priority=1, action=i,
                                         argument=(update_dictionary['title'],))
                elif i == self.get_news:
                    update_news(alarm_time, update_dictionary['title'])
                else:
                    schedule_covid_updates(alarm_time, update_dictionary['title'])

            self.time_arr.append([alarm_time, update_dictionary['already_repeated']])
            logging.info(f"Update added at {alarm_time} with {functions}")

    def get_data(self) -> None:
        """
        Gets the data from the JSON file

        :rtype: None
        """
        with open('covid_data.json', 'r') as file:
            data = load(file)
            logging.info("Getting data from JSON file")
        self.local_7day_cases = data[0][0]
        self.local_location = data[1]
        self.nat_7day_cases, self.hospital_cases, self.total_deaths = data[2]
        self.national_location = data[3]

    def get_news(self) -> None:
        """
        Gets the news from the JSON file and returns the 4 currently used articles

        :returns: None
        """
        with open('covid_news.json', 'r') as file:
            all_articles = load(file)
            logging.info("Getting news from JSON file")
        used_articles = []

        with open('config.json', 'r') as config_file:
            cfg = load(config_file)
        with open('config.json', 'w') as config_file:
            cfg['deleted_titles'] = []
            dump(cfg, config_file)

        for i in range(4):
            used_articles.append(all_articles[i])
        self.current_articles = used_articles


def dump_news(s: str = None) -> None:
    """
    Dumps news articles into a JSON file

    :param s: Update title - parameter not used
    :type: str

    :returns: None
    """

    try:
        all_articles = news_api_request()['articles']
    except Exception as api_err:
        logging.error(f"{api_err}: Failed to update news")
        all_articles = []

    with open('covid_news.json', 'w') as file:
        dump(all_articles, file)
        logging.info("Updating news")


def dump_data(s: str = None) -> None:
    """
    Dumps covid data into a JSON file using the locations specified in the config file

    :param s: Update title, parameter not used
    :type: str

    :returns: None
    """
    with open('config.json', 'r') as file:
        cfg = load(file)

    try:
        all_data = [process_json_data(covid_api_request(cfg['local_location'], cfg['local_location_type'])['data']),
                    covid_api_request(cfg['local_location'], cfg['local_location_type'])['data'][0]['areaName'],
                    process_json_data(covid_api_request(cfg["national_location"],
                                                        cfg["national_location_type"])['data']),
                    covid_api_request(cfg["national_location"], cfg["national_location_type"])['data'][0]['areaName']]
    except Exception as data_err:
        logging.error(f"{data_err}: Failed to update data")
        all_data = [[0, 0, 0], '', [0, 0, 0], '']

    with open('covid_data.json', 'w') as file:
        dump(all_data, file)
        logging.info("Updating data")


def format_time(time_to_format: str, repeating: bool = False) -> float:
    """
    Formats 24hr time into seconds from the current time

    :param time_to_format: 24hr clock time of the update time
    :type: str
    :param repeating: If the update should repeat or not
    :type: bool

    :returns: Alarm time in seconds from current time
    :rtype: float
    """

    date = datetime.today().strftime("%Y-%m-%d")
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    current_time = time.time()
    update_time = time.mktime(time.strptime(f"{date} {time_to_format}:00", "%Y-%m-%d %H:%M:%S"))
    if current_time > update_time:
        date = tomorrow

    if repeating:
        alarms = time.mktime(time.strptime(f"{tomorrow} {time_to_format}:00", "%Y-%m-%d %H:%M:%S")) - time.time()
    else:
        alarms = time.mktime(time.strptime(f"{date} {time_to_format}:00", "%Y-%m-%d %H:%M:%S")) - time.time()
    return float(alarms)


if __name__ == '__main__':
    server = Covid19DataHub()
    app.add_url_rule('/', view_func=server.render_app)
    app.add_url_rule('/index/', view_func=server.app_updates)
    # Clearing the 'pysys.log' file on use
    # File is automatically created when the program is run
    try:
        with open('pysys.log', 'w') as f:
            f.write('')
    except Exception as e:
        print(f"{e} file \"pysys.log\" does not exist")
        pass

    logging.info("Setup complete")
    app.run(debug=True)
