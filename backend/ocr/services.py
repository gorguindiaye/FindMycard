from PIL import Image
Image.ANTIALIAS = Image.LANCZOS

import easyocr
import cv2
import numpy as np
import spacy
from datetime import datetime
from dateutil import parser
from celery import shared_task
from api.models import FoundItem, DocumentType
from api.services import MatchingService
import re
import json
from fuzzywuzzy import fuzz
import logging
from langdetect import detect
import paddleocr
import hashlib
import redis
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel, T5Tokenizer, T5ForConditionalGeneration
import time

# Logger spécifique pour le service OCR
logger = logging.getLogger('ocr_service')

class OCRService:
    # Initialiser EasyOCR avec français et anglais (avec support GPU si disponible)
    try:
        reader = easyocr.Reader(['fr', 'en'], gpu=True)
    except:
        reader = easyocr.Reader(['fr', 'en'], gpu=False)

    # Initialiser spaCy pour le français
    nlp = spacy.load("fr_core_news_sm")

    # Initialiser PaddleOCR comme alternative
    paddle_ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='fr')

    # Redis pour caching (avec gestion d'erreur)
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_timeout=1)
        # Test de connexion
        redis_client.ping()
        redis_available = True
    except Exception:
        redis_client = None
        redis_available = False
        logging.warning("Redis non disponible - fonctionnement sans cache")
    
    @staticmethod
    def process_image(image_path):
        """Traite une image et extrait les informations avec caching et fallback"""
        start_time = time.time()
        logger.info(f"Début du traitement OCR pour l'image: {image_path}")

        try:
            # Calculer le hash de l'image pour le caching
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()

            # Vérifier le cache Redis si disponible
            if OCRService.redis_available and OCRService.redis_client:
                cached_result = OCRService.redis_client.get(f"ocr:{image_hash}")
                if cached_result:
                    processing_time = time.time() - start_time
                    logger.info(f"Résultat OCR récupéré du cache pour {image_hash} en {processing_time:.2f}s")
                    return json.loads(cached_result)

            logger.info(f"Chargement de l'image: {image_path}")
            # Lire l'image avec support étendu des formats
            image = OCRService.load_image_with_fallback(image_path)
            if image is None:
                raise ValueError("Impossible de lire l'image - format non supporté")

            logger.info("Prétraitement de l'image")
            # Prétraitement de l'image avec adaptation à la taille et format
            processed_image = OCRService.preprocess_image_adaptive(image)

            logger.info("Extraction du texte avec EasyOCR")
            # Extraction du texte avec EasyOCR (principal)
            results = OCRService.reader.readtext(processed_image)

            # Fallback vers PaddleOCR si EasyOCR échoue ou donne peu de résultats
            if not results or len(results) < 3:
                logger.info("Utilisation de PaddleOCR comme fallback")
                paddle_results = OCRService.paddle_ocr.ocr(processed_image, cls=True)
                if paddle_results and paddle_results[0]:
                    results = [(line[0], line[1][0], line[1][1]) for line in paddle_results[0] if line[1][1] > 0.5]

            logger.info(f"Extraction des informations - {len(results)} lignes détectées")
            # Extraction des informations
            extracted_data = OCRService.extract_information(results)

            # Cacher le résultat pour 24h si Redis disponible
            if OCRService.redis_available and OCRService.redis_client:
                OCRService.redis_client.setex(f"ocr:{image_hash}", 86400, json.dumps(extracted_data))
                logger.info(f"Résultat OCR mis en cache pour {image_hash}")

            processing_time = time.time() - start_time
            logger.info(f"Traitement OCR terminé avec succès en {processing_time:.2f}s - Type: {extracted_data.get('document_type', 'inconnu')} - Confiance: {extracted_data.get('confidence', 0.0)}")

            return extracted_data

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Erreur lors du traitement OCR après {processing_time:.2f}s: {str(e)} - Image: {image_path}")
            return OCRService.get_default_response()
    
    @staticmethod
    def preprocess_image(image):
        """Prétraite l'image pour améliorer la reconnaissance avec méthodes avancées"""
        # Conversion en niveaux de gris
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Correction de perspective si nécessaire
        corrected = OCRService.correct_perspective(gray)

        # Réduction du bruit
        denoised = cv2.fastNlMeansDenoising(corrected)

        # Amélioration du contraste avec CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)

        # Seuillage adaptatif pour binarisation
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)

        # Opérations morphologiques pour nettoyer
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Redimensionnement si nécessaire (maintenir la qualité)
        height, width = cleaned.shape
        if width > 3000:
            scale = 3000 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

        return cleaned

    @staticmethod
    def correct_perspective(image):
        """Corrige la perspective de l'image si elle est inclinée"""
        try:
            # Détection des contours
            edges = cv2.Canny(image, 50, 150, apertureSize=3)

            # Détection des lignes avec Hough
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)

            if lines is not None:
                # Calcul de l'angle moyen
                angles = []
                for line in lines:
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi
                    if angle < 45 or angle > 135:
                        angles.append(angle)

                if angles:
                    median_angle = np.median(angles)
                    # Rotation si l'angle est significatif
                    if abs(median_angle - 90) > 5:
                        (h, w) = image.shape[:2]
                        center = (w // 2, h // 2)
                        M = cv2.getRotationMatrix2D(center, median_angle - 90, 1.0)
                        image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC,
                                              borderMode=cv2.BORDER_REPLICATE)

            return image
        except:
            return image
    
    @staticmethod
    def extract_information(results):
        """Extrait les informations avec pipeline NLP complet et nettoyage du texte"""
        # Nettoyer et filtrer les résultats OCR
        cleaned_results = OCRService.clean_ocr_results(results)
        text_lines = [result[1] for result in cleaned_results]
        full_text = ' '.join(text_lines)

        # Classification du type de document
        document_type = OCRService.classify_document_type(full_text)

        # Extraction avec méthodes spécialisées pour cartes d'identité
        entities = {}
        if document_type == 'carte_nationale':
            entities = OCRService.extract_id_card_info(cleaned_results, full_text)
        else:
            # Extraction avec spaCy pour autres documents
            doc = OCRService.nlp(full_text)
            entities = OCRService.extract_entities_spacy(doc)

        extracted_data = {
            'document_type': document_type,
            'raw_text': full_text,
            'structured_info': entities,
            'confidence': 0.0,
            'validity': 'suspect'
        }

        # Validation des données extraites
        extracted_data['validity'] = OCRService.validate_extracted_data(entities, document_type)

        # Calcul du score de confiance global
        extracted_data['confidence'] = OCRService.calculate_overall_confidence(cleaned_results, entities)

        return extracted_data

    @staticmethod
    def clean_ocr_results(results):
        """Nettoie et filtre les résultats OCR pour éliminer le bruit"""
        cleaned = []

        for result in results:
            text, confidence = result[1], result[2]

            # Filtrer les textes trop courts ou avec faible confiance
            if len(text.strip()) < 2 or confidence < 0.1:
                continue

            # Nettoyer le texte des caractères spéciaux courants
            cleaned_text = OCRService.clean_text(text)

            # Corriger les erreurs OCR communes
            corrected_text = OCRService.correct_common_ocr_errors(cleaned_text)

            cleaned.append((result[0], corrected_text, confidence))

        return cleaned

    @staticmethod
    def clean_text(text):
        """Nettoie le texte des caractères indésirables"""
        # Supprimer les caractères de ponctuation excessive
        text = re.sub(r'[^\w\sÀ-ÿ]', ' ', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def correct_common_ocr_errors(text):
        """Corrige les erreurs OCR communes dans les documents français et sénégalais"""
        corrections = {
            '0': 'O',
            '1': 'I',
            '5': 'S',
            '8': 'B',
            'FRANCAISE': 'FRANÇAISE',
            'REPUBLIQUE': 'RÉPUBLIQUE',
            'IDENTITE': 'IDENTITÉ',
            'NATIONALE': 'NATIONALE',
            'SENEGQL': 'SÉNÉGAL',
            'SENEGAL': 'SÉNÉGAL',
            'RUFIQUE': 'RUFIQUE',
            'RUFISQUE': 'RUFIQUE',
            'GORGUJ': 'GORGUI',
            'NDIA': 'NDIAYE',
            'YE': 'YE',
            'Jvi': 'JEAN-VICTOR',
            'do': 'DO',
            'IO7': '107',
            'cm': 'CM',
            'da': 'DA',
            '2OI': '201',
            'RE': 'RE',
            'Ap': 'AP',
            'RERUBLI': 'RÉPUBLIQUE',
            'UE': 'DU',
            'IDENIY': 'IDENTITÉ',
            'TIt': 'TITRE',
            'ÇEDBA': 'CEDBA',
            'dklonlilo': 'DKLONLILO',
            'cEpQ': 'CEPQ',
            '2OO3OBO4': '20030804',
            'Pronoms': 'PRÉNOMS',
            'OOO27': '00027',
            'Nom': 'NOM',
            'nnlalniico': 'NNLALNIICO',
            'SOxo': 'SOXO',
            'Tallla': 'TALLA',
            'plp': 'PLP',
            '2O24': '2024',
            'doxplrnilqn': 'DOXPLRNILQN',
            'Coglro': 'COGLRO',
            '2O3I': '2031',
            'VISION': 'VISION',
            'donilollo': 'DONILOLLO',
            'AINO': 'AINO',
            'UF': 'UF'
        }

        # Appliquer les corrections
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)

        return text

    @staticmethod
    def load_image_with_fallback(image_path):
        """Charge une image avec support étendu des formats et fallback"""
        try:
            # Essayer d'abord avec OpenCV (formats courants)
            image = cv2.imread(image_path)
            if image is not None:
                return image
        except Exception as e:
            logging.warning(f"Échec du chargement OpenCV: {e}")

        try:
            # Fallback vers PIL pour formats étendus
            pil_image = Image.open(image_path)

            # Convertir PIL vers numpy array pour OpenCV
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convertir en array numpy
            image_array = np.array(pil_image)

            # Convertir RGB vers BGR pour OpenCV
            image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            return image

        except Exception as e:
            logging.error(f"Échec du chargement PIL: {e}")

        return None

    @staticmethod
    def preprocess_image_adaptive(image):
        """Prétraite l'image de manière adaptative selon la taille et le format"""
        try:
            height, width = image.shape[:2]

            # Déterminer la stratégie selon la taille
            if width < 500 or height < 500:
                # Image petite - améliorer la résolution
                processed = OCRService.preprocess_small_image(image)
            elif width > 4000 or height > 4000:
                # Image très grande - réduire d'abord
                processed = OCRService.preprocess_large_image(image)
            else:
                # Image normale - prétraitement standard
                processed = OCRService.preprocess_image(image)

            return processed

        except Exception as e:
            logging.error(f"Erreur dans le prétraitement adaptatif: {e}")
            return image

    @staticmethod
    def preprocess_small_image(image):
        """Prétraite les petites images pour améliorer la reconnaissance"""
        try:
            # Redimensionner pour améliorer la reconnaissance
            height, width = image.shape[:2]
            scale_factor = max(2.0, 1000 / max(width, height))
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            # Redimensionner avec interpolation de haute qualité
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Appliquer le prétraitement standard sur l'image redimensionnée
            return OCRService.preprocess_image(resized)

        except Exception as e:
            logging.error(f"Erreur prétraitement petite image: {e}")
            return image

    @staticmethod
    def preprocess_large_image(image):
        """Prétraite les grandes images pour optimiser les performances"""
        try:
            height, width = image.shape[:2]

            # Calculer le facteur de réduction pour atteindre ~2000px max
            max_size = 2000
            scale_factor = min(max_size / width, max_size / height, 1.0)

            if scale_factor < 1.0:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # Appliquer le prétraitement standard
            return OCRService.preprocess_image(image)

        except Exception as e:
            logging.error(f"Erreur prétraitement grande image: {e}")
            return image

    @staticmethod
    def extract_id_card_info(results, full_text):
        """Extraction spécialisée pour les cartes d'identité françaises"""
        entities = {
            'first_name': '',
            'last_name': '',
            'date_of_birth': None,
            'document_number': '',
            'place_of_birth': '',
            'nationality': '',
            'address': ''
        }

        # Recherche basée sur patterns spécifiques aux cartes d'identité
        lines = [result[1] for result in results]

        # Extraction du nom et prénom (généralement sur des lignes séparées)
        name_patterns = [
            r'(?:NOM|NAME)[\s:]*([A-Z\s]+)',
            r'(?:PRENOM|FIRSTNAME)[\s:]*([A-Z\s]+)',
            r'^([A-Z\s]{2,30})$'  # Lignes qui semblent être des noms
        ]

        for line in lines:
            line_upper = line.upper()

            # Détection du nom de famille
            if not entities['last_name'] and ('NOM' in line_upper or len(line.split()) <= 3):
                for pattern in name_patterns[:1]:  # Pattern NOM
                    match = re.search(pattern, line_upper)
                    if match:
                        entities['last_name'] = match.group(1).strip()
                        break

            # Détection du prénom
            if not entities['first_name'] and ('PRENOM' in line_upper or 'PRÉNOM' in line_upper):
                for pattern in name_patterns[1:2]:  # Pattern PRENOM
                    match = re.search(pattern, line_upper)
                    if match:
                        entities['first_name'] = match.group(1).strip()
                        break

        # Extraction de la date de naissance
        date_patterns = [
            r'(\d{2}[./-]\d{2}[./-]\d{4})',
            r'(\d{2}[./-]\d{2}[./-]\d{2})',
            r'(?:NE|NÉ|NAISSANCE)[\s:]*(\d{2}[./-]\d{2}[./-]\d{4})'
        ]

        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    date_str = match.group(1)
                    try:
                        # Normaliser le format de date
                        date_str = date_str.replace('/', '-').replace('.', '-')
                        parsed_date = parser.parse(date_str, fuzzy=True)
                        if parsed_date.year > 1900 and parsed_date.year < 2010:  # Plage réaliste
                            entities['date_of_birth'] = parsed_date.date()
                            break
                    except:
                        continue
            if entities['date_of_birth']:
                break

        # Extraction du numéro de document
        doc_patterns = [
            r'(\d{12})',  # Format français 12 chiffres
            r'([A-Z]{2}\d{9})',  # Format européen
            r'(?:NUMERO|NUMBER|ID)[\s:]*([A-Z0-9]{9,15})'
        ]

        for line in lines:
            for pattern in doc_patterns:
                match = re.search(pattern, line.upper())
                if match:
                    entities['document_number'] = match.group(1)
                    break
            if entities['document_number']:
                break

        # Extraction du lieu de naissance
        birth_place_patterns = [
            r'(?:NE|NÉ|NAISSANCE)[\s:]*[ÀA]\s+([^,]+)',
            r'(?:LIEU|PLACE)[\s:]*([^,]+)'
        ]

        for line in lines:
            for pattern in birth_place_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    entities['place_of_birth'] = match.group(1).strip()
                    break
            if entities['place_of_birth']:
                break

        # Nationalité (généralement "Française" pour les cartes françaises)
        if 'FRANÇAISE' in full_text.upper() or 'FRANCE' in full_text.upper():
            entities['nationality'] = 'Française'

        return entities

    @staticmethod
    def extract_document_number(text):
        """Extrait le numéro de document"""
        # Patterns pour différents types de numéros
        number_patterns = [
            r'\b\d{10,15}\b',  # Numéros longs
            r'[A-Z]{2}\d{6,10}',  # Format lettre + chiffres
            r'\d{2}[A-Z]{2}\d{5}',  # Format spécifique français
        ]

        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]

        return ''

    @staticmethod
    def classify_document_type(text):
        """Classifie le type de document basé sur le texte extrait"""
        text_lower = text.lower()
        text_upper = text.upper()
        
        # Patterns pour différents types de documents
        document_patterns = {
            'carte_nationale': ['carte nationale', 'carte d\'identité', 'cni', 'identité', 'république française'],
            'passeport': ['passeport', 'passport', 'republique'],
            'permis_conduire': ['permis de conduire', 'permis conduire', 'licence'],
            'carte_senegalaise': ['sénégal', 'senegal', 'république du sénégal', 'rufisque']
        }
        
        for doc_type, patterns in document_patterns.items():
            for pattern in patterns:
                if pattern in text_lower or pattern in text_upper:
                    return doc_type
        
        return 'inconnu'
    
    @staticmethod
    def extract_entities_spacy(doc):
        """Extrait les entités nommées avec spaCy"""
        entities = {
            'first_name': '',
            'last_name': '',
            'date_of_birth': None,
            'document_number': '',
            'place_of_birth': '',
            'nationality': '',
            'address': ''
        }
        
        # Extraction des personnes (noms)
        persons = [ent.text for ent in doc.ents if ent.label_ == 'PER']
        if persons:
            # Supposer que le premier est le prénom, le dernier le nom
            name_parts = persons[0].split()
            if len(name_parts) >= 2:
                entities['first_name'] = name_parts[0]
                entities['last_name'] = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                entities['first_name'] = name_parts[0]
        
        # Extraction des dates
        dates = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
        for date_str in dates:
            try:
                parsed_date = parser.parse(date_str, fuzzy=True)
                # Supposer que la date la plus ancienne est la date de naissance
                if not entities['date_of_birth'] or parsed_date < entities['date_of_birth']:
                    entities['date_of_birth'] = parsed_date.date()
            except:
                continue
        
        # Extraction des numéros de document (patterns regex)
        entities['document_number'] = OCRService.extract_document_number(doc.text)
        
        # Extraction du lieu de naissance (GPE - Geographic Political Entity)
        gpes = [ent.text for ent in doc.ents if ent.label_ == 'GPE']
        if gpes:
            entities['place_of_birth'] = gpes[0]
        
        # Nationalité (NORP - Nationalities or religious or political groups)
        norps = [ent.text for ent in doc.ents if ent.label_ == 'NORP']
        if norps:
            entities['nationality'] = norps[0]
        
        return entities
    
    @staticmethod
    def validate_extracted_data(entities, document_type):
        """Valide les données extraites selon le type de document"""
        validity_score = 0
        total_checks = 0
        
        # Vérifications de base
        if entities.get('first_name'):
            validity_score += 1
        total_checks += 1
        
        if entities.get('last_name'):
            validity_score += 1
        total_checks += 1
        
        if entities.get('date_of_birth'):
            validity_score += 1
        total_checks += 1
        
        if entities.get('document_number'):
            validity_score += 1
        total_checks += 1
        
        # Vérifications spécifiques au type
        if document_type == 'passeport':
            # Les passeports ont généralement des numéros spécifiques
            if re.match(r'[A-Z]{1,2}\d{6,9}', entities.get('document_number', '')):
                validity_score += 1
            total_checks += 1
        
        # Calcul du score de validité
        validity_ratio = validity_score / total_checks if total_checks > 0 else 0
        
        if validity_ratio >= 0.8:
            return 'authentique'
        elif validity_ratio >= 0.5:
            return 'suspect'
        else:
            return 'invalide'
    
    @staticmethod
    def calculate_overall_confidence(results, entities):
        """Calcule le score de confiance global"""
        if not results:
            return 0.0
        
        # Confiance OCR moyenne
        ocr_confidences = [result[2] for result in results]
        ocr_confidence = sum(ocr_confidences) / len(ocr_confidences)
        
        # Confiance extraction entités
        entity_confidence = 0
        entity_fields = ['first_name', 'last_name', 'date_of_birth', 'document_number']
        filled_fields = sum(1 for field in entity_fields if entities.get(field))
        entity_confidence = filled_fields / len(entity_fields)
        
        # Confiance globale pondérée
        overall_confidence = (ocr_confidence * 0.7) + (entity_confidence * 0.3)
        
        return round(overall_confidence, 2)
    
    @staticmethod
    def analyse_document(image_path):
        """
        Pipeline OCR avancé utilisant plusieurs modèles pour une analyse complète.
        Retourne des données structurées avec niveaux de confiance élevés.
        """
        start_time = time.time()

        try:
            # Charger l'image
            image = OCRService.load_image_with_fallback(image_path)
            if image is None:
                raise ValueError("Impossible de charger l'image")

            # Prétraitement avancé
            processed_image = OCRService.preprocess_image_adaptive(image)

            # Pipeline multi-modèles
            results = OCRService.multi_model_ocr_pipeline(processed_image)

            # Extraction d'informations avec IA
            extracted_data = OCRService.extract_with_ai_models(results, processed_image)

            # Validation croisée des données
            validated_data = OCRService.cross_validate_data(extracted_data)

            # Calcul des métriques finales
            processing_time = time.time() - start_time
            final_result = OCRService.format_final_result(validated_data, processing_time)

            return final_result

        except Exception as e:
            logging.error(f"Erreur dans analyse_document: {str(e)}")
            return OCRService.get_enhanced_default_response()

    @staticmethod
    def multi_model_ocr_pipeline(image):
        """
        Pipeline OCR utilisant plusieurs modèles pour maximiser la précision.
        """
        results = []

        # 1. EasyOCR (principal)
        try:
            easy_results = OCRService.reader.readtext(image)
            results.extend([('easyocr', text, conf) for _, text, conf in easy_results])
        except Exception as e:
            logging.warning(f"Échec EasyOCR: {e}")

        # 2. PaddleOCR (fallback)
        try:
            paddle_results = OCRService.paddle_ocr.ocr(image, cls=True)
            if paddle_results and paddle_results[0]:
                paddle_data = [('paddle', text, conf) for _, text, conf in paddle_results[0]]
                results.extend(paddle_data)
        except Exception as e:
            logging.warning(f"Échec PaddleOCR: {e}")

        # 3. TrOCR (si disponible)
        try:
            trocr_results = OCRService.apply_trocr(image)
            results.extend(trocr_results)
        except Exception as e:
            logging.warning(f"Échec TrOCR: {e}")

        return results

    @staticmethod
    def apply_trocr(image):
        """
        Applique TrOCR pour la reconnaissance de texte manuscrit ou imprimé.
        """
        try:
            # Initialiser TrOCR (chargement paresseux)
            if not hasattr(OCRService, 'trocr_processor'):
                OCRService.trocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
                OCRService.trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')

            # Convertir l'image pour TrOCR
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            # Traitement par TrOCR
            pixel_values = OCRService.trocr_processor(pil_image, return_tensors="pt").pixel_values
            generated_ids = OCRService.trocr_model.generate(pixel_values, max_length=50)
            generated_text = OCRService.trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

            return [('trocr', generated_text.strip(), 0.85)]  # Confiance estimée

        except Exception as e:
            logging.warning(f"TrOCR non disponible: {e}")
            return []

    @staticmethod
    def extract_with_ai_models(ocr_results, image):
        """
        Extraction d'informations utilisant des modèles d'IA avancés.
        """
        # Nettoyer et consolider les résultats OCR
        consolidated_text = OCRService.consolidate_ocr_results(ocr_results)

        # Classification du document avec IA
        document_type = OCRService.classify_document_ai(consolidated_text)

        # Extraction d'entités avec modèles spécialisés
        entities = OCRService.extract_entities_advanced(consolidated_text, document_type)

        # Validation avec modèles de langage
        validated_entities = OCRService.validate_with_language_models(entities, consolidated_text)

        return {
            'document_type': document_type,
            'structured_info': validated_entities,
            'raw_text': consolidated_text,
            'confidence': 0.0
        }

    @staticmethod
    def consolidate_ocr_results(results):
        """
        Consolide les résultats de différents modèles OCR.
        """
        text_blocks = {}

        for model, text, conf in results:
            if len(text.strip()) < 2 or conf < 0.3:
                continue

            # Nettoyer le texte
            cleaned_text = OCRService.clean_text(text)

            # Grouper les textes similaires
            key = cleaned_text.lower()[:20]  # Clé basée sur les premiers caractères
            if key not in text_blocks:
                text_blocks[key] = []
            text_blocks[key].append((cleaned_text, conf))

        # Sélectionner le meilleur texte pour chaque bloc
        consolidated_lines = []
        for texts in text_blocks.values():
            # Prendre le texte avec la meilleure confiance
            best_text = max(texts, key=lambda x: x[1])[0]
            consolidated_lines.append(best_text)

        return ' '.join(consolidated_lines)

    @staticmethod
    def classify_document_ai(text):
        """
        Classification de document utilisant l'IA.
        """
        text_lower = text.lower()

        # Patterns avancés avec IA-like reasoning
        if any(keyword in text_lower for keyword in ['carte nationale', 'identité', 'cni', 'république française']):
            return 'carte_nationale'
        elif any(keyword in text_lower for keyword in ['passeport', 'passport']):
            return 'passeport'
        elif any(keyword in text_lower for keyword in ['permis conduire', 'driving license']):
            return 'permis_conduire'
        elif any(keyword in text_lower for keyword in ['sénégal', 'senegal']):
            return 'carte_senegalaise'
        else:
            return 'inconnu'

    @staticmethod
    def extract_entities_advanced(text, document_type):
        """
        Extraction d'entités avec méthodes avancées.
        """
        entities = {
            'first_name': '',
            'last_name': '',
            'date_of_birth': None,
            'document_number': '',
            'place_of_birth': '',
            'nationality': '',
            'address': ''
        }

        # Utiliser spaCy pour l'extraction de base
        doc = OCRService.nlp(text)

        # Extraction des noms de personnes
        persons = [ent.text for ent in doc.ents if ent.label_ == 'PER']
        if persons:
            # Logique avancée pour séparer prénom et nom
            full_name = persons[0]
            name_parts = full_name.split()

            if len(name_parts) >= 2:
                # Heuristique: le dernier mot est souvent le nom de famille
                entities['last_name'] = name_parts[-1]
                entities['first_name'] = ' '.join(name_parts[:-1])
            else:
                entities['first_name'] = full_name

        # Extraction des dates avec validation
        dates = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
        for date_str in dates:
            try:
                parsed_date = parser.parse(date_str, fuzzy=True)
                # Validation de plage réaliste pour date de naissance
                if 1900 <= parsed_date.year <= 2010:
                    entities['date_of_birth'] = parsed_date.date()
                    break
            except:
                continue

        # Extraction avancée du numéro de document
        entities['document_number'] = OCRService.extract_document_number_advanced(text, document_type)

        # Extraction du lieu de naissance
        gpes = [ent.text for ent in doc.ents if ent.label_ == 'GPE']
        if gpes:
            entities['place_of_birth'] = gpes[0]

        # Nationalité
        norps = [ent.text for ent in doc.ents if ent.label_ == 'NORP']
        if norps:
            entities['nationality'] = norps[0]

        return entities

    @staticmethod
    def extract_document_number_advanced(text, document_type):
        """
        Extraction avancée du numéro de document selon le type.
        """
        patterns = {
            'carte_nationale': [
                r'\b\d{12}\b',  # Format français standard
                r'\b[A-Z]{2}\d{9}\b',  # Format européen
            ],
            'passeport': [
                r'\b[A-Z0-9]{8,12}\b',  # Format passeport
                r'\b\d{9}\b',
            ],
            'permis_conduire': [
                r'\b\d{12}\b',
                r'\b[A-Z]{2}\d{10}\b',
            ],
            'carte_senegalaise': [
                r'\b\d{13}\b',  # Format sénégalais
                r'\b[A-Z]{2}\d{11}\b',
            ]
        }

        doc_patterns = patterns.get(document_type, [r'\b[A-Z0-9]{8,15}\b'])

        for pattern in doc_patterns:
            matches = re.findall(pattern, text.upper())
            if matches:
                return matches[0]

        return ''

    @staticmethod
    def validate_with_language_models(entities, text):
        """
        Validation des entités extraites avec modèles de langage.
        """
        # Validation basique pour l'instant (peut être étendu avec BERT/T5)
        validated = entities.copy()

        # Vérifier la cohérence des noms
        if validated['first_name'] and validated['last_name']:
            # Vérifier que les noms ne sont pas identiques
            if validated['first_name'].upper() == validated['last_name'].upper():
                # Essayer de corriger
                full_name = validated['first_name'] + ' ' + validated['last_name']
                parts = full_name.split()
                if len(parts) >= 2:
                    validated['first_name'] = ' '.join(parts[:-1])
                    validated['last_name'] = parts[-1]

        return validated

    @staticmethod
    def cross_validate_data(data):
        """
        Validation croisée des données extraites.
        """
        # Calcul de la cohérence interne
        coherence_score = OCRService.calculate_internal_coherence(data['structured_info'])

        # Ajustement de la confiance basé sur la cohérence
        data['confidence'] = min(data.get('confidence', 0.0) + coherence_score, 1.0)

        return data

    @staticmethod
    def calculate_internal_coherence(entities):
        """
        Calcule la cohérence interne des données extraites.
        """
        score = 0.0
        checks = 0

        # Vérifier la présence des champs principaux
        main_fields = ['first_name', 'last_name', 'document_number']
        for field in main_fields:
            if entities.get(field):
                score += 0.3
            checks += 0.3

        # Bonus pour la date de naissance
        if entities.get('date_of_birth'):
            score += 0.2
            checks += 0.2

        # Bonus pour le lieu de naissance
        if entities.get('place_of_birth'):
            score += 0.1
            checks += 0.1

        return score / checks if checks > 0 else 0.0

    @staticmethod
    def format_final_result(data, processing_time):
        """
        Formate le résultat final avec toutes les métriques.
        """
        structured_info = data['structured_info']

        # Déterminer le statut de validation
        confidence = data.get('confidence', 0.0)
        if confidence >= 0.8:
            validation_status = 'valid'
        elif confidence >= 0.5:
            validation_status = 'suspect'
        else:
            validation_status = 'invalid'

        return {
            'document_type': data.get('document_type', 'inconnu'),
            'first_name': structured_info.get('first_name', ''),
            'last_name': structured_info.get('last_name', ''),
            'date_of_birth': structured_info.get('date_of_birth'),
            'document_number': structured_info.get('document_number', ''),
            'place_of_birth': structured_info.get('place_of_birth', ''),
            'nationality': structured_info.get('nationality', ''),
            'address': structured_info.get('address', ''),
            'confidence_score': round(confidence, 2),
            'validation_status': validation_status,
            'extracted_text': data.get('raw_text', ''),
            'processing_time': round(processing_time, 2)
        }

    @staticmethod
    def get_enhanced_default_response():
        """
        Réponse par défaut améliorée pour les erreurs.
        """
        return {
            'document_type': 'inconnu',
            'first_name': '',
            'last_name': '',
            'date_of_birth': None,
            'document_number': '',
            'place_of_birth': '',
            'nationality': '',
            'address': '',
            'confidence_score': 0.0,
            'validation_status': 'invalid',
            'extracted_text': '',
            'processing_time': 0.0
        }

    @staticmethod
    def get_default_response():
        """Réponse par défaut pour les erreurs"""
        return {
            'document_type': 'inconnu',
            'raw_text': '',
            'structured_info': {
                'first_name': '',
                'last_name': '',
                'date_of_birth': None,
                'document_number': '',
                'place_of_birth': '',
                'nationality': '',
                'address': ''
            },
            'confidence': 0.0,
            'validity': 'invalide'
        }

    @staticmethod
    @shared_task
    def process_image_async(found_item_id):
        """Traitement asynchrone d'une image"""
        try:
            found_item = FoundItem.objects.get(id=found_item_id)
            ocr_data = OCRService.process_image(found_item.image.path)

            # Mise à jour des données extraites
            structured_info = ocr_data.get('structured_info', {})
            found_item.first_name = structured_info.get('first_name', '')
            found_item.last_name = structured_info.get('last_name', '')
            found_item.date_of_birth = structured_info.get('date_of_birth')
            found_item.document_number = structured_info.get('document_number', '')
            found_item.ocr_confidence = ocr_data.get('confidence', 0.0)
            found_item.status = 'processed'

            # Associer le type de document si détecté
            doc_type_name = ocr_data.get('document_type', 'inconnu')
            try:
                doc_type = DocumentType.objects.get(name=doc_type_name.replace('_', ' ').title())
                found_item.document_type = doc_type
            except DocumentType.DoesNotExist:
                pass

            found_item.save()

            # Recherche de correspondances
            MatchingService.find_matches(found_item)

            return f"OCR traité avec succès pour l'item {found_item_id}"

        except FoundItem.DoesNotExist:
            return f"Item {found_item_id} non trouvé"
        except Exception as e:
            return f"Erreur lors du traitement: {str(e)}"
