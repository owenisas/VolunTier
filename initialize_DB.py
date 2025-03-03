import sqlite3

# SQL script to create all tables
sql_script = """
-- User Table
CREATE TABLE IF NOT EXISTS User (
    user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    username CHAR(50) NOT NULL,
    email TEXT NOT NULL,
    hash_password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    profile TEXT,
    age INTEGER,
    verification INTEGER DEFAULT 0 -- 0: not verified, 1: school, 2: work, etc.
);

-- User Interests Table (each interest is represented by an integer category code)
CREATE TABLE IF NOT EXISTS User_Interests (
    user_id INTEGER NOT NULL,
    interest_category INTEGER NOT NULL,
    PRIMARY KEY (user_id, interest_category),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- User Skills Table (each skill is represented by an integer category code)
CREATE TABLE IF NOT EXISTS User_Skills (
    user_id INTEGER NOT NULL,
    skill_category INTEGER NOT NULL,
    PRIMARY KEY (user_id, skill_category),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- Enhanced Events Table
CREATE TABLE IF NOT EXISTS Events (
    event_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    time TIMESTAMP NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    picture TEXT,                      -- URL or path to an event image
    organizer TEXT,                    -- Organizer name (could be extended to a user reference)
    organization_name TEXT,            -- Optional organization name
    event_link TEXT,                   -- Link for more details or social/website link
    location TEXT,                     -- Event location/address or online meeting link
    certificate INTEGER DEFAULT 0,     -- 0: no, 1: yes (indicates if certificate is provided)
    requirements TEXT,                 -- Event requirements (e.g., volunteer proof, age, skills, etc.)
    contact_methods TEXT,              -- How to contact the organizer
    instructions TEXT,                 -- Additional instructions for the event
    max_participants INTEGER,          -- Maximum number of participants
    duration INTEGER,  -- Duration in minutes
    status INTEGER DEFAULT 1  -- 0: unavailable/ended, 1: upcoming/active
);

-- Event_Users Table to map users to events with a role field
CREATE TABLE IF NOT EXISTS Event_Users (
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    role TEXT DEFAULT 'participant',   -- roles can be participant, host, co-host, saved, etc.
    PRIMARY KEY (user_id, event_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

-- Feedback Table for past events (ratings, comments, and volunteer hours)
CREATE TABLE IF NOT EXISTS Feedback (
    feedback_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER,                    -- e.g., rating on a scale of 1-5
    comment TEXT,
    hours INTEGER,                     -- Total volunteer hours
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- Announcements Table for event-related messages
CREATE TABLE IF NOT EXISTS Announcements (
    announcement_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);
"""


def initialize_database(db_path='app_database.db'):
    # Connect to (or create) the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute the SQL script to create all tables
    cursor.executescript(sql_script)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print(f"Database initialized successfully at '{db_path}'")


if __name__ == "__main__":
    initialize_database()
