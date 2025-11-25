#!/usr/bin/env python3
"""
Test comparatif entre extraction basée sur règles et extraction DL.
"""
import os
import json
import time
from ocr.services import OCRService, extract_fields_by_type, ocr_extract, preprocess_image
from ocr.dl_extractor import DLFieldExtractor

def test_dl_vs_rules(image_path, doc_type="cni_cedeao"):
    """Compare extraction règles vs DL sur une image."""
    print(f"\n=== Test sur {image_path} ===")

    if not os.path.exists(image_path):
        print("Image non trouvée")
        return

    # Prétraitement et OCR
    img = preprocess_image(image_path)
    ocr_results = ocr_extract(img)
    all_text = " ".join([text for _, text in ocr_results])
    print(f"Texte OCR: {all_text[:200]}...")

    # Extraction par règles
    start_time = time.time()
    fields_rules = extract_fields_by_type(ocr_results, doc_type)
    time_rules = time.time() - start_time

    # Extraction par DL
    extractor = DLFieldExtractor()
    start_time = time.time()
    fields_dl = extractor.extract_fields(ocr_results, doc_type)
    time_dl = time.time() - start_time

    print("\nExtraction par règles:")
    print(json.dumps(fields_rules, indent=2, ensure_ascii=False))
    print(f"Temps: {time_rules:.2f}s")

    print("\nExtraction par DL:")
    print(json.dumps(fields_dl, indent=2, ensure_ascii=False))
    print(f"Temps: {time_dl:.2f}s")

    # Comparaison
    common_fields = set(fields_rules.keys()) & set(fields_dl.keys())
    differences = {}
    for field in common_fields:
        if fields_rules[field] != fields_dl[field]:
            differences[field] = {
                "rules": fields_rules[field],
                "dl": fields_dl[field]
            }

    print("\nDifférences:")
    if differences:
        print(json.dumps(differences, indent=2, ensure_ascii=False))
    else:
        print("Aucune différence")

    return {
        "rules": fields_rules,
        "dl": fields_dl,
        "differences": differences,
        "times": {"rules": time_rules, "dl": time_dl}
    }

def main():
    """Test principal."""
    test_images = [
        r"../images/Carte.jpg",
        r"../images/CNI1.jpg"
    ]

    results = {}
    for img_path in test_images:
        if os.path.exists(img_path):
            results[os.path.basename(img_path)] = test_dl_vs_rules(img_path)

    # Sauvegarder résultats
    with open("dl_vs_rules_comparison.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nRésultats sauvegardés dans dl_vs_rules_comparison.json")

if __name__ == "__main__":
    main()
