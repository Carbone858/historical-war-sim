CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE historical_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    author TEXT,
    publication_year INT,
    url TEXT,
    license TEXT,
    verification_status TEXT CHECK (verification_status IN ('peer_reviewed','primary_source','secondary_source','unverified'))
);

CREATE TABLE battles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    year INT NOT NULL,
    start_date DATE,
    end_date DATE,
    center GEOGRAPHY(Point, 4326),
    is_verified BOOLEAN DEFAULT FALSE,
    war_name TEXT,
    terrain_type TEXT,
    source_id UUID REFERENCES historical_sources(id)
);

CREATE TABLE armies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    battle_id UUID REFERENCES battles(id),
    faction TEXT NOT NULL,
    commander TEXT,
    initial_strength INT,
    spawn_pos GEOGRAPHY(Point, 4326),
    unit_composition JSONB,
    source_id UUID REFERENCES historical_sources(id)
);

CREATE TABLE historical_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    battle_id UUID REFERENCES battles(id),
    event_time TIMESTAMPTZ,
    event_type TEXT,
    description TEXT,
    location GEOGRAPHY(Point, 4326),
    outcome_summary TEXT,
    source_id UUID REFERENCES historical_sources(id),
    confidence_level TEXT CHECK (confidence_level IN ('certain','probable','possible'))
);

CREATE TABLE sim_snapshots (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    battle_id UUID REFERENCES battles(id),
    tick_index INT,
    timestamp_utc TIMESTAMPTZ DEFAULT NOW(),
    is_hypothetical BOOLEAN DEFAULT FALSE,
    state JSONB
);

CREATE INDEX idx_battles_center ON battles USING GIST (center);
CREATE INDEX idx_events_time ON historical_events(event_time);