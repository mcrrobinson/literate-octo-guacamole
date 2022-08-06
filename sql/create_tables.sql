-- Create database
CREATE DATABASE models;

\c models;

-- Create the heat table.
CREATE TABLE IF NOT EXISTS heat(
    country CHAR(2), 
    min_gradient FLOAT, 
    min_offset FLOAT, 
    avg_gradient FLOAT, 
    avg_offset FLOAT, 
    max_gradient FLOAT, 
    max_offset FLOAT
);

-- Create the air table.
CREATE TABLE IF NOT EXISTS air(
    country CHAR(2),
    co2_gradient FLOAT,
    co2_offset FLOAT,
    no_gradient FLOAT,
    no_offset FLOAT
);