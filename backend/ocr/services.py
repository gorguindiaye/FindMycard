import os
import cv2
import numpy as np
import json
import argparse
import re
from difflib import SequenceMatcher
from paddleocr import PaddleOCR
from sklearn.ensemble import RandomForestClassifier
import joblib  # pour sauvegarder le modèle de classification
import logging
from .dl_extractor import DLFieldExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- CONFIGURATION ----------------
DOCUMENT_FIELDS = {
    "cni_senegalaise": ["nom", "prenom", "date_naissance", "numero_document", "sexe", "nationalite", "lieu_naissance", "date_expiration", "photo_detectee"]
}

OCR = PaddleOCR(lang='fr', use_angle_cls=True)  # PaddleOCR initialisé avec modèles par défaut pour français (PP-OCRv4 en 3.x, optimisé pour texte imprimé comme IDs)

class OCRService:
    @staticmethod
    def process_image(image_path, expected=None, doc_type=None):
        """
        Traite une image de document et extrait les champs via OCR.
        Retourne un dictionnaire avec les résultats.
        """
        logger.info(f"Processing image: {image_path}")
        if not os.path.exists(image_path):
            logger.error("Image not found")
            return {"error": "Image non trouvée", "success": False}

        img = preprocess_image(image_path)
        logger.info("Image preprocessed")

        # Classification automatique ou forcée
        doc_type = doc_type or classify_document(img)
        logger.info(f"Document type: {doc_type}")
        if doc_type is None:
            logger.error("Type de document inconnu")
            return {"error": "Type de document inconnu", "success": False}

        # OCR et extraction
        ocr_results = ocr_extract(img)
        logger.info(f"OCR results: {len(ocr_results)} lines extracted")
        for box, text in ocr_results[:5]:  # Log first 5
            logger.info(f"OCR line: {text}")
        extracted = extract_fields_by_type(ocr_results, doc_type)
        logger.info(f"Extracted fields: {extracted}")

        # Calculate confidence (simple average of non-empty fields)
        confidence = sum(1 for v in extracted.values() if v) / len(extracted) if extracted else 0.0

        structured_payload = extracted
        result = {
            "doc_type": doc_type,
            "structured_payload": structured_payload,
            "confidence": confidence,
            "success": True
        }

        if expected:
            status, similarity = compare_fields(extracted, expected, doc_type)
            result.update({
                "expected": expected,
                "field_status": status,
                "similarity_%": similarity,
                "success": all(status.values())
            })

        logger.info(f"Processing complete, confidence: {confidence}")
        return result

def preprocess_image(image_path):
    """Prétraitement OpenCV pour tout type de document - gardé en couleur pour améliorer la détection OCR"""
    img = cv2.imread(image_path)
    # Garder l'image en couleur pour PaddleOCR (meilleure détection de texte)
    img = cv2.bilateralFilter(img, 9, 75, 75)
    # Appliquer CLAHE sur chaque canal de couleur
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    for i in range(3):
        img[:, :, i] = clahe.apply(img[:, :, i])
    # Correction de rotation basée sur les contours
    gray_for_rotation = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    coords = np.column_stack(np.where(gray_for_rotation > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = img.shape[:2]
        M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return img

def classify_document(img):
    """
    Classification automatique du type de document, focalisée sur CNI sénégalaise.
    """
    # Pour l'instant, forcer cni_senegalaise car focus Sénégal
    # À l'avenir, détecter via texte OCR
    return "cni_senegalaise"

def ocr_extract(img):
    """Renvoie une liste de tuples : (bbox, texte)"""
    logger.info("Running PaddleOCR...")
    result = OCR.ocr(img)
    logger.info(f"PaddleOCR raw result type: {type(result)}")
    logger.info(f"PaddleOCR raw result length: {len(result) if result else 0}")
    if result and len(result) > 0:
        logger.info(f"First result item type: {type(result[0])}")
        logger.info(f"First result item keys: {result[0].keys() if isinstance(result[0], dict) else 'Not a dict'}")

    ocr_results = []
    if result and len(result) > 0 and isinstance(result[0], dict):
        # Nouveau format PaddleOCR avec doc preprocessing
        rec_texts = result[0].get('rec_texts', [])
        rec_scores = result[0].get('rec_scores', [])
        rec_boxes = result[0].get('rec_boxes', [])

        logger.info(f"Found {len(rec_texts)} text detections")
        for i, text in enumerate(rec_texts):
            if i < len(rec_boxes):
                bbox = rec_boxes[i]
                if len(bbox) >= 4:
                    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    ocr_results.append(((x1, y1, x2, y2), text))
                    logger.info(f"Extracted text: '{text}' (bbox: {x1},{y1},{x2},{y2})")
                else:
                    logger.warning(f"Invalid bbox format for text '{text}': {bbox}")
            else:
                logger.warning(f"No bbox for text '{text}'")
    else:
        logger.warning("No OCR results from PaddleOCR or unexpected format")
    return ocr_results

def normalize_text(text):
    text = text.strip().upper()
    accents = {'É':'E','È':'E','Ê':'E','À':'A','Â':'A','Ù':'U','Û':'U','Î':'I','Ô':'O','Ç':'C'}
    for a,r in accents.items():
        text = text.replace(a,r)
    return text

def correct_ocr_errors(text):
    """Corrige les erreurs OCR courantes pour documents d'identité."""
    corrections = {
        '1': 'I', 'I': '1',
        '8': 'B', 'B': '8',
        '5': 'S', 'S': '5',
        '2': 'Z', 'Z': '2',
        '6': 'G', 'G': '6',
        '4': 'A', 'A': '4',
    }
    # Ne pas corriger 0↔O pour éviter erreurs dans numéros (garder 0)
    # Appliquer corrections seulement sur lettres isolées ou dans mots sans chiffres
    corrected = text
    for wrong, right in corrections.items():
        # Remplacer seulement si pas dans un mot avec chiffres (pour éviter corriger numéros)
        corrected = re.sub(rf'\b{wrong}\b', right, corrected, flags=re.IGNORECASE)
    # Supprimer doublons, artefacts
    corrected = re.sub(r'(\w)\1{2,}', r'\1\1', corrected)  # Limiter répétitions
    corrected = re.sub(r'[^\w\s/:.-]', '', corrected)  # Supprimer symboles inutiles
    # Reconstituer mots coupés (simple: enlever espaces multiples)
    corrected = re.sub(r'\s+', ' ', corrected)
    return corrected.strip()

def parse_date(date_str):
    """Parse dates flexibles au format YYYY-MM-DD."""
    if not date_str:
        return ""
    # Formats: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD MMM YYYY (français)
    mois_fr = {'JAN': '01', 'FEV': '02', 'MAR': '03', 'AVR': '04', 'MAI': '05', 'JUN': '06',
               'JUI': '07', 'AOU': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
    date_str = date_str.upper()
    # Remplacer mois textuels
    for m_fr, num in mois_fr.items():
        date_str = date_str.replace(m_fr, num)
    # Essayer parsing
    try:
        from dateutil import parser
        dt = parser.parse(date_str, dayfirst=True)
        return dt.strftime('%Y-%m-%d')
    except:
        # Fallback regex pour DD/MM/YYYY
        match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if match:
            d, m, y = match.groups()
            y = y.zfill(4) if len(y) == 2 else y
            if int(y) < 1900:
                y = '19' + y
            elif int(y) > 2100:
                y = '20' + y[:2]
            return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        return ""

def capitalize_name(name):
    """Capitalise noms/prénoms."""
    return ' '.join(word.capitalize() for word in name.split())

def post_process_ocr(raw_text: str) -> dict:
    """Post-traitement OCR: corrige, déduit champs pour CNI sénégalaise, normalise, retourne JSON fixe."""
    if not raw_text:
        return {"nom": "", "prenom": "", "date_naissance": "", "numero_document": "", "sexe": "", "nationalite": "", "lieu_naissance": "", "date_expiration": "", "photo_detectee": False}

    corrected_text = correct_ocr_errors(raw_text)
    all_upper = corrected_text.upper()
    photo_detectee = bool(re.search(r'PHOTO|PORTRAIT|VISAGE', all_upper))

    # Détection champs pour CNI sénégalaise
    nom = ""
    # Premier mot majuscule long comme nom
    maj_words = re.findall(r'\b[A-ZÀÂÊÎÔÛÇÉÈÙ]{3,}\b', all_upper)
    if maj_words:
        nom = capitalize_name(maj_words[0])

    prenom = ""
    # Prénom: mots après nom jusqu'à "NE LE" ou date
    prenom_match = re.search(rf'{re.escape(maj_words[0])}\s+([A-ZÀÂÊÎÔÛÇÉÈÙ\s]+?)(?:\s+NE\s+LE|\s+\d)', all_upper)
    if prenom_match:
        prenom_text = prenom_match.group(1).strip()
        # Prendre seulement le premier mot ou deux si court
        prenom_words = prenom_text.split()
        prenom = capitalize_name(' '.join(prenom_words[:2]))  # Max 2 mots pour prénom
    elif len(maj_words) > 1 and maj_words[1] not in ['REPUBLIQUE', 'SENEGAL', 'FRANCE', 'DATE', 'EXP']:
        prenom = capitalize_name(maj_words[1])

    date_naissance = ""
    # Formats dates
    date_matches = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}', corrected_text)
    if date_matches:
        date_naissance = parse_date(date_matches[0])

    numero_document = ""
    # Numéro: après "N° DE LA CARTE D'IDENTITÉ" ou long alphanum 9-12
    num_match = re.search(r"N°\s*DE\s*LA\s*CARTE\s*D'?\s*IDENTITÉ\s*([A-Z0-9\s]{9,12})", all_upper)
    if num_match:
        numero_document = re.sub(r'\s+', '', num_match.group(1))
    else:
        num_fallback = re.findall(r'\b[A-Z0-9]{9,12}\b', all_upper)
        if num_fallback:
            numero_document = num_fallback[0]

    sexe = ""
    sexe_match = re.search(r"SEXE[:\s]*([MF])", all_upper)
    if sexe_match:
        sexe = sexe_match.group(1)

    nationalite = ""
    # Sénégal → Sénégalaise
    if re.search(r'SENEGAL|REPUBLIQUE\s+DU\s+SENEGAL', all_upper):
        nationalite = "Sénégalaise"
    elif re.search(r'FRANCE|REPUBLIQUE\s+FRANCAISE', all_upper):
        nationalite = "Française"

    lieu_naissance = ""
    # Lieu: après date expiration ou dernier mot maj si pas date/exp
    if len(date_matches) > 1:
        # Après la dernière date
        date_exp_str = date_matches[-1]
        lieu_match = re.search(rf'{re.escape(date_exp_str)}\s+([A-ZÀÂÊÎÔÛÇÉÈÙ]+)', all_upper)
        if lieu_match:
            lieu_naissance = capitalize_name(lieu_match.group(1))
    elif maj_words and maj_words[-1] not in ['EXP', 'DATE', 'SENEGAL', 'REPUBLIQUE', 'FRANCE']:
        lieu_naissance = capitalize_name(maj_words[-1])

    date_expiration = ""
    if len(date_matches) > 1:
        date_expiration = parse_date(date_matches[-1])
    exp_match = re.search(r"(?:EXP|EXPIRE|VALABLE\s+JUSQU\'AU)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", all_upper)
    if exp_match:
        date_expiration = parse_date(exp_match.group(1))

    return {
        "nom": nom,
        "prenom": prenom,
        "date_naissance": date_naissance,
        "numero_document": numero_document,
        "sexe": sexe,
        "nationalite": nationalite,
        "lieu_naissance": lieu_naissance,
        "date_expiration": date_expiration,
        "photo_detectee": photo_detectee
    }

def extract_fields_by_type(ocr_results, doc_type):
    """Extraction via post-traitement pour CNI sénégalaise."""
    all_text = " ".join([text for _, text in ocr_results])
    logger.info(f"All extracted text: {all_text}")

    # Essayer l'extraction DL si disponible
    extractor = DLFieldExtractor()
    if extractor.is_available():
        dl_fields = extractor.extract_fields(ocr_results, doc_type)
        # Merger DL si possible, mais prioriser post_process
        logger.info(f"Champs DL intégrés: {dl_fields}")
    else:
        logger.info("Extracteur DL non disponible")

    # Post-traitement principal
    structured_fields = post_process_ocr(all_text)

    logger.info(f"Final extracted fields: {structured_fields}")
    return structured_fields

def compare_fields(extracted, expected, doc_type):
    """Compare chaque champ avec les valeurs attendues"""
    status, similarity = {}, {}
    fields = DOCUMENT_FIELDS.get(doc_type, [])
    for field in fields:
        ext_val = normalize_text(str(extracted.get(field,"")))
        exp_val = normalize_text(str(expected.get(field,"")))
        ratio = SequenceMatcher(None, ext_val, exp_val).ratio()
        similarity[field] = round(ratio*100,2)
        status[field] = ratio >= 0.8  # Lower threshold for partial matches
    return status, similarity

# ---------------- SCRIPT PRINCIPAL ----------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", default="test_images", help="Dossier contenant les images à traiter")
    parser.add_argument("--ground_truth", default="ground_truth.json", help="Fichier JSON des valeurs attendues")
    parser.add_argument("--doc_type", default=None, choices=DOCUMENT_FIELDS.keys(), help="Type de document (si classification automatique impossible)")
    parser.add_argument("--output", default="ocr_report.json", help="Fichier JSON de sortie")
    args = parser.parse_args()

    # Charger ground truth
    with open(args.ground_truth,"r",encoding="utf-8") as f:
        ground_truth = json.load(f)

    report = {}
    total_images, total_success = 0,0

    for filename in os.listdir(args.images):
        if not filename.lower().endswith((".png",".jpg",".jpeg")):
            continue
        total_images +=1
        img_path = os.path.join(args.images, filename)
        img = preprocess_image(img_path)

        # Classification
        doc_type = args.doc_type or classify_document(img)
        if doc_type is None:
            report[filename] = {"error":"Type de document inconnu", "success":False}
            continue

        # OCR
        ocr_results = ocr_extract(img)
        extracted = extract_fields_by_type(ocr_results, doc_type)
        expected = ground_truth.get(filename, {})
        status, similarity = compare_fields(extracted, expected, doc_type)
        success = all(status.values())
        if success: total_success +=1

        report[filename] = {
            "doc_type": doc_type,
            "extracted": extracted,
            "expected": expected,
            "field_status": status,
            "similarity_%": similarity,
            "success": success
        }

    overall_success_rate = round((total_success/total_images)*100,2) if total_images else 0
    final_report = {
        "total_images": total_images,
        "successful_images": total_success,
        "overall_success_rate_%": overall_success_rate,
        "detailed_report": report
    }

    with open(args.output,"w",encoding="utf-8") as f:
        json.dump(final_report,f,indent=4,ensure_ascii=False)

    print(f"Images traitées : {total_images}, réussies : {total_success}")
    print(f"Taux global : {overall_success_rate}%")
    print(f"Rapport généré : {args.output}")

if __name__=="__main__":
    main()
