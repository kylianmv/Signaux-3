import os
import urllib.request

os.makedirs("dataset_nasa", exist_ok=True)

# Frame 7496 = 9 novembre 2026 à 07:00 UTC (Nouvelle Lune exacte)
# Chaque frame suivante ajoute 1 heure -> +24 frames = +1 jour lunaire
FRAME_NOUVELLE_LUNE = 7496
BASE_URL = "https://svs.gsfc.nasa.gov/vis/a000000/a005500/a005587/frames/730x730_1x1_30p/moon.{:04d}.jpg"

for jour in range(30):
    frame = FRAME_NOUVELLE_LUNE + (jour * 24)
    url = BASE_URL.format(frame)
    destination = f"dataset_nasa/jour_{jour:02d}.jpg"
    
    print(f"Téléchargement {destination} (frame {frame})...")
    urllib.request.urlretrieve(url, destination)

print("Terminé : 30 images prêtes dans ./dataset_nasa/")