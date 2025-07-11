import sqlite3

# SQL script to create all tables
sql_script = """
-- User Table
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    username CHAR(50) NOT NULL,
    email TEXT NOT NULL,
    hash_password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    profile TEXT,
    profile_pic_url TEXT,
    age INTEGER,
    pronouns TEXT,
    verified_email TEXT,
    edu_verification_email TEXT,  --"should be it's email if verified"
    work_verification_email TEXT 
);
-- 1. Create the connections table
CREATE TABLE IF NOT EXISTS User_Connections (
  user_a       INTEGER   NOT NULL,     -- smaller user_id
  user_b       INTEGER   NOT NULL,     -- larger  user_id
  connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_a, user_b),
  FOREIGN KEY (user_a) REFERENCES Users(user_id)   ON DELETE CASCADE,
  FOREIGN KEY (user_b) REFERENCES Users(user_id)   ON DELETE CASCADE,
  CHECK (user_a < user_b)
);

-- Event tag tables, shares the same categories as use skills
CREATE TABLE IF NOT EXISTS Event_Tags (
    event_id INTEGER NOT NULL,
    category INTEGER NOT NULL,
    PRIMARY KEY (event_id, category),
    FOREIGN KEY (event_id) REFERENCES Events(event_id)
);

-- User Skills Table (each skill is represented by an integer category code)
CREATE TABLE IF NOT EXISTS User_Skills (
    user_id INTEGER NOT NULL,
    skill_category INTEGER NOT NULL,
    PRIMARY KEY (user_id, skill_category),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
-- User socials Table, with link
CREATE TABLE IF NOT EXISTS User_Socials (
    user_id INTEGER NOT NULL,
    link TEXT NOT NULL,
    PRIMARY KEY (user_id, link),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
-- Enhanced Events Table with end_time
CREATE TABLE IF NOT EXISTS Events (
    event_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,  -- New column to store computed end time
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    organizer TEXT,
    organization_name TEXT,
    event_link TEXT,
    location TEXT,
    certificate INTEGER DEFAULT 0,
    requirements TEXT,
    contact_methods TEXT,
    instructions TEXT,
    max_participants INTEGER,
    is_draft INTEGER DEFAULT 1,
    duration INTEGER,  -- Duration in minutes
    status INTEGER DEFAULT 1  -- 0: ended/unavailable, 1: upcoming/active
);
CREATE TABLE IF NOT EXISTS User_XP (
  xp_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL,
  amount       INTEGER NOT NULL,           -- positive (gain) or negative (loss)
  reason       TEXT,                       -- e.g. 'attended_event', 'gave_feedback'
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);
-- Event_Images Table: Multiple Images per Event
CREATE TABLE IF NOT EXISTS Event_Images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    image_url TEXT NOT NULL, -- Secure URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES Events(event_id)
);

-- Event_Users Table to map users to events with a role field
CREATE TABLE IF NOT EXISTS Event_Users (
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    role TEXT DEFAULT 'participant',   -- roles can be participant, host, co-host, saved, etc.
    volunteer_state TEXT DEFAULT 'registered',  -- Additional state: registered, waitlisted, saved, etc.
    checked_in INTEGER DEFAULT 0,               -- 0: not checked in, 1: checked in
    waitlist_position INTEGER DEFAULT NULL, 
    PRIMARY KEY (user_id, event_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
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
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
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
