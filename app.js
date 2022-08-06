import {
  fileURLToPath
} from "url";
import path from "path";
import {
  dirname
} from "path";
import express from "express";
import hbs from "hbs";
import sqlite3 from "sqlite3";
import {
  open
} from "sqlite";
import * as http from "http";
import {
  countries
} from "./public/js/countries.js";
import {
  createRequire
} from "module";
const require = createRequire(
  import.meta.url);
import dotenv from "dotenv";
dotenv.config();

const dbPromise = open({
  filename: "data.db",
  driver: sqlite3.Database,
});

const app = express();

app.use(express.urlencoded({
  extended: true
}))
app.use(express.json())

//Define paths for Express configuration
const __filename = fileURLToPath(
  import.meta.url);
const __dirname = dirname(__filename);
const publicDirectoryPath = path.join(__dirname, "public");
const viewsPath = path.join(__dirname, "templates/views");
const partialsPath = path.join(__dirname, "templates/partials");

// Setup handlebars engine and views location
app.set("view engine", "hbs");
app.set("views", viewsPath);
hbs.registerPartials(partialsPath);

// Setup static directory to serve
app.use(express.static(publicDirectoryPath));


app.get("/", (req, res) => {
  res.render("index", {
    title: "Live Long App",
    name: "TEAM 31 SETAP",
  });
});

app.post("/messages", async (req, res) => {
  const db = await dbPromise;
  const messageText = req.body.locationSearch;
  const inputTime = req.body.inputDate;
  if (messageText === null || messageText === undefined) {
    return res.json({
      error: "Cannot input null for country"
    });
  }
  res.json({
    message: "Success!"
  });
});

app.get("/countries", async (req, res) => {
  const messageText = req.query.country.toUpperCase();
  var return_results = [];
  Object.keys(countries).forEach((element) => {
    if (element.toUpperCase().includes(messageText)) {
      return_results.push(element);
    }
  });
  res.json(return_results);
});

app.get("/heat_prediction", async (req, res) => {
  if (!req.query.hasOwnProperty("country")) {
    return res.json({
      error: "country was undefined"
    });
  }

  http.get('http://aggregator:8000/heat_prediction?year=' + req.query.year + '&month=' + req.query.month + '&day=' + req.query.day + '&country=' + req.query.country, (resp) => {
    let data = '';

    // A chunk of data has been received.
    resp.on("data", (chunk) => {
      data += chunk;
    });

    // The whole response has been received. Print out the result.
    resp.on("end", () => {
      res.json(JSON.parse(data));
    });
  });
});

app.get("/air_pollution_prediction", async (req, res) => {
  if (!req.query.hasOwnProperty("country")) {
    return res.json({
      error: "country was undefined"
    });
  }

  http.get('http://aggregator:8000/air_pollution_prediction?year=' + req.query.year + '&month=' + req.query.month + '&day=' + req.query.day + '&country=' + req.query.country, (resp) => {
    let data = '';

    // A chunk of data has been received.
    resp.on('data', (chunk) => {
      data += chunk;
    });

    // The whole response has been received. Print out the result.
    resp.on('end', () => {
      res.json(JSON.parse(data));
    });
  });
});

app.get("/about", (req, res) => {
  res.render("about", {
    title: "About Us",
    name: "TEAM 31 SETAP",
  });
});

app.get("/score", async (req, res) => {
  if (!req.query.hasOwnProperty("country")) {
    res.json({
      error: "country was undefined"
    });
  }

  http.get('http://aggregator:8000/score?year=' + req.query.year + '&month=' + req.query.month + '&day=' + req.query.day + '&country=' + req.query.country, (resp) => {
    let data = '';

    // A chunk of data has been received.
    resp.on("data", (chunk) => {
      data += chunk;
    });

    // The whole response has been received. Print out the result.
    resp.on("end", () => {
      res.json(JSON.parse(data));
    });
  });
});

app.get("/help/*", (req, res) => {
  res.render("404", {
    title: "404",
    name: "TEAM 31 SETAP",
    errorMessage: "Help article not found.",
  });
});

app.get("*", (req, res) => {
  res.render("404", {
    title: "404",
    name: "TEAM 31 SETAP",
    errorMessage: "Page not found.",
  });
});

const setup = async () => {
  const db = await dbPromise;
  await db.migrate();
  app.listen("3000", () => {
    console.log("Server is up on port 3000.");
  });
};

setup();