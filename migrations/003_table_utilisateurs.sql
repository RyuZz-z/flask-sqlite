-- Exercice 8 (défi) : les comptes sont rangés en base, avec un mot de passe HACHÉ
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    mot_de_passe_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user'))
);

-- Comptes de démonstration : admin / password et user / 12345
INSERT OR IGNORE INTO utilisateurs (login, mot_de_passe_hash, role) VALUES
    ('admin', 'pbkdf2:sha256:260000$CqGkYU0ARt4cTWNL$638d7e5fbada1746cb314d3900c0bec604502755571eef1ead0c297aec230509', 'admin'),
    ('user',  'pbkdf2:sha256:260000$sbImOUuAfxWP5Q2N$11c211dceead6c8cab53f68fdafb1b4e4da171a986f7617ee95383a586afa1d4', 'user');
