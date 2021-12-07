"""
This module is for handling the covid data
"""

# Imports
import logging
from requests import get
from json import dumps
from sched import scheduler
import time

data_scheduler = scheduler(time.time, time.sleep)


def process_json_data(covid_java_data: dict) -> (int, int, int):
    """
    Processes the json data into three variables, of the number of cases in the last 7 days,
    current hospital cases and the total number of deaths

    :param covid_java_data: dictionary of the java data
    :type: dict

    :returns: The three variables as specified
    :rtype: (int, int, int)
    """
    last7days_cases = 0
    current_hospital_cases = 0
    total_deaths = 0

    # Process for the last7days_cases
    for i in range(2, 8):
        last7days_cases += int(float(covid_java_data[i]["newCasesByPublishDate"]))

    # Process for the current_hospital_cases
    for i in covid_java_data:
        value = i["hospitalCases"]
        if value is not None:
            current_hospital_cases = int(value)
            break

    # Process for the total_deaths
    for i in covid_java_data:
        value = i["cumDeaths28DaysByDeathDate"]
        if value is not None:
            total_deaths = int(value)
            break

    return last7days_cases, current_hospital_cases, total_deaths


def covid_api_request(location: str = "Exeter", location_type: str = "ltla") -> dict:
    """
    Makes a request to get the current covid data from a specified location

    :param location: The specified location
    :type: str
    :param location_type: The location type
    :type: str

    :returns: Dictionary of the covid data
    :type: dict
    """

    url = 'https://api.coronavirus.data.gov.uk/v1/data'
    filters = [
        f"areaType={location_type}",
        f"areaName={location}"
    ]
    data_structure = {
        "areaName": "areaName",
        "areaType": "areaType",
        "date": "date",
        "cumDeaths28DaysByDeathDate": "cumDeaths28DaysByDeathDate",
        "hospitalCases": "hospitalCases",
        "newCasesByPublishDate": "newCasesByPublishDate"
    }

    api_params = {
        "filters": str.join(";", filters),
        "structure": dumps(data_structure, separators=(",", ":"))
    }

    response = get(url, params=api_params, timeout=10)

    if response.status_code >= 400:
        logging.error(f'Request failed: {response.text}')
        raise RuntimeError(f'Request failed: {response.text}')

    url_response = response.json()
    return url_response


def schedule_covid_updates(update_interval: float = 3600.0, update_name: str = None) -> None:
    """
    Adds an event to update the covid data at a specified time

    :param update_interval: time of the update in seconds from current time
    :type: float
    :param update_name: Name of the update
    :type: str

    :rtype: None
    """
    from main import dump_data
    data_scheduler.enter(update_interval, 1, dump_data, (update_name,))


# Parse csv data
def parse_csv_data(csv_filename: str) -> list:
    """
    Parses the csv data into a list of the data

    :param csv_filename: the name of the csv file
    :type: str

    :returns: the parsed csv data
    :rtype: list
    """
    list_of_data = []
    file = open(csv_filename).readlines()
    for i in file:
        list_of_data.append(i.strip())
    return list_of_data


# Process covid csv data
def process_covid_csv_data(covid_csv_data: list) -> (int, int, int):
    """
    Processes the parsed csv data into the number of cases in the last 7 days,
    current hospital cases and the total number of deaths

    :param covid_csv_data: the parsed csv data
    :type: list

    :return: The three variables as specified
    :rtype: (int, int, int)
    """
    last7days_cases = 0

    processed_list_of_data = []
    total_deaths = 0
    processed_list_of_data.clear()

    for i in covid_csv_data:
        processed_list_of_data.append(i.split(","))
    processed_list_of_data.pop(0)
    # Process for the last7days_cases
    for i in range(2, 9):
        last7days_cases += int(float(processed_list_of_data[i][6]))

    # Process for the current_hospital_cases
    current_hospital_cases = processed_list_of_data[0][5]
    if current_hospital_cases == "":
        current_hospital_cases = 0
    else:
        current_hospital_cases = int(float(processed_list_of_data[0][5]))

    # Process for the total_deaths
    for i in processed_list_of_data:
        if i[4] == "":
            continue
        else:
            total_deaths = int(float(i[4]))
            break

    return last7days_cases, current_hospital_cases, total_deaths
