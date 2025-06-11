# 🏙️ Loyers Interactive - Projet ETL & Data Visualisation

Ce projet a pour objectif de construire un pipeline ETL (Extract, Transform, Load) permettant d'analyser les loyers en France à travers des données fiables et interactives. Le tout est présenté sous forme de tableaux de bord visuels et interactifs.

---

## 📌 Objectifs du projet

- Extraire les données brutes liées aux loyers
- Les nettoyer, transformer et structurer
- Charger les données dans un format exploitable
- Visualiser les résultats de manière interactive via des dashboards

---

## 🛠️ Technologies utilisées

- Python
- Pandas, NumPy
- Jupyter Notebook
- Power BI / Tableau / Streamlit (à adapter selon ton outil)
- Matplotlib / Seaborn
- Git / GitHub

---

## 📁 Structure du projet


loyers-interactive/
│
├── data/ # Données sources (anonymisées si nécessaire)
├── notebooks/ # Jupyter Notebooks du pipeline ETL
├── src/ # Scripts Python (fonctions ETL, helpers, etc.)
├── output/ # Graphiques, dashboards, résultats finaux
├── screenshots/ # Captures d’écran des visualisations
├── requirements.txt # Librairies nécessaires
└── README.md # Ce fichier de description


---

## 🧪 Exemple de pipeline ETL

1. **Extraction** : données récupérées depuis [Nom de la source] (CSV, API, etc.)
2. **Transformation** : nettoyage, traitement des valeurs manquantes, standardisation
3. **Chargement** : enregistrement dans un fichier CSV/Excel ou base de données

---

## 📊 Résultats visuels

### Dashboard interactif

![Dashboard principal](./screenshots/carte-interactive.png)

### Carte des loyers par région

![Carte des loyers](./screenshots/carte-avec-filtre.png)

---

## 🔧 Installation

Pour exécuter le projet localement :

```bash
git clone https://github.com/TON-USERNAME/loyers-interactive.git
cd loyers-interactive
pip install -r requirements.txt

