import os
import json
import pandas as pd
import folium
import webbrowser
from pymongo import MongoClient

# === 1. EXTRACTION ET TRANSFORMATION === #
def extract_transform(filepath):
    # Lire un fichier Excel et le convertir en DataFrame pandas
    df = pd.read_excel(filepath)

    # Normaliser les noms des colonnes : enlever espaces, mettre en minuscules et remplacer espaces par _
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

    # Renommer certaines colonnes pour simplifier leur accès dans le code
    df = df.rename(columns={
        'secteurs_géographiques': 'quartier',
        'nombre_de_pièces_principales': 'pieces',
        'loyers_de_référence': 'loyer',
        'type_de_location': 'type_location',
        'geo_point_2d': 'coordonnees'
    })

    # Garder uniquement les lignes où la colonne 'coordonnees' n'est pas vide et contient une virgule (latitude,longitude)
    df = df[df['coordonnees'].notna() & df['coordonnees'].str.contains(',')]

    # Séparer la colonne 'coordonnees' en deux colonnes : 'latitude' et 'longitude'
    df[['latitude', 'longitude']] = df['coordonnees'].str.split(',', expand=True)
    # Convertir les colonnes latitude et longitude en nombres décimaux, sinon NaN si erreur
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    # Convertir la colonne 'loyer' en numérique, pour pouvoir faire des calculs dessus
    df['loyer'] = pd.to_numeric(df['loyer'], errors='coerce')

    # Garder uniquement les colonnes nécessaires et supprimer les lignes avec valeurs manquantes
    df = df[['quartier', 'pieces', 'loyer', 'latitude', 'longitude', 'type_location']].dropna()

    return df  # Retourner le dataframe nettoyé et prêt à être utilisé

# === 2. CHARGEMENT DANS MONGODB === #
def load_to_mongo(df, uri="mongodb://localhost:27017/", db="loyers", collection="paris_2024"):
    client = MongoClient(uri)  # Se connecter à MongoDB via l'URI donné
    col = client[db][collection]  # Accéder à la base de données et à la collection ciblée
    col.delete_many({})  # Supprimer toutes les données existantes dans la collection (nettoyage)
    col.insert_many(df.to_dict(orient="records"))  # Insérer les données du dataframe en tant que documents JSON
    print(f"✅ {len(df)} documents insérés dans MongoDB ({collection})")  # Confirmation en console

# === 3. AFFICHAGE INTERACTIF AVEC FOLIUM === #
def create_map(df, filename="carte_loyers_2024.html"):
    # Initialiser une carte centrée sur Paris avec un zoom de départ à 12
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)

    # Convertir le dataframe en liste de dictionnaires (format JSON)
    data = df.to_dict(orient="records")
    data_json = json.dumps(data)  # Convertir en JSON string pour injecter dans le JS

    # Trouver les valeurs minimale et maximale du loyer pour la colorisation
    loyer_min, loyer_max = df['loyer'].min(), df['loyer'].max()

    # Code HTML qui crée une interface de filtres (sélecteurs et bouton) sur la carte
    filter_html = """
    <div id="filter-container" style="position: fixed; top: 10px; left: 50px; z-index:9999;
        background:white; padding:10px; border-radius:5px; box-shadow:0 2px 6px rgba(0,0,0,0.3); min-width: 260px;">
        <label><b>Pièces :</b></label><br>
        <select id="pieces-select" style="width:100%; margin-bottom:10px;"><option value="all">all</option></select>
        <label><b>Type :</b></label><br>
        <select id="type-select" style="width:100%; margin-bottom:10px;"><option value="all">all</option></select>
        <button id="reset-btn" style="width:100%;">Réinitialiser</button>
        <p id="no-results" style="color:red; font-weight:bold; display:none; margin-top:10px;">Aucun logement trouvé.</p>
    </div>
    """
    # Ajouter ce bloc HTML à la carte (pour afficher les filtres)
    m.get_root().html.add_child(folium.Element(filter_html))

    # Script JavaScript injecté dans la carte pour gérer les filtres et l'affichage dynamique
    js_script = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const data = {data_json}, loyerMin = {loyer_min}, loyerMax = {loyer_max};
        const map = {m.get_name()}, layer = L.layerGroup().addTo(map);
        const selPieces = document.getElementById('pieces-select'), selType = document.getElementById('type-select');
        const noResults = document.getElementById('no-results'), resetBtn = document.getElementById('reset-btn');

        // Remplir les filtres avec les options uniques des pièces et types de location
        [...new Set(data.map(d => d.pieces))].sort().forEach(p => selPieces.add(new Option(p, p)));
        [...new Set(data.map(d => d.type_location))].sort().forEach(t => selType.add(new Option(t, t)));

        // Fonction pour calculer la couleur en fonction du loyer (dégradé rouge/vert)
        const color = loyer => {{
            const ratio = (loyer - loyerMin) / (loyerMax - loyerMin);
            return `rgb(${{Math.floor(255 * ratio)}}, ${{Math.floor(255 * (1 - ratio))}}, 0)`;
        }};

        // Ajout de la légende de couleur
        const legend = L.control({{position: 'topright'}});
        legend.onAdd = function (map) {{
            const div = L.DomUtil.create('div', 'info legend');
            div.innerHTML = `
                <h4>Légende des loyers</h4>
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="background: rgb(255, 0, 0); width: 20px; height: 20px; margin-right: 5px;"></div>
                    <span>Loyer élevé</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="background: rgb(0, 255, 0); width: 20px; height: 20px; margin-right: 5px;"></div>
                    <span>Loyer bas</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="background: rgb(255, 255, 0); width: 20px; height: 20px; margin-right: 5px;"></div>
                    <span>Loyer moyen</span>
                </div>
            `;
            return div;
        }};

        legend.addTo(map);

        // Fonction pour mettre à jour les marqueurs selon les filtres sélectionnés
        function updateMarkers(pf, tf) {{
            layer.clearLayers();  // Supprimer les anciens marqueurs
            // Filtrer les données selon les critères sélectionnés (ou 'all' pour tout afficher)
            const filtered = data.filter(d => (pf == 'all' || d.pieces == pf) && (tf == 'all' || d.type_location == tf));

            // Afficher un message si aucun logement ne correspond
            noResults.style.display = filtered.length ? 'none' : 'block';

            // Ajouter un cercle sur la carte pour chaque logement filtré, avec une couleur selon le loyer
            filtered.forEach(d => {{
                if (!isNaN(d.latitude) && !isNaN(d.longitude)) {{
                    L.circleMarker([d.latitude, d.longitude], {{
                        radius: 6, color: color(d.loyer), fillColor: color(d.loyer), fillOpacity: 0.8
                    }}).bindPopup(`<b>${{d.quartier}}</b><br>Pièces: ${{d.pieces}}<br>Type: ${{d.type_location}}<br>Loyer: ${{d.loyer}} €/m²`).addTo(layer);
                }}
            }});
        }}

        // Mettre à jour les marqueurs à chaque changement dans les filtres
        selPieces.onchange = () => updateMarkers(selPieces.value, selType.value);
        selType.onchange = () => updateMarkers(selPieces.value, selType.value);

        // Bouton pour réinitialiser les filtres et afficher toutes les données
        resetBtn.onclick = () => {{
            selPieces.value = selType.value = 'all';
            updateMarkers('all', 'all');
        }};

        // Afficher tous les marqueurs au chargement
        updateMarkers('all', 'all');
    }});
    </script>
    """
    # Injecter le script JS dans la carte
    m.get_root().html.add_child(folium.Element(js_script))

    # Enregistrer la carte sous forme de fichier HTML
    m.save(filename)
    # Ouvrir automatiquement la carte dans le navigateur
    webbrowser.open(f'file:///{os.path.abspath(filename).replace(os.sep, "/")}')
    print(f"✅ Carte générée : {filename}")

# === 4. PIPELINE PRINCIPAL === #
if __name__ == '__main__':
    filepath = r"C:\Users\Mkoma\OneDrive\Bureau\etl_loyer_paris\logement-encadrement-des-loyers.xlsx"
    df = extract_transform(filepath)  # Extraire et transformer les données depuis Excel
    load_to_mongo(df)  # Charger les données dans MongoDB
    create_map(df)  # Créer et afficher la carte interactive
