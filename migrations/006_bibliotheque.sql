-- Projet bibliothèque (exercice 10) : les livres et les emprunts
CREATE TABLE IF NOT EXISTS livres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    isbn TEXT,
    annee INTEGER,
    genre TEXT,
    nb_exemplaires INTEGER NOT NULL DEFAULT 1 CHECK (nb_exemplaires >= 0)
);

-- Un emprunt relie un livre et un utilisateur.
-- Il est "en cours" tant que date_retour est NULL.
CREATE TABLE IF NOT EXISTS emprunts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livre_id INTEGER NOT NULL,
    utilisateur_id INTEGER NOT NULL,
    date_emprunt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_retour_prevue DATE NOT NULL,
    date_retour TIMESTAMP,
    FOREIGN KEY (livre_id) REFERENCES livres (id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs (id)
);

-- Noms des comptes de démonstration, et un deuxième lecteur : lea / 12345
UPDATE utilisateurs SET nom = 'ADMIN', prenom = 'Bibliothécaire' WHERE login = 'admin' AND nom IS NULL;
UPDATE utilisateurs SET nom = 'MARTIN', prenom = 'Hugo' WHERE login = 'user' AND nom IS NULL;
INSERT OR IGNORE INTO utilisateurs (login, nom, prenom, mot_de_passe_hash, role) VALUES
    ('lea', 'BERNARD', 'Léa', 'pbkdf2:sha256:260000$koowh8qn2e2GkN6L$75299b292f97bb2b035d19a84efba7fa64488f1024ad9c3c15146027219b0ba5', 'user');

-- Livres d'exemple, seulement si le catalogue est vide
CREATE TEMP TABLE exemples_livres (titre TEXT, auteur TEXT, isbn TEXT, annee INTEGER, genre TEXT, nb INTEGER);
INSERT INTO exemples_livres VALUES
    ('Le Petit Prince', 'Antoine de Saint-Exupéry', '9782070612758', 1943, 'Conte', 3),
    ('L''Étranger', 'Albert Camus', '9782070360024', 1942, 'Roman', 2),
    ('Les Misérables', 'Victor Hugo', '9782253096344', 1862, 'Roman', 1),
    ('1984', 'George Orwell', '9782070368228', 1949, 'Science-fiction', 2),
    ('Harry Potter à l''école des sorciers', 'J. K. Rowling', '9782070584628', 1997, 'Fantasy', 4),
    ('Le Comte de Monte-Cristo', 'Alexandre Dumas', '9782253098058', 1844, 'Aventure', 1),
    ('Fondation', 'Isaac Asimov', '9782070360536', 1951, 'Science-fiction', 2),
    ('Madame Bovary', 'Gustave Flaubert', '9782253004868', 1857, 'Roman', 1),
    ('Le Seigneur des anneaux', 'J. R. R. Tolkien', '9782266282369', 1954, 'Fantasy', 2),
    ('Vingt mille lieues sous les mers', 'Jules Verne', '9782253006329', 1870, 'Aventure', 2);
DELETE FROM exemples_livres WHERE (SELECT COUNT(*) FROM livres) > 0;
INSERT INTO livres (titre, auteur, isbn, annee, genre, nb_exemplaires)
    SELECT titre, auteur, isbn, annee, genre, nb FROM exemples_livres;
DROP TABLE exemples_livres;

-- Quelques emprunts d'exemple (un en cours, un en retard, un déjà rendu),
-- seulement si aucun emprunt n'existe encore
INSERT INTO emprunts (livre_id, utilisateur_id, date_emprunt, date_retour_prevue, date_retour)
    SELECT livres.id, utilisateurs.id, datetime('now', '-3 days'), date('now', '+18 days'), NULL
    FROM livres, utilisateurs
    WHERE livres.titre = 'Le Petit Prince' AND utilisateurs.login = 'user'
      AND (SELECT COUNT(*) FROM emprunts) = 0;
INSERT INTO emprunts (livre_id, utilisateur_id, date_emprunt, date_retour_prevue, date_retour)
    SELECT livres.id, utilisateurs.id, datetime('now', '-30 days'), date('now', '-9 days'), NULL
    FROM livres, utilisateurs
    WHERE livres.titre = 'Les Misérables' AND utilisateurs.login = 'lea'
      AND (SELECT COUNT(*) FROM emprunts) = 1;
INSERT INTO emprunts (livre_id, utilisateur_id, date_emprunt, date_retour_prevue, date_retour)
    SELECT livres.id, utilisateurs.id, datetime('now', '-40 days'), date('now', '-19 days'), datetime('now', '-25 days')
    FROM livres, utilisateurs
    WHERE livres.titre = '1984' AND utilisateurs.login = 'user'
      AND (SELECT COUNT(*) FROM emprunts) = 2;
