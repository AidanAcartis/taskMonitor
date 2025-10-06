import mimetypes

# types_map contient {'.ext': 'type/mime'}
for ext, mime in mimetypes.types_map.items():
    print(f"{ext} -> {mime}")

# Pour compter combien d'extensions connues
print(f"\nNombre d'extensions connues : {len(mimetypes.types_map)}")
