import numpy as np
from models.maths import predict, LinearEquation, linear_regression, get_hash, \
    hash_already_completed

def test_predict():
    """ Tests the predict function """
    
    results = predict(gradient=3, offset=5, new_x_value=2)
    if results != 13:
        assert False

def test_linear_equation():
    """Tests the LinearEquation class, which stores the gradient and offset.
    
    To initalise the class, you enter a gradient and offset. It will draw a
    linear equation and plot the input x value from the predict function on the
    graph and return the correspending y value.
    """
    
    linear_equation_test = LinearEquation(5, 2)
        
    if not linear_equation_test.predict(5) == 15:
        assert False

def test_linear_regression():
    """ The linear regression function takes in two numpy arrays and returns the
    LinearEquation class containing the gradient and offset.
    """
    
    np_arr_1 = np.array([1,2,3,4,5,6,7,8])
    np_arr_2 = np.array([3,4,5,6,7,8,9,10])
    linear_regression_test = linear_regression(np_arr_1, np_arr_2)
    if not isinstance(linear_regression_test, LinearEquation):
        assert False

    if not linear_regression_test.gradient == 2.0:
        assert False
        
    if not linear_regression_test.offset == 1.0:
        assert False
        
    if not linear_regression_test.predict(5) == 7.0:
        assert False

def test_get_hash():
    """Gets the SHA1 hash of a file."""
    
    # setup
    with open('sample_hash_file.txt', 'w') as file:
        file.write("""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eu tellus quam.
Cras volutpat, est non vestibulum viverra, neque erat lacinia purus, ut cursus
nulla velit sit amet eros. Aenean iaculis mi nec rutrum fermentum. Donec auctor
vestibulum leo et gravida. Morbi accumsan pharetra vehicula. Proin nec laoreet
ex. Phasellus finibus metus maximus orci efficitur feugiat. Duis eget
pellentesque elit. Nam dictum luctus tincidunt. Maecenas vel urna et enim
rhoncus vulputate. Cras accumsan magna ullamcorper varius ultricies. In mollis
massa et urna eleifend suscipit. Praesent et lacus ac mi feugiat finibus. In
ut ultricies lectus. Mauris sit amet pharetra ante. Nam sit amet arcu elit.""")
        
    result = get_hash('sample_hash_file.txt')
    if result != 'd02ccdc8d76ef50dc50972727f19d47f5702fa96':
        print(result)
        assert False

def test_hash_already_completed():
    """Checks a completed file to see if the entered hash exists, if it does
    the function will return true.
    """
    
    with open('completed.txt', 'w') as file:
        file.write('d02ccdc8d76ef50dc50972727f19d47f5702fa96\n')
     
    result = hash_already_completed('completed.txt', 'd02ccdc8d76ef50dc50972727f19d47f5702fa96')
    if not result:
        assert False
        
    result = hash_already_completed('completed.txt', '9a8beadca09d671bc9eab5cc037825521e95fce3')
    if result:
        assert False
