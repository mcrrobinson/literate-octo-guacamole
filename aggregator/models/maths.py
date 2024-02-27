from hashlib import sha1
import numpy as np

def predict(gradient:float, offset:float, new_x_value:float) -> float:
    """Returns the corresponding y value for the x value input against the
    linear equation.

    Args:
        new_x_value (float): User defined x value.

    Returns:
        float: The corresponding Y value for the input X value.
    """
    try: 
        return gradient + offset * new_x_value
    except ValueError:
        return

class LinearEquation:
    """LinearEquation class is used in all models to predict future values based

    It takes in a gradient and offset and uses it to predict future values. It
    can also return the math notation for representing the line of best fit.
    """
    
    def __init__(self, gradient:float, offset:float) -> None:
        """Initializes the LinearEquation class.

        LinearEquation is used in all models to predict future values based on
        an input x value using the equation y = mx + b.

        Args:
            gradient (float): The gradient for the linear equation.
            offset (float): The offset for th elinear equation.
        """
        self.gradient   = gradient
        self.offset     = offset
    
    def __repr__(self) -> str:
        """ Returns a string representation of the LinearEquation class.

        Returns:
            str: Returns the Linear equation represented as a string.
        """
        return f"y = {self.gradient}x + {self.offset}"
    
    def predict(self, new_x_value:float) -> float:
        """Returns the corresponding y value for the x value input against the
        linear equation.

        Args:
            new_x_value (float): User defined x value.

        Returns:
            float: The corresponding Y value for the input X value.
        """
        return self.gradient + self.offset * new_x_value

def linear_regression(x_axis:np.ndarray, y_axis:np.ndarray) -> LinearEquation:
    """Creates a linear regression equation for the list of values input.

    Args:
        x (list[float]): Defines a list of floats on the x coordinate. In our
            example, it defines the area values.
        y (list[float]): Defines a list of floats on the y coordinate. In our
            example, it defines the price values.

    Returns:
        LinearEquation: A class that holds the gradient, offset and coefficient.
    """
    x_mean = x_axis.mean()
    y_mean = y_axis.mean()

    b1_num = ((x_axis - x_mean) * (y_axis - y_mean)).sum()
    b1_den = ((x_axis - x_mean)**2).sum()

    offset = b1_num / b1_den
    gradient = y_mean - (offset*x_mean)

    return LinearEquation(gradient, offset)

def get_hash(path:str) -> str:
    """Returns the hash of a file.

    Args:
        path (str): The path to the file you're trying to get the hash of.

    Returns:
        str: The hash in string format.
    """    
    sha = sha1()

    with open(path, 'rb') as file:
        while True:
            data = file.read(65536)
            if not data:
                break
            
            sha.update(data)
    return sha.hexdigest()

def hash_already_completed(completed_file_dir:str, file_hash:str) -> bool:
    """Checks if the hash passed exists in the a file by iterating line by
    line.

    Args:
        completed_file_dir (str): The path to the directory containing the
        file hashes.

        file_hash (str): The hash for the predefined file.

    Returns:
        bool: Whether or not the hash exists in the file.
    """
    with open(completed_file_dir) as complete:
        for hash_in_file in complete:
            if hash_in_file.strip() == file_hash:
                return True
        return False
