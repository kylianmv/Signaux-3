import os
import numpy as np
import matplotlib.pyplot as plt
from Signaux_3_Lune import analyser_lune

# Dans datasetLune, moon.7489.png correspond à la Nouvelle Lune (Jour 0)
FRAME_NOUVELLE_LUNE = 7489
CYCLE = 29.53

erreurs = []
jours_reels = []
jours_predits = []

for frame in range(7297, 8018, 24):
    chemin = f"datasetLune/moon.{frame}.png"
    if os.path.exists(chemin):
        # Vérité terrain (jour réel entre 0 et 29.53)
        jour_reel = ((frame - FRAME_NOUVELLE_LUNE) / 24.0) % CYCLE

        # Prédiction de ton script (sans ouvrir 31 fenêtres)
        resultat = analyser_lune(chemin, afficher=False)
        jour_predit = resultat[0] if isinstance(resultat, tuple) else resultat["jour_lunaire"]

        # Différence circulaire (gère le passage Jour 29.5 -> Jour 0)
        diff = abs(jour_predit - jour_reel)
        diff = min(diff, CYCLE - diff)

        erreurs.append(diff)
        jours_reels.append(jour_reel)
        jours_predits.append(jour_predit)

erreur_moyenne = np.mean(erreurs)
print(f"Erreur absolue moyenne sur {len(erreurs)} images : {erreur_moyenne:.2f} jours")

# Génération de la Figure 2 pour le poster
plt.figure(figsize=(8, 5))
plt.plot([0, 29.5], [0, 29.5], 'k--', label='Prédiction parfaite (y = x)')
plt.scatter(jours_reels, jours_predits, color='#D97706', s=60, zorder=5, label='Prédictions script')
plt.title(f"Validation sur cycle lunaire (Erreur moyenne : {erreur_moyenne:.2f} jours)")
plt.xlabel("Jour lunaire réel (vérité terrain)")
plt.ylabel("Jour lunaire prédit par l'algorithme")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("figure2_validation.png", dpi=300)
plt.show()