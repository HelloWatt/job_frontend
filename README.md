# Test technique front-end, Hello Watt

Vous cherchez un job/stage ? Découvrez [nos offres d'emplois](https://hello-watt.welcomekit.co/).

## Votre mission

Construire un **dashboard de diagnostic électrique en un clic**.

Un conseiller Hello Watt doit pouvoir, en quelques secondes :

1. **Trouver un client** par son nom ou son identifiant.
2. **Voir sa courbe de consommation** sur les 12 derniers mois et sur les
   années précédentes.
3. **Lire son diagnostic** : identifiant, nom, chauffage électrique ou non, et
   dysfonctionnement éventuel sur l'installation.

Et, côté staff :

4. **Parcourir la liste des clients** sur `/admin/clients`, pour repérer d'un coup d'œil
  ceux qui ont un chauffage électrique ou un dysfonctionnement.

Le back-end est déjà écrit : les modèles, la base de données peuplée, le calcul du
diagnostic et l'API sont fournis.

Deux templates sont volontairement vides, ce sont les vôtres :

- `dashboard/templates/dashboard/index.html`, la page d'accueil `/`
- `dashboard/templates/dashboard/clients_list.html`, la liste staff `/admin/clients`

Chacun contient un `TODO` décrivant les données déjà disponibles dans le contexte.

### Contraintes

- **Une partie de nos utilisateurs est sur mobile.** Le dashboard doit être utilisable
  sur un téléphone.
- **En production la base contient des centaines de milliers de clients.**
- Pas besoin d'authentification ni d'autorisation : pour l'exercice, n'importe qui peut
  consulter le dashboard de n'importe qui.

Vous êtes libre de changer complètement l'application. Impressionnez-nous !

## Mise en place

Le projet Django vit dans le dossier `hwjob/`. **Toutes les commandes ci-dessous se
lancent depuis `hwjob/`.**

```bash
cd hwjob
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

Le site est alors sur http://127.0.0.1:8000

- **Python 3.14**
- **Django 5.2**
- La base `hwjob/db.sqlite3` est versionnée et **déjà peuplée**

### Interface d'administration

```bash
python manage.py createsuperuser
```

- `/admin/` l'admin Django sur les clients, les consommations et les prix, pour
  explorer les données brutes.
- `/admin/clients` la liste staff **à construire**. La vue
  (`dashboard/sites.py`, `ClientsListView`) fournit déjà la pagination, la recherche et
  le diagnostic de chaque client ; il manque le template.

## Les données

5000 clients, une mesure de consommation par mois et par client, **de mars 2018 à
août 2026**, plus le prix de l'électricité sur la même période.

Le diagnostic est calculé par le back-end, vous n'avez pas à le recalculer :

| Champ | Signification |
| --- | --- |
| `has_elec_heating` | La consommation des mois froids est disproportionnée par rapport aux mois chauds, signe d'un chauffage électrique. |
| `has_anomaly` | Un mois consomme beaucoup plus que le même mois un an plus tôt : l'installation a un dysfonctionnement durable. |
| `anomaly_date` | Le premier mois anormal (`null` s'il n'y a pas d'anomalie). |

## L'API

### `GET /api/search-clients`

Recherche paginée, 10 clients par page.

| Paramètre | Défaut | Rôle |
| --- | --- | --- |
| `query` |, | Identifiant exact, ou fragment de nom (insensible à la casse). |
| `page` | `1` | Numéro de page. |

(10 clients par page, les 3 premiers sont montrés ici.)

### `GET /api/client/<client_id>`

Le détail d'un client, son diagnostic et sa série de consommations.

| Paramètre | Défaut | Rôle |
| --- | --- | --- |
| `year` |, | `2025` pour une année précise, `all` pour tout l'historique, absent pour les **12 derniers mois**. |

## Deux façons de récupérer les données, à vous de choisir

Les deux sont acceptées. Choisissez celle qui
sert votre architecture, et dites-nous pourquoi dans la section
[Vos choix](#vos-choix).

**1. Consommer l'API en JavaScript**, pour une page qui réagit sans rechargement
(recherche au fil de la frappe, changement d'année sans reload), avec React, Vue,
Svelte ou du JS natif.

**2. Embarquer les données dans le template**, pour un rendu serveur, sans requête
supplémentaire au chargement. Les mêmes fonctions que l'API alimentent le contexte django.

## Librairies à votre disposition

Vous êtes libre d'ajouter ce que vous voulez : React, Vue, Svelte, Tailwind, Bootstrap,
sass, Chart.js, D3, un bundler… Si vous ajoutez des dépendances Python, mettez à jour
`requirements.txt`.

## Lancer le projet

> **À compléter si nécessaire.** Si votre rendu demande plus que
> `pip install -r requirements.txt` puis `python manage.py runserver`, un `npm install`,
> un build, une variable d'environnement, décrivez ici les commandes exactes, dans
> l'ordre, pour partir d'un dépôt fraîchement cloné.

## Vos choix

> **À compléter.** Quelques lignes suffisent : ce que vous avez choisi et pourquoi, ce
> que vous auriez fait avec plus de temps, ce que vous avez laissé de côté volontairement.
> Cette section compte autant que le code.

## Une fois terminé

Contactez votre correspondant chez Hello Watt, et envoyez votre rendu :

- soit un lien vers un dépôt Git **privé**, partagé uniquement avec votre correspondant ;
- soit un zip du projet, **dossier `.git` inclus**, nous voulons voir l'historique, donc
  commitez régulièrement plutôt qu'en un seul bloc à la fin.
