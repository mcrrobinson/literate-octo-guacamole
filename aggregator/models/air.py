from typing import Union
import pandas as pd
import os
from models.logger import setup_logging_config
from models.maths import linear_regression, get_hash, hash_already_completed
from models.schemas import AirSchema
from sqlalchemy.orm import Session

log = setup_logging_config(__name__, "air.log")

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


def update_database(update_values: list[AirSchema], session: Session) -> bool:
    """Updates the database with the new dataset information.

    Args:
        update_values (list[LinearModel]): A list of LinearModel classes which
        contain all the necessary coefficients and matches the schema of the
        model.air SQL table.

    Returns:
        bool: Returns a bool based on the success of the function.
    """
    for model in update_values:

        result = (
            session.query(AirSchema).filter(AirSchema.country == model.country).all()
        )
        result_length = len(result)

        if result_length == 0:
            if model.co2_gradient and model.no_gradient:
                session.add(model)
            elif model.co2_gradient and not model.no_gradient:
                new_record = AirSchema(
                    country=model.country,
                    co2_gradient=model.co2_gradient,
                    co2_offset=model.co2_offset,
                )
                session.add(new_record)
            elif model.no_gradient and not model.co2_gradient:
                new_record = AirSchema(
                    country=model.country,
                    no_gradient=model.no_gradient,
                    no_offset=model.no_offset,
                )
                session.add(new_record)
            else:
                log.error("Don't have either product... this shouldn't happen...")

        elif result_length == 1:
            existing_record = result[0]
            if model.co2_gradient and not model.no_gradient:
                existing_record.co2_gradient = model.co2_gradient
                existing_record.co2_offset = model.co2_offset
            elif model.no_gradient and not model.co2_gradient:
                existing_record.no_gradient = model.no_gradient
                existing_record.no_offset = model.no_offset
            elif model.co2_gradient and model.no_gradient:
                existing_record.co2_gradient = model.co2_gradient
                existing_record.co2_offset = model.co2_offset
                existing_record.no_gradient = model.no_gradient
                existing_record.no_offset = model.no_offset
            else:
                log.error("Don't have either product... this shouldn't happen...")
        else:
            log.error("This shouldn't happen.")
            continue

    log.info(
        "Successfully inserted Linear Regression Coefficients into the database..."
    )
    session.commit()
    return True


def process_dataset(dataset_path: str) -> Union[list[AirSchema], None]:
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
    carbon_dioxide_levels = None
    nitrogen_oxide_levels = None
    country_column_name = None

    # Read in the CSV file into pandas.
    data = pd.read_csv(dataset_path)

    # Fuzz the column headers identified by pandas, both the date and
    # average temperature are needed to be passed.
    for col in data.columns:
        if col == "year":
            date_column_name = col
        elif col == "co2":
            carbon_dioxide_levels = col
        elif col == "nitrous_oxide":
            nitrogen_oxide_levels = col
        elif col == "country":
            country_column_name = col
        else:
            pass

    # If not all the required information was found, raise error and return.
    if country_column_name is None:
        log.error("Couldn't locate the country column in the supplied dataset.")
        return

    if date_column_name is None:
        log.error("Couldn't locate the date column in the supplied dataset.")
        return

    if nitrogen_oxide_levels is None and carbon_dioxide_levels is None:
        log.error(
            "Couldn't locate either the carbon dioxide levels, or the nitrogen levels."
        )
        return

    # Split the dataframes based on the country names
    grouped = data.groupby(data[country_column_name])

    nitrogen_linear_regression = None
    carbon_linear_regression = None

    # Iterates the dataframe by country
    linear_models = []
    for key in grouped.groups.keys():
        country_dataframe = grouped.get_group(key)

        # Iterate through the pandas group using itertuples, much faster than
        # iterrows. Additionally, remove the enumerator added by pandas. Not
        # necessary.
        if nitrogen_oxide_levels and carbon_dioxide_levels:
            nitrogen_linear_regression = linear_regression(
                country_dataframe[date_column_name],
                country_dataframe[nitrogen_oxide_levels],
            )

            carbon_linear_regression = linear_regression(
                country_dataframe[date_column_name],
                country_dataframe[carbon_dioxide_levels],
            )

            linear_models.append(
                AirSchema(
                    key,
                    carbon_linear_regression.gradient,
                    carbon_linear_regression.offset,
                    nitrogen_linear_regression.gradient,
                    nitrogen_linear_regression.offset,
                )
            )

        elif nitrogen_oxide_levels and not carbon_dioxide_levels:
            nitrogen_linear_regression = linear_regression(
                country_dataframe[date_column_name],
                country_dataframe[nitrogen_oxide_levels],
            )

            linear_models.append(
                AirSchema(
                    key,
                    None,
                    None,
                    nitrogen_linear_regression.gradient,
                    nitrogen_linear_regression.offset,
                )
            )

        elif carbon_dioxide_levels and not nitrogen_oxide_levels:
            carbon_linear_regression = linear_regression(
                country_dataframe[date_column_name],
                country_dataframe[carbon_dioxide_levels],
            )

            linear_models.append(
                AirSchema(
                    key,
                    carbon_linear_regression.gradient,
                    carbon_linear_regression.offset,
                    None,
                    None,
                )
            )

        else:
            log.error("Neither carbon nor nitrogen found, this shouldn't happen...")
            return

    return linear_models


def generate_air(file: str, session: Session) -> None:
    """Callback function from watchdog, called when a new file is created.

    This callback function is called when watchdog events detect that a new file
    was created in the specified directory. It will check to see if the file has
    been seen already by checking the hash of the file and checking it against
    the completed.txt file. If the file has not been seen before, it will parse.

    Args:
        event (_type_): Class of the event that was triggered.
    """
    log.debug(f"File {file} has been identified, parsing...")
    # Get the file path of the completed.txt file. Should be in the same
    # directory as the datasets.
    completed_file_path = "completed.txt"

    # Get the fie hash
    file_hash = get_hash(file)

    # Iterate through the completed file and check to see if the found hash
    # was already processed successfully.
    if hash_already_completed(completed_file_path, file_hash):
        log.warning(f"Moved {file_hash} has already been processed once...")
        return

    linear_regression_models = process_dataset(file)
    if not linear_regression_models:
        log.error("No linear regression models were found.")
        return

    result = update_database(linear_regression_models, session)
    if not result:
        log.error("Unable to upload dataset to database...")
        return

    # If it returned successfully write the hash to the completed file.
    if len(linear_regression_models) > 0:
        with open(completed_file_path, "a+") as complete:
            complete.write(file_hash + "\n")
        log.info("Successfully updated completed file to include new dataset...")
