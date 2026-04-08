INSERT INTO historical_sources (id, title, author, publication_year, url, license, verification_status) VALUES
('src-nps-gettysburg', 'Gettysburg Battle Summary', 'National Park Service', 2024, 'https://www.nps.gov/gett/learn/historyculture/battle-summary.htm', 'Public Domain', 'peer_reviewed');

INSERT INTO battles (id, name, year, start_date, end_date, center, is_verified, war_name, terrain_type, source_id) VALUES
('b-001', 'Battle of Gettysburg', 1863, '1863-07-01', '1863-07-03', ST_SetSRID(ST_MakePoint(-77.218, 39.824), 4326), TRUE, 'American Civil War', 'open_field', 'src-nps-gettysburg');

INSERT INTO armies (id, battle_id, faction, commander, initial_strength, spawn_pos, unit_composition, source_id) VALUES
('army-union-101', 'b-001', 'Union', 'George G. Meade', 93000, ST_SetSRID(ST_MakePoint(-77.23, 39.83), 4326), '[{"type":"infantry","count":75000,"weapon":"rifle_musket","speed_kmh":4},{"type":"artillery","count":350,"weapon":"field_artillery","speed_kmh":3},{"type":"cavalry","count":12000,"weapon":"repeating_rifle","speed_kmh":12}]', 'src-nps-gettysburg'),
('army-confed-102', 'b-001', 'Confederate', 'Robert E. Lee', 71000, ST_SetSRID(ST_MakePoint(-77.20, 39.81), 4326), '[{"type":"infantry","count":60000,"weapon":"rifle_musket","speed_kmh":4},{"type":"artillery","count":280,"weapon":"field_artillery","speed_kmh":3},{"type":"cavalry","count":10000,"weapon":"musket","speed_kmh":11}]', 'src-nps-gettysburg');

INSERT INTO historical_events (battle_id, event_time, event_type, description, location, outcome_summary, source_id, confidence_level) VALUES
('b-001', '1863-07-01 10:00:00-05', 'engagement', 'Confederate Heth division engages Union cavalry west of Gettysburg', ST_SetSRID(ST_MakePoint(-77.24, 39.83), 4326), 'Union cavalry falls back', 'src-nps-gettysburg', 'certain'),
('b-001', '1863-07-02 16:00:00-05', 'engagement', 'Longstreet assault on Union left at Little Round Top', ST_SetSRID(ST_MakePoint(-77.23, 39.81), 4326), 'Union holds position', 'src-nps-gettysburg', 'certain'),
('b-001', '1863-07-03 13:00:00-05', 'engagement', 'Picketts Charge: Confederate assault on Union center', ST_SetSRID(ST_MakePoint(-77.22, 39.82), 4326), 'Assault repulsed', 'src-nps-gettysburg', 'certain');