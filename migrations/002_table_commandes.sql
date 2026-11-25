-- Exercice 7 : une deuxième table, reliée aux clients par une clé étrangère
CREATE TABLE IF NOT EXISTS commandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    produit TEXT NOT NULL,
    montant REAL NOT NULL,
    date_commande TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id)
);

-- Quelques commandes d'exemple, seulement si la table est vide
-- et seulement pour des clients qui existent encore
CREATE TEMP TABLE exemples (client_id INTEGER, produit TEXT, montant REAL);
INSERT INTO exemples VALUES
    (2, 'Clavier', 49.90), (2, 'Souris', 19.90), (3, 'Écran', 189.00),
    (5, 'Casque', 79.00), (5, 'Webcam', 59.00), (5, 'Câble HDMI', 9.90);
DELETE FROM exemples WHERE (SELECT COUNT(*) FROM commandes) > 0;
INSERT INTO commandes (client_id, produit, montant)
    SELECT exemples.client_id, exemples.produit, exemples.montant
    FROM exemples JOIN clients ON clients.id = exemples.client_id;
DROP TABLE exemples;
