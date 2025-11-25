import os
import argparse
import csv
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findmyid.settings')

import django  # noqa: E402

django.setup()

from ocr.services import OCRService  # noqa: E402


def evaluate_folder(folder: Path, output: Path | None = None):
    images = [p for p in folder.rglob('*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
    rows = []

    for image_path in images:
        result = OCRService.process_image(str(image_path))
        payload = result.get('structured_payload', {})
        rows.append({
            'image': str(image_path),
            'type': payload.get('type', ''),
            'nom': payload.get('nom', ''),
            'prenom': payload.get('prenom', ''),
            'date_naissance': payload.get('date_naissance', ''),
            'num_document': payload.get('num_document', ''),
            'sexe': payload.get('sexe', ''),
            'nationalite': payload.get('nationalite', ''),
            'date_expiration': payload.get('date_expiration', ''),
            'date_delivrance': payload.get('date_delivrance', ''),
            'confidence': result.get('confidence', 0.0),
        })

    if output and rows:
        with output.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    filled = sum(1 for row in rows if row.get('num_document'))
    print(f"Evaluated {len(rows)} documents. Documents avec numéro détecté: {filled}")


def main():
    parser = argparse.ArgumentParser(description="Évalue un dossier d'images via OCRService.")
    parser.add_argument('folder', type=Path, help='Chemin du dossier contenant les images')
    parser.add_argument('--output', type=Path, help='Chemin du CSV de sortie')
    args = parser.parse_args()

    if not args.folder.exists():
        raise SystemExit(f"Le dossier {args.folder} n'existe pas.")

    evaluate_folder(args.folder, args.output)


if __name__ == '__main__':
    main()

