CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE battles (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(100) NOT NULL, year INT NOT NULL, start_date DATE, end_date DATE, center GEOGRAPHY(Point, 4326), is_verified BOOLEAN DEFAULT TRUE, sources JSONB DEFAULT '[]');
CREATE TABLE armies (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), battle_id UUID REFERENCES battles(id), faction VARCHAR(50) NOT NULL, commander VARCHAR(100), initial_strength INT, spawn_pos GEOGRAPHY(Point, 4326));
CREATE TABLE sim_snapshots (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, battle_id UUID REFERENCES battles(id), tick_index INT, timestamp_utc TIMESTAMPTZ DEFAULT NOW(), is_hypothetical BOOLEAN DEFAULT FALSE, state JSONB);
CREATE INDEX idx_snap_battle ON sim_snapshots(battle_id, tick_index);
CREATE TABLE users (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email VARCHAR(255) UNIQUE NOT NULL, password_hash VARCHAR(255) NOT NULL, role VARCHAR(20) CHECK (role IN ('user','researcher','admin')) DEFAULT 'user');
