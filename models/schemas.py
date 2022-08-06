import math
import sqlalchemy

from sqlalchemy.ext.declarative import declarative_base
from maths import predict

Base = declarative_base()
CARBON_DIOXIDE_MAX_CONST = 444.7619
NITROUS_OXIDE_MAX_CONST = 555.9525
MAX_HEAT_CONST = 40


class AirSchema(Base):
    """ LinearModel contains all required information to create a prediction
    based on the dataset.

    The predictions are based on the dataset and the coefficients. Specifically
    CO2 (million tonnes) per country and NOx (10,000 tonnes) per country. This
    class can be returned and represented in string form which returns the
    country. As there are gaps in the datasets, all but the country is optional
    to initalise the class.
    """

    __tablename__ = "air"
    country = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    co2_gradient = sqlalchemy.Column(sqlalchemy.Float)
    co2_offset = sqlalchemy.Column(sqlalchemy.Float)
    no_gradient = sqlalchemy.Column(sqlalchemy.Float)
    no_offset = sqlalchemy.Column(sqlalchemy.Float)

    def __init__(self,
                 country:       str,
                 co2_gradient:  float,
                 co2_offset:    float,
                 no_gradient:   float,
                 no_offset:     float):
        self.country = country
        self.co2_gradient = co2_gradient
        self.co2_offset = co2_offset
        self.no_gradient = no_gradient
        self.no_offset = no_offset

    def __repr__(self) -> str:
        """Displays the country in a string format for debugging the class.

        Returns:
            str: String object as defined in the string below.
        """
        return f"<Air {self.country}>"

    def normalize_carbon_dioxide(self, y_axis: float):
        """Fits the carbon dioxide data to a normal distribution.

        Args:
            y_axis (float): The carbon dioxide value based on the y axis.

        Returns:
            float: The noramlized value between 0 and 1.
        """
        if y_axis < 0:
            return None  # Impossible

        if y_axis > CARBON_DIOXIDE_MAX_CONST:
            return 1

        return y_axis / (CARBON_DIOXIDE_MAX_CONST - 0)

    def normalize_nitrous_oxide(self, y_axis: float):
        """Fits the nitrious oxide data to a normal distribution.

        Args:
            y_axis (float): The nitrious oxide value based on the y axis.

        Returns:
            float: The noramlized value between 0 and 1.
        """
        if y_axis < 0:
            return None  # Impossible

        if y_axis > NITROUS_OXIDE_MAX_CONST:
            return 1

        return y_axis / (NITROUS_OXIDE_MAX_CONST - 0)

    def predict(self, user_input_date: int) -> float:
        """ Uses the coefficients to make a prediction from the input date

        Args:
            user_input_date (int): Takes in a date in the format $year$month$day

        Returns:
            dict: Returns the lowest 5% temperatures from the linear equation,
            the average temperature coefficients and top 5% temperatures.
        """
        carbon_dioxide = None
        nitrogen_oxide = None

        co2_grad_type = type(self.co2_gradient)
        no_grad_type = type(self.no_gradient)

        if co2_grad_type in (float, int) and math.isnan(self.co2_gradient) is False:
            carbon_dioxide = self.normalize_carbon_dioxide(
                predict(self.co2_gradient, self.co2_offset, user_input_date))

        if no_grad_type in (float, int) and math.isnan(self.no_gradient) is False:
            nitrogen_oxide = self.normalize_nitrous_oxide(
                predict(self.no_gradient, self.no_offset, user_input_date))

        if carbon_dioxide and nitrogen_oxide:
            return (carbon_dioxide + nitrogen_oxide) / 2

        if carbon_dioxide:
            return carbon_dioxide

        if nitrogen_oxide:
            return nitrogen_oxide

        return


class HeatSchema(Base):
    """Schema for the country coefficients in the postgres database.

    Args:
        Base (_type_): Declarative base object class
    """

    __tablename__ = "heat"

    country = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    min_gradient = sqlalchemy.Column(sqlalchemy.Float)
    min_offset = sqlalchemy.Column(sqlalchemy.Float)
    avg_gradient = sqlalchemy.Column(sqlalchemy.Float)
    avg_offset = sqlalchemy.Column(sqlalchemy.Float)
    max_gradient = sqlalchemy.Column(sqlalchemy.Float)
    max_offset = sqlalchemy.Column(sqlalchemy.Float)

    def __init__(self,
                 country:       str,
                 min_gradient:  float,
                 min_offset:    float,
                 avg_gradient:  float,
                 avg_offset:    float,
                 max_gradient:  float,
                 max_offset:    float):
        self.country = country
        self.min_gradient = min_gradient
        self.min_offset = min_offset
        self.avg_gradient = avg_gradient
        self.avg_offset = avg_offset
        self.max_gradient = max_gradient
        self.max_offset = max_offset

    def __repr__(self) -> str:
        """Displays the country in a string format for debugging the class.

        Returns:
            str: String object as defined in the string below.
        """
        return f"<Heat {self.country}>"

    def normalize(self, y_axis: float):
        """Fits the heat data to a normal distribution.

        Args:
            y_axis (float): The temperature value based on the y axis.

        Returns:
            float: The noramlized value between 0 and 1.
        """
        max_const = 40
        if y_axis < 1 or y_axis > 39:
            return 1

        return abs((math.log(max_const/y_axis - 1)) / 5 * math.log(math.e))

    def predict(self, user_input_date: int) -> float:
        """ Uses the coefficients to make a prediction from the input date

        Args:
            user_input_date (int): Takes in a date in the format $year$month$day

        Returns:
            dict: Returns the lowest 5% temperatures from the linear equation,
            the average temperature coefficients and top 5% temperatures.
        """

        return self.normalize(predict(self.avg_gradient, self.avg_offset, user_input_date))
