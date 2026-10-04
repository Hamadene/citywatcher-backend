import time
import requests

# Ce script simule un camion qui se déplace le long d'un trajet.
# Il envoie sa position au backend toutes les 2 secondes.
# À l'étape 7 (production), tu remplaceras ce script par le vrai flux GPS
# de ta commune — le reste de l'architecture ne changera pas.

BASE_URL = "http://127.0.0.1:8000"

# Trajet simulé : une liste de coordonnées GPS (latitude, longitude)
# Ici c'est un trajet fictif — remplace par de vraies rues de ta ville plus tard
TRAJET = [
    (48.8566, 2.3522),   # Point de départ
    (48.8570, 2.3530),
    (48.8575, 2.3540),
    (48.8580, 2.3550),
    (48.8585, 2.3560),
    (48.8590, 2.3570),
    (48.8595, 2.3580),
    (48.8600, 2.3590),
    (48.8605, 2.3600),
    (48.8610, 2.3610),   # Point d'arrivée
]

def simuler_camion():
    print("🚛 Simulateur de camion démarré...")
    print(f"   Trajet : {len(TRAJET)} points GPS")
    print(f"   Intervalle : 2 secondes entre chaque position\n")

    for i, (lat, lng) in enumerate(TRAJET):
        try:
            response = requests.post(
                f"{BASE_URL}/camion/position",
                json={"latitude": lat, "longitude": lng}
            )
            if response.status_code == 200:
                print(f"📍 Position {i+1}/{len(TRAJET)} envoyée → lat: {lat}, lng: {lng}")
            else:
                print(f"❌ Erreur {response.status_code} à la position {i+1}")
        except Exception as e:
            print(f"❌ Impossible de joindre le backend : {e}")

        time.sleep(2)  # Attendre 2 secondes avant la prochaine position

    print("\n✅ Trajet terminé !")

if __name__ == "__main__":
    simuler_camion()
