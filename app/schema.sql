CREATE TABLE IF NOT EXISTS incidents (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    title                      TEXT    NOT NULL,
    description                TEXT    NOT NULL,
    location                   TEXT    NOT NULL,
    incident_date              TEXT    NOT NULL,
    created_at                 TEXT    NOT NULL,
    category                   TEXT    NOT NULL,
    priority                   TEXT    NOT NULL,
    classification_explanation TEXT    NOT NULL
);
