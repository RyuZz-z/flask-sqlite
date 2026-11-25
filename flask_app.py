# ---------------------------------------------------------------
#  Atelier Flask + SQLite
# ---------------------------------------------------------------
#  Ce fichier est le "cerveau" de votre application : il reçoit
#  les demandes des navigateurs, interroge la base de données
#  et fabrique les réponses.
#
#  Vous allez le compléter petit à petit, exercice après exercice.
#  Les consignes sont dans le dossier "exercices/".
# ---------------------------------------------------------------

import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash

from migrate import appliquer_migrations

app = Flask(__name__)
# Clé secrète pour signer les sessions. On peut la cacher dans une variable
# d'environnement SECRET_KEY ; sinon, la valeur par défaut est utilisée.
app.secret_key = os.environ.get('SECRET_KEY', b'_5#y2L"F4Q8z\n\xec]/')

# Chemin ABSOLU vers la base de données.
# Sur PythonAnywhere, le serveur ne démarre pas forcément dans le dossier
# du projet : un simple 'database.db' créerait une base vide ailleurs !
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')

# Exercice 6 (défi) : au démarrage, on applique les migrations qui manquent
# (colonne telephone, tables commandes et utilisateurs) sans toucher aux données.
if os.path.exists(DATABASE):
    try:
        for nom_migration in appliquer_migrations(DATABASE):
            print('Migration appliquée :', nom_migration, flush=True)
    except sqlite3.Error as erreur:
        print('⚠️ Migrations non appliquées :', erreur, flush=True)


def get_db():
    """Ouvre une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # pour écrire row['nom'] au lieu de row[2]
    conn.execute('PRAGMA foreign_keys = ON')  # faire respecter les clés étrangères
    return conn


# ---------------------------------------------------------------
#  Contrôle d'accès (exercice 8)
# ---------------------------------------------------------------

# Fonction pour savoir si l'utilisateur s'est authentifié
def est_authentifie():
    return session.get('authentifie')


def a_le_role(*roles):
    """Renvoie True si l'utilisateur connecté a l'un des rôles indiqués."""
    return session.get('role') in roles


def acces_refuse():
    """Réponse renvoyée à un utilisateur connecté qui n'est pas admin."""
    return render_template('message.html', titre="Accès refusé",
                           message="Cette page est réservée aux administrateurs."), 403


@app.route('/')
def hello_world():
    return render_template('hello.html')


@app.route('/lecture')
def lecture():
    if not est_authentifie():
        # Rediriger vers la page d'authentification si l'utilisateur n'est pas authentifié
        return redirect(url_for('authentification'))

    # Si l'utilisateur est authentifié
    return render_template('message.html', titre="Bravo, vous êtes authentifié",
                           message=f"Connecté en tant que {session['utilisateur']} "
                                   f"(rôle : {session['role']}).")


@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        login = request.form.get('username', '').strip()
        mot_de_passe = request.form.get('password', '')

        # Les comptes sont rangés en base, avec un mot de passe haché (défi de l'exercice 8)
        conn = get_db()
        compte = conn.execute('SELECT * FROM utilisateurs WHERE login = ?', (login,)).fetchone()
        conn.close()

        if compte and check_password_hash(compte['mot_de_passe_hash'], mot_de_passe):
            session['authentifie'] = True
            session['utilisateur'] = compte['login']
            session['role'] = compte['role']
            # Rediriger vers la route lecture après une authentification réussie
            return redirect(url_for('lecture'))
        # Afficher un message d'erreur si les identifiants sont incorrects
        return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)


@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect('/')


# ---------------------------------------------------------------
#  Lire les clients (exercices 2 et 3)
# ---------------------------------------------------------------

@app.route('/consultation/')
def ReadBDD():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients ORDER BY nom;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    client = cursor.fetchone()
    # Deuxième requête : les commandes de ce client (exercice 7)
    cursor.execute('SELECT * FROM commandes WHERE client_id = ? ORDER BY date_commande DESC', (post_id,))
    commandes = cursor.fetchall()
    conn.close()
    if client is None:
        return render_template('message.html', titre="Client introuvable",
                               message=f"Aucun client ne porte le numéro {post_id}."), 404
    erreur = request.args.get('erreur')
    return render_template('fiche_client.html', client=client, commandes=commandes, erreur=erreur)


@app.route('/fiche_nom/<nom>')
def fiche_nom(nom):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE nom = ?', (nom,))
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


# Défi de l'exercice 3 : on ne peut pas mettre "?" à la place d'un nom de
# colonne dans ORDER BY. On n'accepte donc que les valeurs de cette liste.
TRIS_AUTORISES = {
    'nom': ('Nom', 'nom, prenom'),
    'prenom': ('Prénom', 'prenom, nom'),
    'created': ('Date de création', 'created DESC'),
}


@app.route('/recherche')
def recherche():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    q = request.args.get('q', '').strip()
    tri = request.args.get('tri', 'nom')
    if tri not in TRIS_AUTORISES:
        tri = 'nom'
    data = []
    if q:
        conn = get_db()
        cursor = conn.cursor()
        motif = '%' + q + '%'
        cursor.execute('SELECT * FROM clients WHERE nom LIKE ? OR prenom LIKE ? ORDER BY '
                       + TRIS_AUTORISES[tri][1], (motif, motif))
        data = cursor.fetchall()
        conn.close()
    return render_template('recherche.html', q=q, data=data, tri=tri, tris=TRIS_AUTORISES)


# ---------------------------------------------------------------
#  Enregistrer, modifier, supprimer (exercices 4 et 5)
# ---------------------------------------------------------------

def lire_formulaire_client():
    """Récupère et nettoie les champs du formulaire client."""
    nom = request.form.get('nom', '').strip().upper()
    prenom = request.form.get('prenom', '').strip()
    adresse = request.form.get('adresse', '').strip()
    telephone = request.form.get('telephone', '').strip() or None
    return nom, prenom, adresse, telephone


@app.route('/enregistrer_client', methods=['GET'])
def formulaire_client():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    if not a_le_role('admin'):
        return acces_refuse()
    return render_template('formulaire.html')  # afficher le formulaire


@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    if not a_le_role('admin'):
        return acces_refuse()

    nom, prenom, adresse, telephone = lire_formulaire_client()

    # Validation côté serveur : on ne fait jamais confiance au navigateur
    if not nom or not prenom or not adresse:
        return render_template('formulaire.html', erreur="Tous les champs sont obligatoires.",
                               saisie=request.form), 400

    # Connexion à la base de données
    conn = get_db()
    cursor = conn.cursor()

    # Exécution de la requête SQL pour insérer un nouveau client
    # (la colonne "created" est remplie par SQLite avec la date du jour)
    cursor.execute('INSERT INTO clients (nom, prenom, adresse, telephone) VALUES (?, ?, ?, ?)',
                   (nom, prenom, adresse, telephone))
    conn.commit()
    nouvel_id = cursor.lastrowid
    conn.close()
    # Défi de l'exercice 4 : on affiche la fiche du client qu'on vient de créer
    return redirect(url_for('Readfiche', post_id=nouvel_id))


@app.route('/modifier_client/<int:id>', methods=['GET', 'POST'])
def modifier_client(id):
    if not est_authentifie():
        return redirect(url_for('authentification'))
    if not a_le_role('admin'):
        return acces_refuse()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (id,))
    client = cursor.fetchone()
    if client is None:
        conn.close()
        return render_template('message.html', titre="Client introuvable",
                               message=f"Aucun client ne porte le numéro {id}."), 404

    if request.method == 'POST':
        nom, prenom, adresse, telephone = lire_formulaire_client()
        if not nom or not prenom or not adresse:
            conn.close()
            return render_template('modifier_client.html', client=client,
                                   erreur="Le nom, le prénom et l'adresse sont obligatoires."), 400
        cursor.execute('UPDATE clients SET nom = ?, prenom = ?, adresse = ?, telephone = ? WHERE id = ?',
                       (nom, prenom, adresse, telephone, id))
        conn.commit()
        conn.close()
        return redirect('/consultation/')

    conn.close()
    return render_template('modifier_client.html', client=client)


@app.route('/supprimer_client/<int:id>', methods=['POST'])
def supprimer_client(id):
    if not est_authentifie():
        return redirect(url_for('authentification'))
    if not a_le_role('admin'):
        return acces_refuse()

    conn = get_db()
    try:
        conn.execute('DELETE FROM clients WHERE id = ?', (id,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Défi de l'exercice 7 : un message clair, avec le vrai nombre de commandes
        nb = conn.execute('SELECT COUNT(*) FROM commandes WHERE client_id = ?', (id,)).fetchone()[0]
        return render_template('message.html', titre="Suppression impossible",
                               message=f"Ce client a {nb} commande(s) : il ne peut pas être supprimé.",
                               lien=url_for('Readfiche', post_id=id),
                               texte_lien="Voir sa fiche"), 409
    finally:
        conn.close()  # exécuté dans TOUS les cas, même après le return
    return redirect('/consultation/')


# ---------------------------------------------------------------
#  Commandes et statistiques (exercice 7)
# ---------------------------------------------------------------

@app.route('/commandes/')
def liste_commandes():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    commandes = conn.execute(
        'SELECT commandes.id, commandes.client_id, clients.nom, clients.prenom, '
        'commandes.produit, commandes.montant, commandes.date_commande '
        'FROM commandes JOIN clients ON commandes.client_id = clients.id '
        'ORDER BY commandes.date_commande DESC'
    ).fetchall()
    conn.close()
    return render_template('commandes.html', commandes=commandes)


@app.route('/fiche_client/<int:post_id>/commandes', methods=['POST'])
def ajouter_commande(post_id):
    """Défi de l'exercice 7 : créer une commande depuis la fiche client."""
    if not est_authentifie():
        return redirect(url_for('authentification'))
    if not a_le_role('admin'):
        return acces_refuse()

    produit = request.form.get('produit', '').strip()
    try:
        montant = float(request.form.get('montant', '').replace(',', '.'))
    except ValueError:
        montant = 0
    if not produit or montant <= 0:
        return redirect(url_for('Readfiche', post_id=post_id,
                                erreur="Indiquez un produit et un montant positif."))

    conn = get_db()
    try:
        conn.execute('INSERT INTO commandes (client_id, produit, montant) VALUES (?, ?, ?)',
                     (post_id, produit, montant))
        conn.commit()
    except sqlite3.IntegrityError:
        return render_template('message.html', titre="Client introuvable",
                               message=f"Aucun client ne porte le numéro {post_id}."), 404
    finally:
        conn.close()
    return redirect(url_for('Readfiche', post_id=post_id))


@app.route('/statistiques/')
def statistiques():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification'))
    conn = get_db()
    stats = conn.execute(
        'SELECT clients.id, clients.nom, clients.prenom, '
        'COUNT(commandes.id) AS nb_commandes, '
        'COALESCE(SUM(commandes.montant), 0) AS total '
        'FROM clients LEFT JOIN commandes ON commandes.client_id = clients.id '
        'GROUP BY clients.id ORDER BY total DESC, clients.nom'
    ).fetchall()
    conn.close()
    return render_template('statistiques.html', stats=stats)


# ---------------------------------------------------------------
#  API JSON (exercice 9)
# ---------------------------------------------------------------

@app.get('/api/clients')
def api_liste_clients():
    q = request.args.get('q', '').strip()
    conn = get_db()
    if q:
        motif = '%' + q + '%'
        rows = conn.execute('SELECT * FROM clients WHERE nom LIKE ? OR prenom LIKE ? ORDER BY nom',
                            (motif, motif)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM clients ORDER BY nom').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.get('/api/clients/<int:id>')
def api_un_client(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM clients WHERE id = ?', (id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({'erreur': 'Client introuvable'}), 404
    return jsonify(dict(row))


@app.post('/api/clients')
def api_creer_client():
    if not a_le_role('admin'):
        return jsonify({'erreur': 'Authentification administrateur requise'}), 401

    donnees = request.get_json(silent=True) or {}
    nom = str(donnees.get('nom', '')).strip().upper()
    prenom = str(donnees.get('prenom', '')).strip()
    adresse = str(donnees.get('adresse', '')).strip()
    telephone = str(donnees.get('telephone') or '').strip() or None

    if not nom or not prenom or not adresse:
        return jsonify({'erreur': 'Les champs nom, prenom et adresse sont obligatoires'}), 400

    conn = get_db()
    cursor = conn.execute('INSERT INTO clients (nom, prenom, adresse, telephone) VALUES (?, ?, ?, ?)',
                          (nom, prenom, adresse, telephone))
    conn.commit()
    nouvel_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': nouvel_id, 'nom': nom, 'prenom': prenom,
                    'adresse': adresse, 'telephone': telephone}), 201


@app.delete('/api/clients/<int:id>')
def api_supprimer_client(id):
    if not a_le_role('admin'):
        return jsonify({'erreur': 'Authentification administrateur requise'}), 401

    conn = get_db()
    try:
        cursor = conn.execute('DELETE FROM clients WHERE id = ?', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'erreur': 'Client introuvable'}), 404
    except sqlite3.IntegrityError:
        return jsonify({'erreur': 'Ce client a des commandes : suppression impossible'}), 409
    finally:
        conn.close()
    return jsonify({'supprime': id})


@app.route('/clients_js')
def clients_js():
    """Défi de l'exercice 9 : une page qui appelle l'API en JavaScript."""
    return render_template('clients_js.html')


# ---------------------------------------------------------------
#  Ajoutez vos nouvelles routes ci-dessous 👇
# ---------------------------------------------------------------


# ---------------------------------------------------------------
#  Ne pas modifier : utile seulement pour lancer le site
#  sur votre propre ordinateur (python flask_app.py)
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
