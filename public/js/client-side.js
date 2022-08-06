import { countries } from "/js/countries.js";

var today = new Date();
var dd = String(today.getDate()).padStart(2, "0");
var mm = String(today.getMonth() + 1).padStart(2, "0"); //January is 0!
var yyyy = today.getFullYear();

var dateInput = document.createElement("INPUT");
var dateDiv = document.getElementById("dateDiv");
dateInput.setAttribute("type", "date");
dateInput.setAttribute("min", yyyy + "-" + mm + "-" + dd);
dateInput.value = yyyy + "-" + mm + "-" + dd;
dateDiv.appendChild(dateInput);

// TODO: This is a temporary solution, either pass as array like to frontend
// or when the total score is ready uncomment the below code.
function map_to_2d_array(original) {
  var multiArray = [];
  for (var key in original) {
    multiArray.push([key, original[key]]);
  }
  return multiArray;
}

function drawRegionsMap(countries_and_values, focus_country) {
  var data;

  if (focus_country === "world") {
    console.log("Mapping dictionary to 2d array...");
    data = google.visualization.arrayToDataTable(
      [["Country", "Score"]].concat(map_to_2d_array(countries_and_values))
    );
  } else {
    console.log("Drawing region country...", focus_country);
    data = google.visualization.arrayToDataTable([
      ["Country", "Score"],
      [focus_country, countries_and_values],
    ]);
  }

  var options = {
    sizeAxis: {
      minValue: 0,
      maxValue: 1,
    },
    region: focus_country,
    colorAxis: {
      minValue: 0,
      maxValue: 1,
      colors: ["green", "red"],
    },
  };

  var chart = new google.visualization.GeoChart(
    document.getElementById("regions_div")
  );
  chart.draw(data, options);
}

var submit_button = document.getElementById("country_submit_button");
submit_button.addEventListener("click", function () {
  var getSelectedValue = document.querySelector(
    'input[name="display"]:checked'
  );

  var country_request = document.getElementById("myInput").value;
  if (!(country_request in countries)) {
    displayErrorModal("Error, please type proper country name...");
    return;
  }

  var countryCodeLocation = countries[country_request];

  var dateObject = dateInput.valueAsDate;
  var month = dateObject.getUTCMonth() + 1; //months from 1-12
  var day = dateObject.getUTCDate();
  var year = dateObject.getUTCFullYear();

  fetch("/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      locationSearch: country_request,
      inputDate: dateObject.toISOString().slice(0, 19).replace("T", " "),
    }),
  })
    .then((res) => {
      return res.json();
    })
    .then((data) => console.log(data));

  if (getSelectedValue.value == "heat") {
    fetch(
      "/heat_prediction?year=" +
        year +
        "&month=" +
        month +
        "&day=" +
        day +
        "&country=" +
        countryCodeLocation
    ).then((response) => {
      response.json().then((data) => {
        if (data.error) {
          displayErrorModal(data.error);
        } else {
          if (country_request === "World") {
            console.log("Drawing entire map...", country_request);
            drawRegionsMap(data, "world");
          } else {
            console.log("Drawing region of map...", country_request);
            drawRegionsMap(data, countryCodeLocation);
          }
        }
      });
    });
  } else if (getSelectedValue.value == "air") {
    fetch(
      "/air_pollution_prediction?year=" +
        year +
        "&month=" +
        month +
        "&day=" +
        day +
        "&country=" +
        countryCodeLocation
    ).then((response) => {
      response.json().then((data) => {
        if (data.error) {
          displayErrorModal(data.error);
        } else {
          if (country_request === "World") {
            console.log("Drawing entire map...", country_request);
            drawRegionsMap(data, "world");
          } else {
            console.log("Drawing region of map...", country_request);
            drawRegionsMap(data, countryCodeLocation);
          }
        }
      });
    });
  } else if (getSelectedValue.value == "score") {
    fetch(
      "/score?year=" +
        year +
        "&month=" +
        month +
        "&day=" +
        day +
        "&country=" +
        countryCodeLocation
    ).then((response) => {
      response.json().then((data) => {
        if (data.error) {
          displayErrorModal(data.error);
        } else {
          if (country_request === "World") {
            console.log("Drawing entire map...", country_request);
            drawRegionsMap(data, "world");
          } else {
            console.log("Drawing region of map...", country_request);
            drawRegionsMap(data, countryCodeLocation);
          }
        }
      });
    });
  } else {
    displayErrorModal("Selected value was incorrect, this shouldn't happen...");
  }
});

function regions_map_wrapper() {
  drawRegionsMap(0, "world");
}

google.charts.load("current", {
  packages: ["geochart"],
});
google.charts.setOnLoadCallback(regions_map_wrapper);

// TODO: Make changes once the score is implemented.
