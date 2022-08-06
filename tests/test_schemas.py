import math
from sys import maxsize
from models.schemas import predict, AirSchema, HeatSchema, \
    CARBON_DIOXIDE_MAX_CONST, NITROUS_OXIDE_MAX_CONST

def test_predict():
    """Testing the predict function"""
        
    result = predict(gradient=3,offset=5,new_x_value=2)
    if result != 13:
        assert False
        
    result = predict(gradient=3,offset=5,new_x_value=0)
    if result != 3:
        assert False
        
    result = predict(gradient=3,offset=5,new_x_value=-50)
    if result != -247:
        assert False
        
    result = predict(gradient=3,offset=5,new_x_value=maxsize)
    if result != 46116860184273879038:
        assert False
        
    assert True
        
def test_airschema():
    """ Testing the AirSchema class """
    
    country = 'CN'
    min_gradient = 0.1
    min_offset = 0.1
    avg_gradient = 0.2
    avg_offset = 0.2
    max_gradient = 0.3
    max_offset = 0.3
    
    result = HeatSchema(
        country,
        min_gradient,
        min_offset,
        avg_gradient,
        avg_offset,
        max_gradient,
        max_offset)
    
    if result.normalize(-10) != 1:
        assert False
        
    # Over the const value.
    prediction = result.predict(2022)
    
    expected_average_value =  1
    if not math.isclose(prediction, expected_average_value, rel_tol=1e-5): 
        assert False
    
    assert True
    
def test_heatschema():
    """ Test the HeatSchema class """
    
    country = "CN"
    co2_gradient = 3
    co2_offset = 5
    no_gradient = 2
    no_offset = 3
    
    co2_normalize_value = 1
    no_normalize_value = 1
    result = AirSchema(country,co2_gradient,co2_offset,no_gradient,no_offset)
    
    co2_expected_value = 0.0022483940283553965
    # Enter a possible value, use the math.isclose function because comparing
    # floating point numbers is often a bit of a pain.
    if not math.isclose(result.normalize_carbon_dioxide(co2_normalize_value), 
                        co2_expected_value, 
                        rel_tol=1e-5):
        assert False
    
    # -1 can't exist, it should handle it by returning None instead of erroring.
    if result.normalize_carbon_dioxide(-1) is not None:
        assert False
    
    # Over the const value.
    if result.normalize_carbon_dioxide(CARBON_DIOXIDE_MAX_CONST + 1) != 1:
        assert False
    
    no_expected_value = 0.0017987148182623516
    # Enter a possible value, use the math.isclose function because comparing
    # floating point numbers is often a bit of a pain.
    if not math.isclose(result.normalize_nitrous_oxide(no_normalize_value), 
                        no_expected_value, 
                        rel_tol=1e-5):
        print(result.normalize_nitrous_oxide(no_normalize_value))
        assert False
        
    # -1 can't exist, it should handle it by returning None instead of erroring.
    if result.normalize_nitrous_oxide(-1) is not None:
        assert False

    # Over the const value.
    if result.normalize_nitrous_oxide(NITROUS_OXIDE_MAX_CONST + 1) != 1:
        assert False
        
    # Over the const value.
    prediction = result.predict(1)
    if prediction is None:
        assert False
    
    expected_value = 0.013490363159077465
    if not math.isclose(prediction, expected_value, rel_tol=1e-5): 
        assert False
    
    assert True
