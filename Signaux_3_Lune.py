import skimage as skim
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
from scipy.io.wavfile import read

def analyser_lune(image_path, hemisphere="N", afficher=True):
    # 1. Chargement de l'image et conversion en niveaux de gris [0, 1]
    img = skim.io.imread(image_path)
    if img.ndim == 3:
        # Gestion RGBA éventuelle (on garde uniquement RGB)
        gris = skim.color.rgb2gray(img[:, :, :3])
    else:
        gris = skim.img_as_float(img)

    # 2. Prétraitement : filtrage passe-bas 2D (noyau gaussien) via scipy.signal
    taille_noyau = 9
    sigma = 2.0
    ax = np.linspace(-(taille_noyau - 1) / 2., (taille_noyau - 1) / 2., taille_noyau)
    gauss_1d = np.exp(-0.5 * np.square(ax) / np.square(sigma))
    noyau_2d = np.outer(gauss_1d, gauss_1d)
    noyau_2d /= np.sum(noyau_2d)

    flou = signal.convolve2d(gris, noyau_2d, mode="same", boundary="symm")

    # 3. Segmentation (Seuillage d'Otsu + Morphologie mathématique)
    seuil = skim.filters.threshold_otsu(flou)
    masque = flou > seuil

    # Fermeture (comble les mers lunaires sombres) puis ouverture (supprime le bruit/étoiles)
    element_structurant = skim.morphology.disk(5)
    masque = skim.morphology.closing(masque, element_structurant)
    masque = skim.morphology.opening(masque, element_structurant)

    # 4. Extraction de la composante connexe principale (la Lune)
    labels = skim.measure.label(masque)
    regions = skim.measure.regionprops(labels)

    if not regions:
        return {"erreur": "Aucune lune détectée (Nouvelle lune ou nuages)"}

    # On garde la région avec la plus grande aire (en pixels)
    lune = max(regions, key=lambda r: r.area)
    aire_illuminee = lune.area

    # Coordonnées des pixels appartenant à la lune (y = ligne, x = colonne)
    coords = lune.coords
    yb, xb = lune.centroid  # Barycentre (centre de masse des pixels éclairés)

    # 5. Estimation du cercle complet de la Lune
    # Sur un disque ou un croissant > 180°, le diamètre maximal (feret_diameter_max)
    # correspond au diamètre réel D de la pleine lune.
    diametre = lune.feret_diameter_max
    rayon = diametre / 2.0
    aire_totale = np.pi * (rayon ** 2)

    if aire_totale == 0:
        return {"erreur": "Rayon nul détecté"}

    # Fraction illuminée k dans [0, 1]
    k = min(aire_illuminee / aire_totale, 1.0)

    # Estimation du centre géométrique (xc, yc) du disque complet
    # Le vecteur (barycentre - centre_cercle) pointe vers la zone éclairée
    y_min, x_min, y_max, x_max = lune.bbox
    xc_bbox = (x_min + x_max) / 2.0
    yc_bbox = (y_min + y_max) / 2.0

    # Dans l'hémisphère Nord, lumière à droite (xb >= xc_bbox) = lune croissante
    est_croissante = (xb >= xc_bbox) if hemisphere == "N" else (xb < xc_bbox)

    # 6. Déduction de l'angle de phase et du jour lunaire (cycle synodique = 29.53 jours)
    # Formule astronomique : k = (1 - cos(theta)) / 2  =>  theta = arccos(1 - 2k)
    theta = np.arccos(np.clip(1.0 - 2.0 * k, -1.0, 1.0))  # radians [0, pi]
    cycle = 29.53

    if est_croissante:
        jour_lunaire = (theta / np.pi) * (cycle / 2.0)
        xc_cercle = x_max - rayon  # Le bord droit est le limbe circulaire
    else:
        jour_lunaire = cycle - (theta / np.pi) * (cycle / 2.0)
        xc_cercle = x_min + rayon  # Le bord gauche est le limbe circulaire
    yc_cercle = (y_min + y_max) / 2.0

    # Identification de la phase principale
    if jour_lunaire < 1.5 or jour_lunaire > 28.0:
        phase = "Nouvelle lune"
    elif 1.5 <= jour_lunaire < 6.0:
        phase = "Premier croissant"
    elif 6.0 <= jour_lunaire <= 8.8:
        phase = "Premier quartier"
    elif 8.8 < jour_lunaire < 13.5:
        phase = "Gibbeuse croissante"
    elif 13.5 <= jour_lunaire <= 16.0:
        phase = "Pleine lune"
    elif 16.0 < jour_lunaire < 20.8:
        phase = "Gibbeuse décroissante"
    elif 20.8 <= jour_lunaire <= 23.5:
        phase = "Dernier quartier"
    else:
        phase = "Dernier croissant"

    # 7. Affichage Matplotlib (idéal pour exporter les figures du poster A1)
    if afficher:
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))
        
        axes[0].imshow(img)
        axes[0].set_title("1. Image originale")
        axes[0].axis("off")

        axes[1].imshow(masque, cmap="gray")
        axes[1].set_title(f"2. Masque segmenté (Otsu={seuil:.2f})")
        axes[1].axis("off")

        axes[2].imshow(img)
        # Tracé du contour détecté
        contours = skim.measure.find_contours(masque, 0.5)
        for c in contours:
            axes[2].plot(c[:, 1], c[:, 0], color="lime", linewidth=2, label="Contour")
        # Tracé du cercle théorique complet
        cercle = plt.Circle((xc_cercle, yc_cercle), rayon, color="cyan", fill=False, linewidth=2, linestyle="--", label="Disque théorique")
        axes[2].add_patch(cercle)
        # Barycentre vs Centre
        axes[2].scatter([xb], [yb], color="red", s=50, zorder=5, label="Barycentre")
        axes[2].scatter([xc_cercle], [yc_cercle], color="cyan", s=50, zorder=5, label="Centre disque")
        axes[2].set_title(f"3. Jour {jour_lunaire:.1f} — {phase}\n(Illumination : {k*100:.1f}%)")
        axes[2].axis("off")

        plt.tight_layout()
        plt.show()

    return {
        "jour_lunaire": round(float(jour_lunaire), 1),
        "phase": phase,
        "illumination_pct": round(float(k * 100), 1),
        "masque": masque
    }

# --- Exemple d'exécution ---
# resultat = analyser_lune("dataset_nasa/jour_07.jpg")
# print(resultat)