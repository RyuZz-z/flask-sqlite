# ---------------------------------------------------------------
#  Migrations : faire évoluer la STRUCTURE de la base sans perdre
#  les DONNÉES (exercice 6, défi).
# ---------------------------------------------------------------
#  Chaque fichier de migrations/ (001_..., 002_...) n'est exécuté
#  qu'UNE seule fois par base : la table "migrations_appliquees"
#  garde la liste de ceux qui ont déjà été appliqués.
#
#  Les migrations sont lancées automatiquement au démarrage de
#  l'application (voir flask_app.py). On peut aussi les lancer
#  à la main depuis une console Bash PythonAnywhere :
#      cd ~/mysite
#      python3 migrate.py
# ---------------------------------------------------------------

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOSSIER_MIGRATIONS = os.path.join(BASE_DIR, 'migrations')


def appliquer_migrations(chemin_base):
    """Applique, dans l'ordre, les migrations qui ne l'ont pas encore été."""
    if not os.path.isdir(DOSSIER_MIGRATIONS):
        return []

    conn = sqlite3.connect(chemin_base)
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS migrations_appliquees ('
                     'nom TEXT PRIMARY KEY, '
                     'date_application TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        deja_faites = {row[0] for row in conn.execute('SELECT nom FROM migrations_appliquees')}

        appliquees = []
        for nom in sorted(os.listdir(DOSSIER_MIGRATIONS)):
            if not nom.endswith('.sql') or nom in deja_faites:
                continue
            with open(os.path.join(DOSSIER_MIGRATIONS, nom), encoding='utf-8') as f:
                script = f.read()
            try:
                conn.executescript(script)
            except sqlite3.OperationalError as erreur:
                # La modification a déjà été faite à la main (ex : ALTER TABLE
                # tapé dans la console à l'exercice 6) : on la note comme faite.
                if 'duplicate column' not in str(erreur):
                    raise
            conn.execute('INSERT INTO migrations_appliquees (nom) VALUES (?)', (nom,))
            conn.commit()
            appliquees.append(nom)
        return appliquees
    finally:
        conn.close()


if __name__ == '__main__':
    faites = appliquer_migrations(os.path.join(BASE_DIR, 'database.db'))
    if faites:
        for nom in faites:
            print('✅ Migration appliquée :', nom)
    else:
        print('👍 La base est déjà à jour.')
