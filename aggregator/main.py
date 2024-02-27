from datetime import datetime, timedelta
import shutil
from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import sqlalchemy
from sqlalchemy.orm import Session, sessionmaker
from models.env import COUNTRIES, DATABASE_URL
from models.schemas import AirSchema, HeatSchema
from models.heat import generate_heat
from models.air import generate_air
from time import sleep

try:
    engine = sqlalchemy.create_engine(DATABASE_URL)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

except Exception as err:
    print("Unable to connect databse")
    raise SystemExit(-1) from err


def get_session():
    """Gets the local database session

    Uses SQL alchemy to create a generator function which returns the session.
    Yields:
        SessionLocal: Session object
    """
    session = session_local()
    try:
        yield session
    finally:
        session.close()


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def query(session, schema, country) -> classmethod:
    """Queries the database for the input class schema and country.

    Returns:
        classmethod: Returns a class based on the input class in schema.
    """
    return session.query(schema).filter(schema.country == country).first()


def calculate_score(heat_prediction_score: dict, air_predictions: dict) -> float:
    """Calculates the overall score based on the heat and air predictions

    Takes the heat and air predictions. Then calculates the overall score by
    averaging the heat and air predictions.

    Args:
        heat_prediction_score (dict): Contains the min, avg and max heat
            scores based on what's survivable to the human body.
        air_predictions (dict): Contains the carbon dioxide and nitrous oxide
            scores based on what's healthy for the human body.

    Returns:
        float: Returns a score between 0 and 1 with 0 being the worst and 1
        being excellent.
    """

    division_counter = 0
    counter = 0

    if heat_prediction_score and type(heat_prediction_score) in (int, float):
        division_counter += 1
        counter += heat_prediction_score

    if air_predictions and type(air_predictions) in (int, float):
        division_counter += 1
        counter += air_predictions

    if division_counter == 0:
        return None

    return counter / division_counter


@app.on_event("startup")
async def startup():
    """On API startup, connect the SQL database."""
    while True:
        try:
            engine.connect()

            # Create the tables if they don't exist
            AirSchema.__table__.create(bind=engine, checkfirst=True)
            HeatSchema.__table__.create(bind=engine, checkfirst=True)

            # Make sure completed.txt exists
            with open("completed.txt", "a") as _:
                pass

            break
        except Exception as err:
            print("Connection refused, restarting...", err)
            sleep(5)


@app.on_event("shutdown")
async def shutdown():
    """On API shutdown, cleanly disconnect from the database."""
    engine.dispose()


@app.get("/score")
async def score(
    country: str = None,
    day: int = None,
    month: int = None,
    year: int = None,
    session: Session = Depends(get_session),
):
    """Returns the score for the country and date inputted.

    Args:
        country (str): Country name.
        day (int): Day of the month.
        month (int): Month of the year.
        year (int): Year.

    Returns:
        dict: Returns the lowest 5% temperatures from the linear equation,
        the average temperature coefficients and top 5% temperatures.
    """
    current_date = datetime.now()
    if day or month or year:
        if not day:
            return {"error": "The day wasn't supplied"}
        if not month:
            return {"error": "The month wasn't supplied"}
        if not year:
            return {"error": "The year wasn't supplied"}

        try:
            supplied_date = datetime(year=year, month=month, day=day)
        except ValueError:
            return {"error": "Invalid date"}

        if (supplied_date + timedelta(days=1)) < current_date:
            return {"error": "The date entered was in the past"}

        prediction_date = supplied_date.year

    else:
        prediction_date = current_date.year

    air_prediction_score = None
    heat_prediction_score = None

    if country:

        if country not in COUNTRIES:
            return {"error": "Country doesn't match schema."}

        db_air_result = (
            session.query(AirSchema).filter(AirSchema.country == country).first()
        )
        if db_air_result:
            air_prediction_score = db_air_result.predict(prediction_date)

        db_heat_result = (
            session.query(HeatSchema).filter(HeatSchema.country == country).first()
        )
        if db_heat_result:
            heat_prediction_score = db_heat_result.predict(prediction_date)

        if not db_air_result and not db_heat_result:
            return {"error": "Country doesn't exist in the dataset"}

        return calculate_score(heat_prediction_score, air_prediction_score)

    # NOT EFFICIENT. MUST BE A BETTER WAY
    country_scores = {}
    countries_from_air_table = [row.country for row in session.query(AirSchema).all()]
    countries_from_heat_table = [row.country for row in session.query(HeatSchema).all()]

    for iso3 in countries_from_air_table:
        if iso3 in countries_from_heat_table:
            db_air_result = query(session, AirSchema, iso3)
            db_heat_result = query(session, HeatSchema, iso3)

            country_scores[iso3] = calculate_score(
                db_heat_result.predict(prediction_date) if db_heat_result else None,
                db_air_result.predict(prediction_date) if db_air_result else None,
            )

        elif iso3 not in countries_from_heat_table:
            db_air_result = query(session, AirSchema, iso3)

            # Do this check here, don't want to run the function if both results are
            # null
            if not db_air_result:
                continue

            country_scores[iso3] = calculate_score(
                None, db_air_result.predict(prediction_date)
            )

    for iso3 in countries_from_heat_table:

        # We want to ignore already traversed ISOs
        if iso3 in countries_from_air_table:
            continue

        db_heat_result = query(session, HeatSchema, iso3)

        # Do this check here, don't want to run the function if both results are
        # null
        if not db_heat_result:
            continue

        country_scores[iso3] = calculate_score(
            db_heat_result.predict(prediction_date), None
        )

    return country_scores


@app.get("/air_pollution_prediction")
async def air_pollution_prediction(
    country: str = None,
    day: int = None,
    month: int = None,
    year: int = None,
    session: Session = Depends(get_session),
):
    """Returns a score from 0 to 1 for air quality for a country.

    Args:
        country (str, optional): A user can request a country input, if this is
            enabled, the function will only return that country otherwise it
            defaults to return every country.
        day (int, optional): A user can specify a specific day to predict.
            Defaults to None.
        month (int, optional): A user can specify a specific month to predict.
            Defaults to None.
        year (int, optional): A user can specify a specific year to predict.
            Defaults to None.
        session (Session, optional): Session yield to connect to the database.
            Defaults to Depends(get_session).

    Returns:
        list: An array of dictionaries containing the country name and the
            polltion score.
    """
    current_date = datetime.now()
    if day or month or year:
        if not day:
            return {"error": "The day wasn't supplied"}
        if not month:
            return {"error": "The month wasn't supplied"}
        if not year:
            return {"error": "The year wasn't supplied"}

        try:
            supplied_date = datetime(year=year, month=month, day=day)
        except ValueError:
            return {"error": "Invalid date"}

        if (supplied_date + timedelta(days=1)) < current_date:
            return {"error": "The date entered was in the past"}

        prediction_date = supplied_date.year

    else:
        prediction_date = current_date.year

    if country:
        if country not in COUNTRIES:
            return {"error": "Country doesn't match schema"}

        iso3_air_result = query(session, AirSchema, country)
        if iso3_air_result:
            return iso3_air_result.predict(prediction_date)

        # Was null, entered country didn't fit in the database.
        return {"error": "Country doesn't exist in the dataset"}

    return {
        item.country: item.predict(prediction_date)
        for item in session.query(AirSchema).all()
        if item is not None
    }


@app.get("/heat_prediction")
async def heat_prediction(
    country: str = None,
    day: int = None,
    month: int = None,
    year: int = None,
    session: Session = Depends(get_session),
):
    """Housing risk returns the current predictions on the input location and
    date

    Returns:
    {
        "countries": [
            ...
        ],
        "date": {
            'day':      ...
            'month':    ...
            'year':     ...
        }
    }
    """
    current_date = datetime.now()
    if day or month or year:
        if not day:
            return {"error": "The day wasn't supplied"}
        if not month:
            return {"error": "The month wasn't supplied"}
        if not year:
            return {"error": "The year wasn't supplied"}

        try:
            supplied_date = datetime(year=year, month=month, day=day)
        except ValueError:
            return {"error": "Invalid date"}

        if (supplied_date + timedelta(days=1)) < current_date:
            return {"error": "The date entered was in the past"}

        prediction_date = supplied_date.year

    else:
        prediction_date = current_date.year

    if country:
        if country not in COUNTRIES:
            return {"error": "Country doesn't match schema."}

        iso3_heat_result = (
            session.query(HeatSchema).filter(HeatSchema.country == country).first()
        )
        if iso3_heat_result:
            return iso3_heat_result.predict(prediction_date)

        # The entered country may have been in the country list but not in the
        # database yet.
        return {"error": "Country doesn't exist in the dataset"}

    return {
        item.country: item.predict(prediction_date)
        for item in session.query(HeatSchema).all()
        if item is not None
    }


@app.get("/upl/air")
async def main():
    content = """
<body>
<form action="/upl/air/file" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.get("/upl/heat")
async def main():
    content = """
<body>
<form action="/upl/heat/file" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.post("/upl/air/file")
async def create_upload_file(
    file: UploadFile = File(...), session: Session = Depends(get_session)
):
    # You can now save the file, process it, etc. For example, you can save it to disk with:
    with open(file.filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    generate_air(file.filename, session)
    # Return a message or any information you want
    return {"filename": file.filename}


@app.post("/upl/heat/file")
async def create_upload_file(
    file: UploadFile = File(...), session: Session = Depends(get_session)
):
    # You can now save the file, process it, etc. For example, you can save it to disk with:
    with open(file.filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    generate_heat(file.filename, session)
    # Return a message or any information you want
    return {"filename": file.filename}
