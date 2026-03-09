import subprocess

def convertir_mp4_en_mp3(fichier_mp4, fichier_mp3):
    try:
        # Commande FFmpeg pour extraire l'audio et le convertir en MP3
        commande = [
            "ffmpeg",
            "-i", fichier_mp4,  # Fichier source
            "-q:a", "0",        # Qualité audio (0 est la meilleure)
            "-map", "a",        # Extraire uniquement l'audio
            fichier_mp3         # Fichier de sortie
        ]
        
        # Exécuter la commande
        subprocess.run(commande, check=True)
        
        print(f"Conversion réussie ! Fichier enregistré sous : {fichier_mp3}")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la conversion : {e}")
    except FileNotFoundError:
        print("FFmpeg n'est pas installé ou introuvable. Assurez-vous qu'il est dans le PATH.")

# Exemple d'utilisation
fichier_entree = "song.mp4"  # Chemin vers le fichier .mp4
fichier_sortie = "audio.mp3"  # Chemin souhaité pour le fichier .mp3

convertir_mp4_en_mp3(fichier_entree, fichier_sortie)
