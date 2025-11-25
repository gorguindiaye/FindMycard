import os
import json

# ---------------- Initialisation Django ----------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findmyid.settings')
import django
django.setup()

# ---------------- Import OCR Service ----------------
from ocr.services import OCRService

# ---------------- Paramètres des tests ----------------
test_images = [
    r"C:/Users/Administrator/Desktop/FindMyCard/images/Carte.jpg",
    r"C:/Users/Administrator/Desktop/FindMyCard/images/CNI1.jpg",
    # r"C:/Users/Administrator/Desktop/FindMyCard/images/Passport1.jpg"  # exemple pour passport
]

# Ground-truth pour comparaison
ground_truth = {
    "Carte.jpg": {
        "nom": "NDIAYE",
        "prenom": "GORGUI",
        "date_naissance": "01/01/2003",
        "numero_doc": "CNI123456",
        "date_expiration": "01/01/2030",
        "sexe": "M",
        "nationalite": "SENEGAL",
        "lieu_naissance": "DAKAR",
        "photo_present": "OUI"
    },
    # Ajouter d'autres ground-truth si nécessaire
}

# Type de document à tester pour chaque image
doc_types = {
    "Carte.jpg": "cni",
    "CNI1.jpg": "cni",
    # "Passport1.jpg": "passport"
}

# ---------------- Fonction utilitaire ----------------
def compare_results(result, expected):
    """
    Compare le résultat OCR avec le ground-truth
    Retourne True si tout correspond, sinon liste des champs incorrects
    """
    if not expected or not result.get("success"):
        return False, "Pas de ground-truth ou OCR échoué"

    mismatches = {}
    for key, val in expected.items():
        if key not in result or result[key] != val:
            mismatches[key] = {
                "attendu": val,
                "obtenu": result.get(key)
            }
    if mismatches:
        return False, mismatches
    return True, None

# ---------------- Tests ----------------
summary = []

for img_path in test_images:
    img_name = os.path.basename(img_path)
    print(f"\n=== Test OCRService sur {img_path} ===")

    if not os.path.exists(img_path):
        print(f"❌ Image non trouvée : {img_path}")
        summary.append((img_name, "Image non trouvée"))
        continue

    # Type de document forcé
    doc_type = doc_types.get(img_name, None)
    if doc_type is None:
        print(f"⚠ Type de document non défini pour {img_name}")
        summary.append((img_name, "Type de document non défini"))
        continue

    # Ground-truth si disponible
    expected = ground_truth.get(img_name, None)

    # Appel au service OCR
    result = OCRService.process_image(
        img_path,
        expected=expected,
        doc_type=doc_type
    )

    # Affichage formaté
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Comparaison avec ground-truth
    ok, details = compare_results(result, expected)
    if ok:
        summary.append((img_name, "✅ Tous les champs corrects"))
    else:
        summary.append((img_name, f"❌ Erreurs : {details}"))

# ---------------- Résumé final ----------------
print("\n=== Résumé final ===")
for img_name, status in summary:
    print(f"{img_name} : {status}")

print("\n=== Test OCR terminé ===")
