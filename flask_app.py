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
from werkzeug.security import check_password_hash, generate_password_hash

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
        return redirect(url_for('authentification', next=request.path))

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
            session['utilisateur_id'] = compte['id']
            # Revenir sur la page demandée avant la connexion, sinon vers la route lecture
            suivante = request.args.get('next', '')
            if suivante.startswith('/') and not suivante.startswith('//'):
                return redirect(suivante)
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
        return redirect(url_for('authentification', next=request.path))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients ORDER BY nom;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
    if not a_le_role('admin'):
        return acces_refuse()
    return render_template('formulaire.html')  # afficher le formulaire


@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    if not est_authentifie():
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
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
        return redirect(url_for('authentification', next=request.path))
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


# ===============================================================
#  📚 PROJET BIBLIOTHÈQUE (exercice 10)
# ===============================================================

DUREE_EMPRUNT_JOURS = 21   # durée d'un prêt
MAX_EMPRUNTS = 3           # règle R2 : 3 livres en même temps au maximum

# La disponibilité n'est pas stockée : elle se CALCULE à partir des emprunts en cours.
REQUETE_LIVRES = (
    'SELECT livres.*, '
    'livres.nb_exemplaires - COUNT(emprunts.id) AS nb_disponibles '
    'FROM livres '
    'LEFT JOIN emprunts ON emprunts.livre_id = livres.id AND emprunts.date_retour IS NULL '
)


def utilisateur_id():
    """Renvoie l'id (table utilisateurs) de la personne connectée."""
    if 'utilisateur_id' not in session and session.get('utilisateur'):
        conn = get_db()
        row = conn.execute('SELECT id FROM utilisateurs WHERE login = ?',
                           (session['utilisateur'],)).fetchone()
        conn.close()
        if row:
            session['utilisateur_id'] = row['id']
    return session.get('utilisateur_id')


def message(titre, texte, code=200, lien=None, texte_lien=None):
    """Affiche une page de message (refus d'une règle de gestion, erreur...)."""
    return render_template('message.html', titre=titre, message=texte,
                           lien=lien, texte_lien=texte_lien), code


def lire_livre(conn, id):
    return conn.execute(REQUETE_LIVRES + 'WHERE livres.id = ? GROUP BY livres.id', (id,)).fetchone()


# ---------- F3 : catalogue et recherche ----------

@app.route('/livres')
def catalogue():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification', next=request.path))
    q = request.args.get('q', '').strip()
    conn = get_db()
    if q:
        motif = '%' + q + '%'
        livres = conn.execute(REQUETE_LIVRES + 'WHERE livres.titre LIKE ? OR livres.auteur LIKE ? '
                              'GROUP BY livres.id ORDER BY livres.titre', (motif, motif)).fetchall()
    else:
        livres = conn.execute(REQUETE_LIVRES + 'GROUP BY livres.id ORDER BY livres.titre').fetchall()
    nb_en_cours = conn.execute('SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? AND date_retour IS NULL',
                               (utilisateur_id(),)).fetchone()[0]
    conn.close()
    return render_template('livres.html', livres=livres, q=q,
                           nb_en_cours=nb_en_cours, max_emprunts=MAX_EMPRUNTS)


@app.route('/livres/<int:id>')
def fiche_livre(id):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification', next=request.path))
    conn = get_db()
    livre = lire_livre(conn, id)
    emprunts = []
    if livre is not None and a_le_role('admin'):
        emprunts = conn.execute(
            'SELECT emprunts.*, utilisateurs.login, utilisateurs.nom, utilisateurs.prenom '
            'FROM emprunts JOIN utilisateurs ON utilisateurs.id = emprunts.utilisateur_id '
            'WHERE emprunts.livre_id = ? ORDER BY emprunts.date_emprunt DESC', (id,)).fetchall()
    conn.close()
    if livre is None:
        return message("Livre introuvable", f"Aucun livre ne porte le numéro {id}.", 404)
    return render_template('fiche_livre.html', livre=livre, emprunts=emprunts)


# ---------- F1, F2 : administration des livres ----------

def lire_formulaire_livre():
    """Récupère les champs du formulaire livre et renvoie (valeurs, erreur)."""
    valeurs = {
        'titre': request.form.get('titre', '').strip(),
        'auteur': request.form.get('auteur', '').strip(),
        'isbn': request.form.get('isbn', '').strip() or None,
        'genre': request.form.get('genre', '').strip() or None,
        'annee': request.form.get('annee', '').strip() or None,
        'nb_exemplaires': request.form.get('nb_exemplaires', '1').strip(),
    }
    # Règle R5 : pas de livre sans titre ni auteur
    if not valeurs['titre'] or not valeurs['auteur']:
        return valeurs, "Le titre et l'auteur sont obligatoires."
    try:
        valeurs['nb_exemplaires'] = int(valeurs['nb_exemplaires'])
        if valeurs['annee'] is not None:
            valeurs['annee'] = int(valeurs['annee'])
    except ValueError:
        return valeurs, "L'année et le nombre d'exemplaires doivent être des nombres entiers."
    if valeurs['nb_exemplaires'] < 0:
        return valeurs, "Le nombre d'exemplaires ne peut pas être négatif."
    return valeurs, None


@app.route('/livres/nouveau', methods=['GET', 'POST'])
def nouveau_livre():
    if not est_authentifie():
        return redirect(url_for('authentification', next=request.path))
    if not a_le_role('admin'):
        return acces_refuse()
    if request.method == 'POST':
        valeurs, erreur = lire_formulaire_livre()
        if erreur:
            return render_template('formulaire_livre.html', livre=valeurs, erreur=erreur, nouveau=True), 400
        conn = get_db()
        cursor = conn.execute(
            'INSERT INTO livres (titre, auteur, isbn, annee, genre, nb_exemplaires) VALUES (?, ?, ?, ?, ?, ?)',
            (valeurs['titre'], valeurs['auteur'], valeurs['isbn'], valeurs['annee'],
             valeurs['genre'], valeurs['nb_exemplaires']))
        conn.commit()
        nouvel_id = cursor.lastrowid
        conn.close()
        return redirect(url_for('fiche_livre', id=nouvel_id))
    return render_template('formulaire_livre.html', livre={'nb_exemplaires': 1}, nouveau=True)


@app.route('/livres/<int:id>/modifier', methods=['GET', 'POST'])
def modifier_livre(id):
    if not est_authentifie():
        return redirect(url_for('authentification', next=request.path))
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    livre = lire_livre(conn, id)
    if livre is None:
        conn.close()
        return message("Livre introuvable", f"Aucun livre ne porte le numéro {id}.", 404)

    if request.method == 'POST':
        valeurs, erreur = lire_formulaire_livre()
        nb_empruntes = livre['nb_exemplaires'] - livre['nb_disponibles']
        if not erreur and valeurs['nb_exemplaires'] < nb_empruntes:
            erreur = (f"{nb_empruntes} exemplaire(s) sont actuellement empruntés : "
                      f"le stock ne peut pas descendre en dessous.")
        if erreur:
            conn.close()
            valeurs['id'] = id
            return render_template('formulaire_livre.html', livre=valeurs, erreur=erreur, nouveau=False), 400
        conn.execute('UPDATE livres SET titre = ?, auteur = ?, isbn = ?, annee = ?, genre = ?, '
                     'nb_exemplaires = ? WHERE id = ?',
                     (valeurs['titre'], valeurs['auteur'], valeurs['isbn'], valeurs['annee'],
                      valeurs['genre'], valeurs['nb_exemplaires'], id))
        conn.commit()
        conn.close()
        return redirect(url_for('fiche_livre', id=id))

    conn.close()
    return render_template('formulaire_livre.html', livre=livre, nouveau=False)


@app.route('/livres/<int:id>/supprimer', methods=['POST'])
def supprimer_livre(id):
    if not est_authentifie():
        return redirect(url_for('authentification', next=request.path))
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    try:
        livre = lire_livre(conn, id)
        if livre is None:
            return message("Livre introuvable", f"Aucun livre ne porte le numéro {id}.", 404)
        # Règle R3 : pas de suppression si un exemplaire est en cours d'emprunt
        nb_empruntes = livre['nb_exemplaires'] - livre['nb_disponibles']
        if nb_empruntes > 0:
            return message("Suppression impossible",
                           f"« {livre['titre']} » a {nb_empruntes} exemplaire(s) en cours d'emprunt.",
                           409, url_for('fiche_livre', id=id), "Voir le livre")
        # Les emprunts déjà rendus (historique) sont supprimés avec le livre
        conn.execute('DELETE FROM emprunts WHERE livre_id = ?', (id,))
        conn.execute('DELETE FROM livres WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('catalogue'))


# ---------- F4, F5, F6 : emprunter, rendre, mes emprunts ----------

@app.route('/livres/<int:id>/emprunter', methods=['POST'])
def emprunter(id):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification', next=request.path))
    uid = utilisateur_id()
    conn = get_db()
    try:
        livre = lire_livre(conn, id)
        if livre is None:
            return message("Livre introuvable", f"Aucun livre ne porte le numéro {id}.", 404)
        # Règle R1 : il faut un exemplaire disponible
        if livre['nb_disponibles'] <= 0:
            return message("Emprunt impossible",
                           f"Tous les exemplaires de « {livre['titre']} » sont déjà empruntés.",
                           409, url_for('catalogue'), "Retour au catalogue")
        # Règle R2 : 3 emprunts en cours au maximum
        nb_en_cours = conn.execute('SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? '
                                   'AND date_retour IS NULL', (uid,)).fetchone()[0]
        if nb_en_cours >= MAX_EMPRUNTS:
            return message("Emprunt impossible",
                           f"Vous avez déjà {nb_en_cours} livres empruntés : "
                           f"rendez-en un avant d'en emprunter un autre (maximum {MAX_EMPRUNTS}).",
                           409, url_for('mes_emprunts'), "Voir mes emprunts")
        conn.execute("INSERT INTO emprunts (livre_id, utilisateur_id, date_retour_prevue) "
                     "VALUES (?, ?, date('now', ?))", (id, uid, f'+{DUREE_EMPRUNT_JOURS} days'))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('mes_emprunts'))


@app.route('/emprunts/<int:id>/rendre', methods=['POST'])
def rendre(id):
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification', next=request.path))
    conn = get_db()
    try:
        emprunt = conn.execute('SELECT * FROM emprunts WHERE id = ?', (id,)).fetchone()
        if emprunt is None:
            return message("Emprunt introuvable", f"Aucun emprunt ne porte le numéro {id}.", 404)
        # Un utilisateur ne peut rendre que SES livres ; l'admin peut tout rendre
        if emprunt['utilisateur_id'] != utilisateur_id() and not a_le_role('admin'):
            return message("Accès refusé", "Cet emprunt n'est pas le vôtre.", 403)
        if emprunt['date_retour'] is not None:
            return message("Déjà rendu", "Ce livre a déjà été rendu.", 409)
        # On ne supprime pas l'emprunt : on note la date de retour (historique)
        conn.execute('UPDATE emprunts SET date_retour = CURRENT_TIMESTAMP WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    retour = request.form.get('retour')
    return redirect(retour if retour in ('/emprunts', '/mes_emprunts') else url_for('mes_emprunts'))


@app.route('/mes_emprunts')
def mes_emprunts():
    if not a_le_role('user', 'admin'):
        return redirect(url_for('authentification', next=request.path))
    conn = get_db()
    emprunts = conn.execute(
        "SELECT emprunts.*, livres.titre, livres.auteur, "
        "(emprunts.date_retour IS NULL AND emprunts.date_retour_prevue < date('now')) AS en_retard "
        "FROM emprunts JOIN livres ON livres.id = emprunts.livre_id "
        "WHERE emprunts.utilisateur_id = ? "
        "ORDER BY emprunts.date_retour IS NOT NULL, emprunts.date_emprunt DESC",
        (utilisateur_id(),)).fetchall()
    conn.close()
    en_cours = [e for e in emprunts if e['date_retour'] is None]
    historique = [e for e in emprunts if e['date_retour'] is not None]
    return render_template('mes_emprunts.html', en_cours=en_cours, historique=historique,
                           max_emprunts=MAX_EMPRUNTS)


@app.route('/emprunts')
def tous_les_emprunts():
    """Bonus : l'admin voit tous les emprunts en cours, retards en premier."""
    if not est_authentifie():
        return redirect(url_for('authentification', next=request.path))
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    emprunts = conn.execute(
        "SELECT emprunts.*, livres.titre, utilisateurs.login, utilisateurs.nom, utilisateurs.prenom, "
        "(emprunts.date_retour_prevue < date('now')) AS en_retard "
        "FROM emprunts "
        "JOIN livres ON livres.id = emprunts.livre_id "
        "JOIN utilisateurs ON utilisateurs.id = emprunts.utilisateur_id "
        "WHERE emprunts.date_retour IS NULL "
        "ORDER BY en_retard DESC, emprunts.date_retour_prevue").fetchall()
    top = conn.execute(
        'SELECT livres.id, livres.titre, COUNT(emprunts.id) AS nb '
        'FROM livres JOIN emprunts ON emprunts.livre_id = livres.id '
        'GROUP BY livres.id ORDER BY nb DESC, livres.titre LIMIT 5').fetchall()
    conn.close()
    return render_template('emprunts.html', emprunts=emprunts, top=top)


# ---------- F7 : gestion des utilisateurs ----------

@app.route('/utilisateurs', methods=['GET', 'POST'])
def utilisateurs():
    if not est_authentifie():
        return redirect(url_for('authentification', next=request.path))
    if not a_le_role('admin'):
        return acces_refuse()
    conn = get_db()
    erreur = None
    if request.method == 'POST':
        login = request.form.get('login', '').strip().lower()
        nom = request.form.get('nom', '').strip().upper()
        prenom = request.form.get('prenom', '').strip()
        mot_de_passe = request.form.get('mot_de_passe', '')
        role = request.form.get('role', 'user')
        if not login or not nom or not prenom or len(mot_de_passe) < 5:
            erreur = "Tous les champs sont obligatoires (mot de passe : 5 caractères minimum)."
        elif role not in ('user', 'admin'):
            erreur = "Rôle inconnu."
        else:
            try:
                conn.execute('INSERT INTO utilisateurs (login, nom, prenom, mot_de_passe_hash, role) '
                             'VALUES (?, ?, ?, ?, ?)',
                             (login, nom, prenom,
                              generate_password_hash(mot_de_passe, method='pbkdf2:sha256:260000'), role))
                conn.commit()
                conn.close()
                return redirect(url_for('utilisateurs'))
            except sqlite3.IntegrityError:
                erreur = f"Le login « {login} » est déjà utilisé."
    liste = conn.execute(
        'SELECT utilisateurs.id, utilisateurs.login, utilisateurs.nom, utilisateurs.prenom, utilisateurs.role, '
        'COUNT(emprunts.id) AS nb_en_cours '
        'FROM utilisateurs LEFT JOIN emprunts '
        'ON emprunts.utilisateur_id = utilisateurs.id AND emprunts.date_retour IS NULL '
        'GROUP BY utilisateurs.id ORDER BY utilisateurs.login').fetchall()
    conn.close()
    return render_template('utilisateurs.html', utilisateurs=liste, erreur=erreur,
                           saisie=request.form if erreur else None), (400 if erreur else 200)


@app.route('/utilisateurs/<int:id>/supprimer', methods=['POST'])
def supprimer_utilisateur(id):
    if not est_authentifie():
        return redirect(url_for('authentification', next=request.path))
    if not a_le_role('admin'):
        return acces_refuse()
    if id == utilisateur_id():
        return message("Suppression impossible", "Vous ne pouvez pas supprimer votre propre compte.", 409,
                       url_for('utilisateurs'), "Retour aux utilisateurs")
    conn = get_db()
    try:
        nb = conn.execute('SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? AND date_retour IS NULL',
                          (id,)).fetchone()[0]
        if nb > 0:
            return message("Suppression impossible",
                           f"Cet utilisateur a encore {nb} livre(s) à rendre.", 409,
                           url_for('utilisateurs'), "Retour aux utilisateurs")
        conn.execute('DELETE FROM emprunts WHERE utilisateur_id = ?', (id,))
        conn.execute('DELETE FROM utilisateurs WHERE id = ?', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('utilisateurs'))


# ---------- F9 : API JSON des livres ----------

@app.get('/api/livres')
def api_livres():
    q = request.args.get('q', '').strip()
    conn = get_db()
    if q:
        motif = '%' + q + '%'
        rows = conn.execute(REQUETE_LIVRES + 'WHERE livres.titre LIKE ? OR livres.auteur LIKE ? '
                            'GROUP BY livres.id ORDER BY livres.titre', (motif, motif)).fetchall()
    else:
        rows = conn.execute(REQUETE_LIVRES + 'GROUP BY livres.id ORDER BY livres.titre').fetchall()
    conn.close()
    return jsonify([dict(row, disponible=row['nb_disponibles'] > 0) for row in rows])


@app.get('/api/livres/<int:id>')
def api_un_livre(id):
    conn = get_db()
    row = lire_livre(conn, id)
    conn.close()
    if row is None:
        return jsonify({'erreur': 'Livre introuvable'}), 404
    return jsonify(dict(row, disponible=row['nb_disponibles'] > 0))


# ---------------------------------------------------------------
#  Ajoutez vos nouvelles routes ci-dessous 👇
# ---------------------------------------------------------------


# ---------------------------------------------------------------
#  Ne pas modifier : utile seulement pour lancer le site
#  sur votre propre ordinateur (python flask_app.py)
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
