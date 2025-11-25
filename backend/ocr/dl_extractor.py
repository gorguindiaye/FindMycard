import os
import logging
import re
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch

logger = logging.getLogger(__name__)

class DLFieldExtractor:
    """
    Extracteur de champs basé sur l'apprentissage profond utilisant NER.
    Utilise un modèle Hugging Face pré-entraîné ou affiné pour identifier les entités.
    """

    def __init__(self, model_path=None):
        """
        Initialise l'extracteur DL.
        :param model_path: Chemin vers le modèle affiné, sinon utilise un modèle pré-entraîné.
        """
        self.model_path = model_path or "Jean-Baptiste/camembert-ner"  # Modèle NER français
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = None

        try:
            if os.path.exists(self.model_path):
                logger.info(f"Chargement du modèle affiné depuis {self.model_path}")
                tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                model = AutoModelForTokenClassification.from_pretrained(self.model_path)
                self.pipeline = pipeline(
                    "ner",
                    model=model,
                    tokenizer=tokenizer,
                    device=self.device,
                    aggregation_strategy="simple"
                )
            else:
                logger.info(f"Utilisation du modèle pré-entraîné {self.model_path}")
                self.pipeline = pipeline(
                    "ner",
                    model=self.model_path,
                    device=self.device,
                    aggregation_strategy="simple"
                )
        except Exception as e:
            logger.warning(f"Impossible de charger le modèle DL: {e}. Repli sur extraction par règles.")
            self.pipeline = None

    def extract_fields(self, ocr_texts, doc_type):
        """
        Extrait les champs des textes OCR en utilisant NER + règles hybrides.
        :param ocr_texts: Liste de tuples (bbox, text) ou liste de textes.
        :param doc_type: Type de document (e.g., 'cni_cedeao').
        :return: Dictionnaire des champs extraits.
        """
        if not self.pipeline:
            logger.warning("Pipeline DL non disponible, retour champs vides.")
            return {}

        # Gérer le cas où ocr_texts est vide
        if not ocr_texts:
            logger.warning("Aucun texte OCR disponible, retour champs vides.")
            return {}

        # Concaténer les textes OCR
        if isinstance(ocr_texts[0], tuple):
            all_text = " ".join([text for _, text in ocr_texts])
        else:
            all_text = " ".join(ocr_texts)

        logger.info(f"Texte pour NER: {all_text[:200]}...")

        # Appliquer NER pour entités nommées
        entities = self.pipeline(all_text)
        logger.info(f"Entités détectées: {entities}")

        # Extraire champs avec approche hybride
        fields = self._hybrid_extract_fields(entities, all_text, doc_type)
        logger.info(f"Champs extraits par DL hybride: {fields}")
        return fields

    def _hybrid_extract_fields(self, entities, full_text, doc_type):
        """
        Extraction hybride : NER pour entités nommées + regex pour formats structurés.
        """
        fields = {}

        # 1. Extraction NER pour entités nommées
        if doc_type == "cni_cedeao":
            # Collecter toutes les entités PER pour noms/prénoms
            person_entities = [e for e in entities if e['entity_group'] == 'PER']
            if len(person_entities) >= 1:
                # Premier PER = nom de famille
                fields["nom"] = person_entities[0]['word'].strip().upper()
            if len(person_entities) >= 2:
                # Deuxième PER = prénom
                fields["prenom"] = person_entities[1]['word'].strip().upper()

            # Lieu de naissance (LOC)
            loc_entities = [e for e in entities if e['entity_group'] == 'LOC']
            if loc_entities:
                fields["lieu_naissance"] = loc_entities[0]['word'].strip().upper()

            # Nationalité (LOC, ORG, MISC pour pays)
            nationality_entities = [e for e in entities if e['entity_group'] in ['LOC', 'ORG', 'MISC']]
            for entity in nationality_entities:
                word = entity['word'].strip().upper()
                # Liste de pays africains courants
                african_countries = ['SENEGAL', 'MALI', 'BURKINA', 'NIGER', 'TOGO', 'BENIN', 'COTE', 'IVOIRE', 'GHANA', 'GUINEE']
                if any(country in word for country in african_countries):
                    fields["nationalite"] = word
                    break

        # 2. Extraction par regex pour formats structurés
        fields.update(self._extract_structured_fields_regex(full_text))

        return fields

    def _extract_structured_fields_regex(self, text):
        """
        Extrait les champs structurés (dates, numéros) avec regex.
        """
        fields = {}

        # Numéro de document (patterns courants pour CNI)
        numero_patterns = [
            r'\b\d{9,12}\b',  # 9-12 chiffres
            r'\b[A-Z]{2}\d{7,10}\b',  # Lettres + chiffres
            r'\b\d{2}\s*\d{2}\s*\d{2}\s*\d{4}\b'  # Format XX XX XX XXXX
        ]
        for pattern in numero_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Prendre le premier match qui semble être un numéro de doc
                candidate = matches[0].replace(' ', '')
                if len(candidate) >= 8:  # Longueur minimale pour numéro doc
                    fields["numero_doc"] = candidate.upper()
                    break

        # Dates (formats courants : JJ/MM/AAAA, JJ-MM-AAAA, etc.)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # JJ/MM/AAAA
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # AAAA/MM/JJ
        ]

        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates_found.extend(matches)

        # Trier et assigner dates (naissance puis expiration)
        if len(dates_found) >= 1:
            fields["date_naissance"] = dates_found[0]
        if len(dates_found) >= 2:
            fields["date_expiration"] = dates_found[1]

        # Sexe (M/F)
        sexe_match = re.search(r'\b(M|F|MASCULIN|FEMININ|HOMME|FEMME)\b', text, re.IGNORECASE)
        if sexe_match:
            sexe = sexe_match.group(1).upper()
            if sexe in ['M', 'MASCULIN', 'HOMME']:
                fields["sexe"] = "M"
            elif sexe in ['F', 'FEMININ', 'FEMME']:
                fields["sexe"] = "F"

        return fields

    def _post_process_fields(self, fields):
        """
        Post-traitement pour standardiser et nettoyer les champs extraits.
        """
        # Standardiser les noms de champs
        field_mapping = {
            'num_document': 'numero_doc',
            'numero_document': 'numero_doc',
            'num_doc': 'numero_doc',
            'photo_presente': 'photo_present',
            'photo_present': 'photo_present',
            'place_of_birth': 'lieu_naissance',
            'birth_place': 'lieu_naissance',
            'birth_date': 'date_naissance',
            'expiration_date': 'date_expiration',
            'delivery_date': 'date_delivrance',
            'gender': 'sexe',
            'nationality': 'nationalite',
            'first_name': 'prenom',
            'last_name': 'nom',
            'surname': 'nom'
        }

        # Appliquer le mapping
        standardized_fields = {}
        for key, value in fields.items():
            standardized_key = field_mapping.get(key, key)
            standardized_fields[standardized_key] = value

        # Nettoyer les valeurs
        for key, value in standardized_fields.items():
            if isinstance(value, str):
                # Supprimer les espaces en trop et mettre en majuscules
                standardized_fields[key] = value.strip().upper()
                # Normaliser les dates
                if 'date' in key:
                    standardized_fields[key] = self._normalize_date(value)
                # Normaliser le sexe
                if key == 'sexe':
                    if value in ['M', 'MASCULIN', 'HOMME', 'H']:
                        standardized_fields[key] = 'M'
                    elif value in ['F', 'FEMININ', 'FEMME', 'FÉMININ']:
                        standardized_fields[key] = 'F'
                # Normaliser photo_present
                if key == 'photo_present':
                    if value in ['OUI', 'YES', 'TRUE', '1', 'O']:
                        standardized_fields[key] = 'OUI'
                    elif value in ['NON', 'NO', 'FALSE', '0', 'N']:
                        standardized_fields[key] = 'NON'

        return standardized_fields

    def _normalize_date(self, date_str):
        """
        Normalise une date au format JJ/MM/AAAA.
        """
        if not date_str:
            return ''

        # Essayer différents formats
        formats = [
            ('%d/%m/%Y', r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
            ('%d-%m-%Y', r'\b\d{1,2}-\d{1,2}-\d{4}\b'),
            ('%Y-%m-%d', r'\b\d{4}-\d{1,2}-\d{1,2}\b'),
            ('%Y/%m/%d', r'\b\d{4}/\d{1,2}/\d{1,2}\b'),
            ('%d.%m.%Y', r'\b\d{1,2}\.\d{1,2}\.\d{4}\b')
        ]

        for fmt, pattern in formats:
            match = re.search(pattern, date_str)
            if match:
                try:
                    parsed = datetime.strptime(match.group(), fmt)
                    return parsed.strftime('%d/%m/%Y')
                except ValueError:
                    continue

        return date_str

    def _map_entities_to_fields(self, entities, doc_type):
        """
        Ancienne méthode - conservée pour compatibilité.
        Utilise maintenant _hybrid_extract_fields.
        """
        return self._hybrid_extract_fields(entities, "", doc_type)

    def is_available(self):
        """Vérifie si l'extracteur DL est disponible."""
        return self.pipeline is not None
