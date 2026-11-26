import skimage as skim
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt

def analyser_lune(image_path, hemisphere="N"):
    # 1. Lecture de l'image comme dans le labo
    I = plt.imread(image_path).astype(float)
    # Si l'image est en couleur (RGB/RGBA), on passe en niveaux de gris 2D
    if I.ndim == 3:
        I = np.mean(I[:, :, :3], axis=2)

    # 2. Filtrage passe-bas par matrice de convolution 2D (lissage du bruit/étoiles)
    h_LP = np.array([
        [1, 2, 1],
        [2, 4, 2],
        [1, 2, 1]
    ], dtype=float) / 16.0
    I_flou = signal.convolve2d(I, h_LP, mode='same')

    # 3. Détection des bords avec Sobel (comme dans le labo) + segmentation
    I_sobel = skim.filters.sobel(I_flou)
    seuil = skim.filters.threshold_otsu(I_flou)
    masque = I_flou > seuil

    # Nettoyage morphologique pour garder un disque/croissant plein
    noyau = skim.morphology.disk(5)
    masque = skim.morphology.closing(masque, noyau)
    masque = skim.morphology.opening(masque, noyau)

    # 4. Extraction de la Lune (plus grande région connectée)
    labels = skim.measure.label(masque)
    regions = skim.measure.regionprops(labels)
    if not regions:
        print("Aucune lune détectée.")
        return None

    lune = max(regions, key=lambda r: r.area)
    aire_illuminee = lune.area
    yb, xb = lune.centroid

    # 5. Calcul du cercle complet et du pourcentage illuminé k
    diametre = lune.feret_diameter_max
    rayon = diametre / 2.0
    aire_totale = np.pi * (rayon ** 2)
    k = min(aire_illuminee / aire_totale, 1.0)

    # Orientation (hémisphère Nord : lumière à droite = croissante)
    y_min, x_min, y_max, x_max = lune.bbox
    xc_bbox = (x_min + x_max) / 2.0
    est_croissante = (xb >= xc_bbox) if hemisphere == "N" else (xb < xc_bbox)

    # 6. Déduction du jour lunaire (cycle de 29.53 jours)
    theta = np.arccos(np.clip(1.0 - 2.0 * k, -1.0, 1.0))
    cycle = 29.53
    if est_croissante:
        jour_lunaire = (theta / np.pi) * (cycle / 2.0)
        xc_cercle = x_max - rayon
    else:
        jour_lunaire = cycle - (theta / np.pi) * (cycle / 2.0)
        xc_cercle = x_min + rayon
    yc_cercle = (y_min + y_max) / 2.0

    # Détermination de la phase
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

    # 7. Affichage en subplots (style du labo)
    plt.figure(figsize=(10, 10))

    plt.subplot(2, 2, 1)
    plt.title('1. Image de base')
    plt.imshow(I, cmap='gray')

    plt.subplot(2, 2, 2)
    plt.title('2. Bords (Sobel)')
    plt.imshow(I_sobel, cmap='gray')

    plt.subplot(2, 2, 3)
    plt.title('3. Masque segmenté (Otsu)')
    plt.imshow(masque, cmap='gray')

    plt.subplot(2, 2, 4)
    plt.title(f'4. Jour {jour_lunaire:.1f} - {phase} ({k*100:.1f}%)')
    plt.imshow(I, cmap='gray')
    ax = plt.gca()
    ax.add_patch(plt.Circle((xc_cercle, yc_cercle), rayon, color='cyan', fill=False, linewidth=2, linestyle='--'))
    plt.scatter([xb], [yb], color='red', s=40)

    plt.tight_layout()
    plt.show()

    return round(float(jour_lunaire), 1), phase

# --- Exécution sur une image précise ---
jour, phase = analyser_lune('dataset_nasa/jour_07.jpg')
print(f"Résultat : Jour {jour} ({phase})")