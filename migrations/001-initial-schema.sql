-- Up

CREATE TABLE IF NOT EXISTS Messages (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL,
  msg TEXT NOT NULL,
  time DATETIME
);

-- Down

DROP TABLE Messages;
