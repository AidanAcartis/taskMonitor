# La chaîne d'entrée
input_string = "This Game - OP Full - No Game No Life by Konomi Suzuki (Lyrics).mp4 - VLC media player"

# On cherche le dernier point '.' dans la chaîne
dot_index = input_string.rfind('.')

if dot_index != -1:
    # Diviser la chaîne en deux parties : avant le point et après
    chaine1 = input_string[:dot_index]
    chaine2 = input_string[dot_index+1:]
    
    # Garder uniquement la première partie de la chaîne après le point (l'extension)
    chaine2 = chaine2.split()[0]  # Pour extraire juste l'extension sans les espaces
    
    # Combiner les deux parties
    result = chaine1 + '.' + chaine2
else:
    # Si aucun point n'est trouvé, retourner la chaîne telle quelle
    result = input_string

# Afficher le résultat
print(result)
