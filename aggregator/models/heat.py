import sys
from typing import List, Union
from time import sleep
import psycopg2
import pandas as pd
import os
import numpy as np
from models.logger import setup_logging_config
from models.maths import linear_regression, get_hash, hash_already_completed
from models.schemas import HeatSchema
from models.env import MAX_RETRY_COUNT, RETRY_SLEEP_COUNT
from sqlalchemy.orm import Session

log = setup_logging_config(__name__, "heat.log")

try:
    MAX_RETRY_COUNT = int(os.getenv("MAX_RETRY_COUNT", "1"))
except ValueError as err:
    log.error(
        "Unable to convert MAX_RETRY_COUNT to an integer. Reverting to default...", err
    )

try:
    RETRY_SLEEP_COUNT = int(os.getenv("RETRY_SLEEP_COUNT", "5"))
except ValueError as err:
    log.error(
        "Unable to convert RETRY_SLEEP_COUNT to an integer. Reverting to default...",
        err,
    )


def update_database(update_values: List[HeatSchema], session: Session) -> bool:
    """Updates the database with the new dataset information.

    Args:
        update_values (list[LinearModel]): A list of LinearModel classes which
        contain all the necessary coefficients and matches the schema of the
        model.heat SQL table.

    Returns:
        bool: Returns a bool based on the success of the function.
    """
    for model in update_values:

        result = (
            session.query(HeatSchema).filter(HeatSchema.country == model.country).all()
        )
        result_length = len(result)

        if result_length == 0:
            session.add(model)
        else:
            log.error("This shouldn't happen.")
            continue

    log.info(
        "Successfully inserted Linear Regression Coefficients into the database..."
    )
    session.commit()
    return True


def process_dataset(dataset_path: str) -> Union[List[HeatSchema], None]:
    """Parses the dataset and extracts the countries and their average
    temperatures per date.

    Uses pandas to read the CSV for the location that was returned by watchdog
    it then checks to make sure that all the headers of the CSV match up. Then
    parses them based on date and runs them through linear regression models.

    Args:
        dataset_path (str): The path to the dataset CSV

    Returns:
        Union[list[LinearModel], None]: Returns a list of LinearModels schema
        defined in the database, if there was an error. It will return nothing.
    """

    date_column_name = None
    temp_column_name = None
    country_column_name = None

    # Read in the CSV file into pandas.
    data = pd.read_csv(dataset_path)

    # Fuzz the column headers identified by pandas, both the date and
    # average temperature are needed to be passed.
    for col in data.columns:
        if col == "Date":
            date_column_name = col
        elif col == "AverageTemperature":
            temp_column_name = col
        elif col == "Country":
            country_column_name = col
        else:
            pass

    # Format the date column as a datetime format
    data[date_column_name] = pd.to_datetime(data[date_column_name])

    # Create a new column with the name or the original with "_formatted", this
    # contains the date in a formatted string e.g. 01-01-2000 = 20000101
    # This is so that we can easily manipulate the numbers dates without having
    # to worry strongly about parsing to a datetime format later.
    date_formatted_column = f"{date_column_name}_formatted"
    data[date_formatted_column] = (
        data[date_column_name].dt.strftime("%Y%m%d").astype(int)
    )

    # If not all the required information was found, raise error and return.
    if country_column_name is None:
        log.debug("Couldn't locate the country column in the supplied dataset.")
        return

    if date_column_name is None:
        log.debug("Couldn't locate the date column in the supplied dataset.")
        return

    if temp_column_name is None:
        log.debug("Couldn't locate the temperature column in the supplied dataset.")
        return

    # Split the dataframes based on the country names
    grouped = data.groupby(data[country_column_name])

    # Iterates the dataframe by country
    linear_models = []
    for key in grouped.groups.keys():
        country_dataframe = grouped.get_group(key)

        # Iterate through the pandas group using itertuples, much faster than
        # iterrows. Additionally, remove the enumerator added by pandas. Not
        # necessary
        country_by_year = country_dataframe.groupby(
            country_dataframe[date_column_name].dt.year
        )

        pandas_data = {"min": [], "max": [], "date": []}

        for year in country_by_year.groups.keys():
            year_group = country_by_year.get_group(year)
            temperatures_per_country_per_year = year_group[temp_column_name]
            temperatures_per_country_per_year_date = year_group[date_formatted_column]

            pandas_data["max"].append(np.amax(temperatures_per_country_per_year))

            pandas_data["min"].append(np.amin(temperatures_per_country_per_year))

            pandas_data["date"].append(min(temperatures_per_country_per_year_date))

        pandas_dataframe = pd.DataFrame(data=pandas_data)

        average_linear_regression = linear_regression(
            country_dataframe[date_formatted_column],
            country_dataframe[temp_column_name],
        )

        min_linear_regression = linear_regression(
            pandas_dataframe["date"], pandas_dataframe["min"]
        )

        max_linear_regression = linear_regression(
            pandas_dataframe["date"], pandas_dataframe["max"]
        )

        linear_models.append(
            HeatSchema(
                key,
                min_linear_regression.gradient,
                min_linear_regression.offset,
                average_linear_regression.gradient,
                average_linear_regression.offset,
                max_linear_regression.gradient,
                max_linear_regression.offset,
            )
        )

    return linear_models


def generate_heat(path: str, session: Session):
    """Callback function from watchdog, called when a new file is created.

    This callback function is called when watchdog events detect that a new file
    was created in the specified directory. It will check to see if the file has
    been seen already by checking the hash of the file and checking it against
    the completed.txt file. If the file has not been seen before, it will parse.

    Args:
        event (_type_): Class of the event that was triggered.
    """
    log.debug(f"File {path} has been identified, parsing...")
    # Get the file path of the completed.txt file. Should be in the same
    # directory as the datasets.
    completed_file_path = "completed.txt"

    # Get the fie hash
    file_hash = get_hash(path)

    # Iterate through the completed file and check to see if the found hash
    # was already processed successfully.
    if hash_already_completed(completed_file_path, file_hash):
        log.debug(f"Moved {file_hash} has already been processed once...")
        return

    linear_regression_models = process_dataset(path)
    result = update_database(linear_regression_models, session)
    if not result:
        log.debug("Unable to upload dataset to database...")
        return

    # If it returned successfully write the hash to the completed file.
    if len(linear_regression_models) > 0:
        with open(completed_file_path, "a+") as complete:
            complete.write(file_hash + "\n")
        log.debug("Successfully updated completed file to include new dataset...")
