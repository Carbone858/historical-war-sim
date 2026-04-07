INSERT INTO battles (id, name, year, start_date, end_date, center, sources) VALUES
('b-001', 'Gettysburg', 1863, '1863-07-01', '1863-07-03', ST_SetSRID(ST_MakePoint(-77.218, 39.824), 4326), '["NPS"]'),
('b-002', 'Waterloo', 1815, '1815-06-18', '1815-06-18', ST_SetSRID(ST_MakePoint(4.41, 50.68), 4326), '["Wellington"]'),
('b-003', 'Stalingrad Assault', 1942, '1942-08-23', '1942-09-13', ST_SetSRID(ST_MakePoint(44.53, 48.71), 4326), '["Glantz"]');
INSERT INTO armies (id, battle_id, faction, commander, initial_strength, spawn_pos) VALUES
('u-101','b-001','Union','Meade',93000, ST_SetSRID(ST_MakePoint(-77.23, 39.83),4326)),
('c-102','b-001','Confederate','Lee',71000, ST_SetSRID(ST_MakePoint(-77.20, 39.81),4326));
