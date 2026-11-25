# 📒 Mon carnet de bord

**Nom :GLOUZOUIC

**Prénom :Mateo

**Adresse de mon site :** https://ryuzz.pythonanywhere.com

**Adresse de mon dépôt GitHub :** https://github.com/RyuZz-z/flask-sqlite

> Modifiez ce fichier directement sur GitHub (icône crayon ✏️) pour répondre aux questions de chaque exercice.
> Écrivez avec vos propres mots : une réponse courte et juste vaut mieux qu'un long copier-coller ! 🙂

---

## 🟢 Exercice 1 — Explorer la base en SQL

1. Expliquez avec vos mots la différence entre une **table**, une **colonne** et une **ligne**.

   > _Ma réponse :_ Une tables c'est un tableau qui contient différentes lignes et colonnes

2. À quoi sert la clé primaire `id` ? Pourquoi ne pas simplement identifier un client par son nom ?

   > _Ma réponse :_ L'ID permet de pouvoir différencier les clients entre eux et aussi d'éviter qu'en faisant une recherche par nom ou prénom ou adresse on retrouve plusieurs clients.

3. Pourquoi votre client ajouté en console est-il apparu sur le site ?

   > _Ma réponse :_ Notre client ajouté en console est apparu sur le site car nous l'avons écrit dans sa database directement et les deux étant liés cela remonte instinctivement.

4. Que signifie `NOT NULL` dans `schema.sql` ? Quelle erreur avez-vous obtenue avec `INSERT INTO clients (nom) VALUES ('TEST');` ?

   > _Ma réponse :_ NOT NULL oblige une colonne à avoir une valeur ; j'ai eu l'erreur NOT NULL constraint failed: clients.prenom car je n'ai pas donné de prenom

🧩 **Défi** — mes requêtes / ma solution :

   >SELECT * from clients order by id desc limit 3;
   >SELECT * from clients where prenom like 'A%';
   >SELECT count(*) from clients where adresse like '%Paris%';   

---

## 🟢 Exercice 2 — Afficher les données proprement

1. Décrivez avec vos mots le trajet d'une requête, du navigateur jusqu'à la base de données, puis le retour.

   > _Ma réponse :_ Le navigateur envoie une requête HTTP (ex : `/consultation/`) au serveur. Flask trouve la route correspondante et exécute la fonction Python, qui se connecte à la base SQLite et lance une requête SQL. La base renvoie les lignes, Flask les injecte dans le template HTML, puis renvoie la page HTML au navigateur qui l'affiche.

2. Pourquoi faut-il **fermer** la connexion (`conn.close()`) après chaque requête ?

   > _Ma réponse :_ Pour libérer la base : une connexion ouverte bloque des ressources et peut verrouiller le fichier SQLite, ce qui empêcherait d'autres requêtes (surtout les écritures) de fonctionner.

3. Quel est l'avantage d'écrire `row['nom']` plutôt que `row[2]` ? (Pensez à ce qui arriverait si on ajoutait une colonne au milieu de la table.)

   > _Ma réponse :_ row['nom']` cherche la colonne par son nom, donc le code marche toujours même si on ajoute ou déplace une colonne. Avec `row[2]`, si on ajoute une colonne au milieu, l'index 2 pointe vers une autre colonne et on affiche les mauvaises données. C'est aussi plus lisible.

4. Pourquoi est-il préférable de trier avec `ORDER BY` dans la requête SQL plutôt qu'en Python ?

   > _Ma réponse :_ La base de données est optimisée pour trier, elle renvoie directement les lignes dans le bon ordre. Le code Python reste plus simple et c'est plus rapide quand il y a beaucoup de données.

---

## 🟢 Exercice 3 — Rechercher un client

1. Quelle est la différence entre `WHERE nom = 'DUPONT'` et `WHERE nom LIKE '%DUP%'` ?

   > _Ma réponse :_ `=` cherche une valeur exactement identique (DUPONT, et pas dupont ni DUP). `LIKE '%DUP%'` cherche un motif : `%` remplace n'importe quels caractères, donc tous les noms qui contiennent « DUP » sont trouvés (et dans SQLite, `LIKE` ignore les majuscules).

2. Expliquez avec vos mots ce qu'est une **injection SQL**. Qu'est-ce qu'un pirate pourrait faire de pire qu'afficher tous les clients ?

   > _Ma réponse :_ C'est quand le texte tapé par l'utilisateur est collé directement dans la requête SQL : il peut alors ajouter du SQL à lui (ex : `x' OR '1'='1`) et changer le sens de la requête. Au pire, un pirate pourrait lire des données secrètes (mots de passe), modifier ou supprimer des lignes, voire supprimer des tables entières (`DROP TABLE`).

3. Pourquoi la version avec `?` est-elle protégée contre l'injection ?

   > _Ma réponse :_ Avec `?`, la valeur est envoyée à part de la requête : SQLite la traite toujours comme une simple donnée, jamais comme du code SQL. Même si elle contient des apostrophes ou `OR '1'='1'`, elle est juste comparée au nom.

4. Pour la recherche, on a utilisé `method="get"`. Quel avantage pour l'utilisateur ? (Indice : favoris, partage de lien.)

   > _Ma réponse :_ Avec GET, la recherche apparaît dans l'URL (`/recherche?q=dup`) : on peut l'ajouter en favori, la partager par un lien, revenir en arrière ou recharger la page sans renvoyer de formulaire.

🧩 **Défi** — mes requêtes / ma solution :

   > J'ai ajouté une liste déroulante `tri` (nom, prénom, date de création) au formulaire. Dans `flask_app.py`, un dictionnaire `TRIS_AUTORISES` associe chaque choix à une colonne : si la valeur reçue n'est pas dans la liste, on trie par nom. Ainsi, seul du SQL écrit par moi arrive dans le `ORDER BY`, et l'utilisateur ne peut pas injecter de code.

---

## 🔵 Exercice 4 — Enregistrer un client

1. Quelles étaient les deux anomalies du formulaire d'origine, et d'où venaient-elles ?

   > _Ma réponse :_ 1) Il n'y avait pas de champ adresse : le code mettait toujours « ICI » (`"ICI"` écrit en dur dans l'`INSERT`). 2) La date de création était fausse : le code mettait toujours la valeur fixe `1002938` dans `created` au lieu de laisser SQLite mettre la date du jour.

2. Pourquoi la validation côté **navigateur** (`required`) ne suffit-elle pas ? Pourquoi la garder quand même ?

   > _Ma réponse :_ Parce que tout ce qui est côté navigateur peut être modifié par l'utilisateur (F12, ou envoyer la requête sans le formulaire) : seul le serveur est fiable. On garde quand même `required` parce que ça prévient l'utilisateur tout de suite, sans aller-retour avec le serveur : c'est plus confortable.

3. À quoi sert `conn.commit()` ? Que se passe-t-il sans lui ?

   > _Ma réponse :_ `commit()` valide définitivement les modifications dans la base. Sans lui, l'`INSERT` est annulé à la fermeture de la connexion : le client n'apparaît jamais dans la liste.

4. Pourquoi redirige-t-on vers `/consultation/` après l'enregistrement, au lieu d'afficher directement une page ? (Indice : essayez d'appuyer sur F5 après l'envoi.)

   > _Ma réponse :_ Si on affichait directement une page après le POST, appuyer sur F5 renverrait le formulaire et créerait le client une deuxième fois. Avec la redirection (302), le navigateur fait un nouveau GET vers la liste : F5 recharge juste la liste, sans doublon.

---

## 🔵 Exercice 5 — Modifier et supprimer

1. Que signifie CRUD ? Donnez la requête SQL correspondant à chaque lettre.

   > _Ma réponse :_ CRUD = Create, Read, Update, Delete. Create → `INSERT INTO`, Read → `SELECT`, Update → `UPDATE ... SET ... WHERE`, Delete → `DELETE FROM ... WHERE`.

2. Que se passe-t-il si l'on oublie le `WHERE` dans un `UPDATE` ou un `DELETE` ? À quoi servent `BEGIN` et `ROLLBACK` ?

   > _Ma réponse :_ Sans `WHERE`, la requête s'applique à TOUTES les lignes : tous les clients s'appellent OUPS, ou tous sont supprimés. `BEGIN` démarre une transaction (les changements sont en attente) et `ROLLBACK` annule tout ce qui a été fait depuis le `BEGIN`, comme si rien ne s'était passé.

3. Pourquoi ne faut-il **jamais** supprimer des données avec une requête GET (un simple lien) ? (Indice : les moteurs de recherche et certains navigateurs « visitent » les liens à l'avance.)

   > _Ma réponse :_ Un lien peut être « visité » sans que l'utilisateur le veuille : moteurs de recherche, préchargement du navigateur, antivirus qui testent les liens… Ils supprimeraient des données. Une requête GET doit seulement lire ; les actions qui modifient passent par POST (formulaire).

4. Une fois un `id` supprimé, pourquoi est-il préférable qu'il ne soit jamais réattribué à un autre client ?

   > _Ma réponse :_ Sinon, un ancien lien, un favori ou une commande qui pointait vers l'ancien client désignerait par erreur le nouveau client. Grâce à `AUTOINCREMENT`, un id n'est jamais réutilisé, donc il identifie toujours la même personne.

---

## 🟣 Exercice 6 — Faire évoluer la base

1. Quelle est la différence entre le **schéma** d'une base et ses **données** ? Où se trouve chacun ?

   > _Ma réponse :_ Le schéma, c'est la structure (les tables, les colonnes, leurs types) : il est décrit dans `schema.sql` sur GitHub. Les données, ce sont les lignes enregistrées (les clients) : elles sont seulement dans `database.db`, sur le serveur PythonAnywhere.

2. Pourquoi ne faut-il pas relancer `create_db.py` sur une application en production ?

   > _Ma réponse :_ Parce qu'il commence par `DROP TABLE` : il efface toutes les tables et recrée une base avec les données d'exemple. Toutes les données saisies par les vrais utilisateurs seraient perdues.

3. Pourquoi est-il important de garder `schema.sql` à jour, même si on a modifié la base avec `ALTER TABLE` ?

   > _Ma réponse :_ Pour que le code et la base restent cohérents : si on doit recréer la base (nouveau serveur, collègue, tests), `schema.sql` doit donner exactement la même structure que la base du serveur. Sinon le code planterait sur une colonne manquante.

4. Pour ajouter **une** information, combien de fichiers avez-vous dû modifier ? Lesquels ?

   > _Ma réponse :_ Pour le téléphone : la base (`ALTER TABLE` + `schema.sql`), `formulaire.html`, `flask_app.py` (enregistrement et modification), `read_data.html` et `modifier_client.html`. Donc 5 à 6 fichiers pour une seule information : il faut modifier toute la chaîne.

---

## 🟣 Exercice 7 — Relier deux tables

1. Qu'est-ce qu'une **clé étrangère** ? Dans quelle table se trouve-t-elle ici, et pourquoi pas dans l'autre ?

   > _Ma réponse :_ C'est une colonne qui contient l'id d'une ligne d'une autre table, pour les relier. Ici c'est `client_id` dans la table `commandes` : une commande appartient à UN client, alors qu'un client peut avoir plusieurs commandes. On met donc le lien du côté « plusieurs » (on ne pourrait pas mettre toutes les commandes dans une seule colonne du client).

2. Pourquoi est-ce une mauvaise idée de créer des colonnes `commande1`, `commande2`… dans la table `clients` ?

   > _Ma réponse :_ On ne sait pas combien de commandes un client aura (3 ? 50 ?) : il faudrait sans cesse ajouter des colonnes, beaucoup resteraient vides, et ce serait très compliqué de chercher ou de compter les commandes. Une table à part gère n'importe quel nombre de commandes.

3. À quoi sert un `JOIN` ? Et un `GROUP BY` ?

   > _Ma réponse :_ `JOIN` assemble les lignes de deux tables qui sont liées (ex : chaque commande avec le nom de son client). `GROUP BY` regroupe les lignes qui ont la même valeur pour calculer quelque chose par groupe (ex : nombre de commandes et total par client avec `COUNT` et `SUM`).

4. Pour la bibliothèque, quelles tables imaginez-vous ? Lesquelles contiendront des clés étrangères ?

   > _Ma réponse :_ Trois tables : `livres`, `utilisateurs` et `emprunts`. C'est `emprunts` qui contient les clés étrangères : `livre_id` (vers `livres`) et `utilisateur_id` (vers `utilisateurs`), car un emprunt relie un livre et une personne.

---

## 🔴 Exercice 8 — Contrôle d'accès

1. Quelle est la différence entre **authentification** et **autorisation** ?

   > _Ma réponse :_ L'authentification vérifie QUI on est (login + mot de passe). L'autorisation vérifie CE QU'ON A LE DROIT de faire, selon son rôle (un `user` peut consulter, un `admin` peut aussi modifier et supprimer).

2. Où est stockée la session ? Comment le serveur sait-il qui vous êtes à chaque nouvelle requête ?

   > _Ma réponse :_ Dans un cookie `session` du navigateur, signé avec la `secret_key` du serveur. À chaque requête, le navigateur renvoie ce cookie : le serveur vérifie la signature et y lit qui on est et notre rôle.

3. Pourquoi masquer un bouton dans le HTML ne suffit-il pas à protéger une action ?

   > _Ma réponse :_ Parce qu'on peut quand même envoyer la requête à la main (recréer le bouton avec F12, utiliser `fetch` ou un autre outil). La vraie protection doit être sur le serveur, qui vérifie le rôle à chaque requête ; masquer le bouton ne sert qu'au confort.

4. Que signifient les codes `302` et `403` ? Dans quel cas votre application renvoie-t-elle chacun d'eux ?

   > _Ma réponse :_ `302` = redirection : quand on n'est pas connecté, l'application nous renvoie vers `/authentification` (et aussi après un enregistrement, vers la liste). `403` = accès interdit : on est connecté mais avec un rôle qui n'a pas le droit, par exemple un `user` qui essaie de supprimer un client.

5. Le mot de passe `password` est écrit en clair dans `flask_app.py`, sur un dépôt **public**. Quel est le risque ? Quelle solution avez-vous déjà rencontrée dans cet atelier pour cacher une information sensible ?

   > _Ma réponse :_ Tout le monde peut lire le dépôt public, donc n'importe qui pourrait se connecter en admin et tout supprimer. Solution déjà vue : les **secrets GitHub** (comme `PA_TOKEN`), ou des variables d'environnement. Et dans mon application, les mots de passe sont maintenant stockés **hachés** dans la table `utilisateurs`, plus en clair dans le code.

---

## 🔴 Exercice 9 — Créer une API

1. Quelle est la différence entre une page HTML et une réponse JSON ? À qui chacune est-elle destinée ?

   > _Ma réponse :_ Une page HTML est faite pour être affichée à un humain dans un navigateur (mise en page, liens, boutons). Une réponse JSON contient seulement les données brutes, structurées, faites pour être lues par un programme (application mobile, script, autre site, JavaScript).

2. Que signifient les codes `200`, `201`, `400`, `401` et `404` renvoyés par votre API ?

   > _Ma réponse :_ `200` : OK, la requête a réussi. `201` : créé, un nouveau client a été ajouté. `400` : requête incorrecte (champ obligatoire manquant). `401` : non authentifié, il faut être connecté en admin. `404` : la ressource demandée n'existe pas (client introuvable).

3. Pourquoi une API renvoie-t-elle une erreur JSON plutôt qu'une redirection vers la page de connexion ?

   > _Ma réponse :_ Parce qu'un programme ne sait pas quoi faire d'une page HTML de connexion : il attend du JSON. Avec une erreur JSON et un code (`401`), le programme comprend directement le problème et peut l'afficher ou demander à l'utilisateur de se connecter.

4. Citez une application de votre téléphone qui, selon vous, utilise une API. Quelles données échange-t-elle ?

   > _Ma réponse :_ Par exemple une application météo : elle envoie ma position à une API et reçoit en JSON la température, le ciel et les prévisions des prochains jours. Ou Spotify, qui récupère les titres, artistes et playlists via une API.

---

## 📚 Projet bibliothèque

1. Pourquoi ne supprime-t-on pas un emprunt quand le livre est rendu ?

   > _Ma réponse :_ Parce qu'on garde l'historique : on sait qui a emprunté quel livre et quand, on peut repérer les retards et faire des statistiques (livres les plus empruntés). On remplit juste `date_retour` : un emprunt avec `date_retour` vide est « en cours ».

2. Pourquoi calculer la disponibilité d'un livre plutôt que de la stocker dans une colonne ?

   > _Ma réponse :_ Parce qu'une colonne `nb_disponibles` modifiée à la main risque de devenir fausse (oubli de mise à jour, bug, deux emprunts en même temps). En la calculant à partir des emprunts en cours (`nb_exemplaires - COUNT(...)` avec `LEFT JOIN`), elle est toujours juste.

3. Quelle a été la plus grande difficulté rencontrée pendant le projet, et comment l'avez-vous surmontée ?

   > _Ma réponse :_ Faire évoluer la base du serveur sans perdre les données déjà saisies (téléphone, commandes, utilisateurs, livres). J'ai créé un dossier `migrations/` avec des scripts numérotés qui sont appliqués une seule fois au démarrage de l'application. Il fallait aussi bien gérer les règles R1 à R5 avec des messages clairs plutôt qu'une erreur 500.

4. Quelles fonctionnalités n'avez-vous pas eu le temps de réaliser ? Comment vous y prendriez-vous ?

   > _Ma réponse :_ La réservation d'un livre indisponible avec une notification à son retour, et les recommandations (« les lecteurs ont aussi emprunté… »). Pour la réservation, j'ajouterais une table `reservations` (livre_id, utilisateur_id, date) et, au retour d'un livre, je vérifierais s'il y a une réservation pour afficher une alerte à la personne. Pour les recommandations, une requête qui cherche les autres livres empruntés par les lecteurs de ce livre (`JOIN` + `GROUP BY` + `ORDER BY COUNT`).

---

## 🏁 Pour conclure

En quelques phrases, expliquez à un ami ce qui se passe entre le moment où il clique sur « Enregistrer » dans un formulaire et celui où l'information s'affiche dans une liste :

> _Ma réponse :_ Quand tu cliques sur « Enregistrer », ton navigateur envoie les champs du formulaire au serveur dans une requête POST. Flask reçoit la requête, vérifie que tu as le droit et que les champs sont bien remplis, puis lance une requête SQL `INSERT` (avec des `?` pour éviter les injections) et fait `commit()` pour l'enregistrer dans la base SQLite. Ensuite il te redirige vers la liste : ton navigateur demande la page, Flask fait un `SELECT`, met les lignes dans le template HTML et te renvoie la page, où ta nouvelle ligne apparaît.
