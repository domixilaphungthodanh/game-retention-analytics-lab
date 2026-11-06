PRAGMA foreign_keys=ON;
CREATE TABLE players(player_id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE CHECK(length(trim(name))>0));
CREATE TABLE levels(level_id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,level_order INTEGER NOT NULL UNIQUE CHECK(level_order>0));
CREATE TABLE sessions(session_id INTEGER PRIMARY KEY,player_id INTEGER NOT NULL REFERENCES players,
    started_at TEXT NOT NULL,ended_at TEXT NOT NULL,CHECK(ended_at>started_at));
CREATE INDEX sessions_player_time ON sessions(player_id,started_at);
CREATE TABLE level_attempts(attempt_id INTEGER PRIMARY KEY,session_id INTEGER NOT NULL REFERENCES sessions,
    level_id INTEGER NOT NULL REFERENCES levels,started_at TEXT NOT NULL,ended_at TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN('completed','failed')),CHECK(ended_at>started_at));
CREATE INDEX attempts_session_time ON level_attempts(session_id,started_at);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
