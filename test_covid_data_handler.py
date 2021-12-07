from covid_data_handling import parse_csv_data
from covid_data_handling import process_covid_csv_data
from covid_data_handling import covid_api_request
from covid_data_handling import schedule_covid_updates


def test_parse_csv_data():
    data = parse_csv_data('nation_2021-10-28.csv')
    assert len(data) == 639


def test_process_covid_csv_data():
    last7days_cases, current_hospital_cases, total_deaths = \
        process_covid_csv_data(parse_csv_data(
            'nation_2021-10-28.csv'))
    assert last7days_cases == 240_299
    assert current_hospital_cases == 7_019
    assert total_deaths == 141_544


def test_covid_api_request():
    data = covid_api_request()
    assert isinstance(data, dict)


def test_schedule_covid_updates():
    schedule_covid_updates(update_interval=10, update_name='update test')
