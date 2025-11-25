#!/usr/bin/env python3
"""
Test de précision OCR pour les pièces d'identité
Vérification de l'extraction exacte des informations avec 100% de correspondance
"""
import os
import cv2
import numpy as np
import json
import time
from datetime import datetime
from ocr.services import OCRService
from fuzzywuzzy import fuzz
import re

class OCRAccuracyTester:
    def __init__(self):
        self.base_image_path = "../images/Carte.jpg"
        self.test_images_dir = "../images/test_variations"
        self.results = []
        self.ground_truths = self.define_ground_truths()

        # Créer le dossier de test si nécessaire
        os.makedirs(self.test_images_dir, exist_ok=True)

    def define_ground_truths(self):
        """Définit les vérités terrain pour chaque variation d'image"""
        return {
            'original': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'numero_doc': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'rotated_15': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'noisy': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'blurry': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'dark': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'contrast_high': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'rotated_30': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'small': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'large': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'mixed_case': {
                'nom': 'Dupont',
                'prenom': 'Jean Pierre',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'Paris',
                'photo_presente': True
            },
            'accents': {
                'nom': 'DUPÔNT',
                'prenom': 'JEÂN PIÉRRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PÂRIS',
                'photo_presente': True
            },
            'o_zero_confusion': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '12345678901O',  # O au lieu de 0
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'partial_occlusion': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': False  # Photo partiellement occultée
            },
            'low_quality': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            },
            'inverted_colors': {
                'nom': 'DUPONT',
                'prenom': 'JEAN PIERRE',
                'date_naissance': '1985-05-15',
                'num_document': '123456789012',
                'sexe': 'M',
                'nationalite': 'Française',
                'date_expiration': '2030-05-15',
                'lieu_naissance': 'PARIS',
                'photo_presente': True
            }
        }

    def create_image_variations(self):
        """Crée les variations d'images pour les tests"""
        if not os.path.exists(self.base_image_path):
            print(f"Image de base non trouvée: {self.base_image_path}, création d'une image synthétique...")
            image = self.create_synthetic_id_card()
        else:
            image = cv2.imread(self.base_image_path)
            if image is None:
                print("Impossible de charger l'image de base, création d'une image synthétique...")
                image = self.create_synthetic_id_card()

        variations = {
            'original': lambda img: img,
            'rotated_15': lambda img: self.rotate_image(img, 15),
            'noisy': self.add_noise,
            'blurry': lambda img: cv2.GaussianBlur(img, (5, 5), 0),
            'dark': lambda img: cv2.convertScaleAbs(img, alpha=0.3, beta=0),
            'contrast_high': lambda img: cv2.convertScaleAbs(img, alpha=2.0, beta=0),
            'rotated_30': lambda img: self.rotate_image(img, 30),
            'small': lambda img: cv2.resize(img, (int(img.shape[1] * 0.5), int(img.shape[0] * 0.5))),
            'large': lambda img: cv2.resize(img, (int(img.shape[1] * 1.5), int(img.shape[0] * 1.5))),
            'mixed_case': lambda img: img,  # Même image, ground truth différente
            'accents': lambda img: img,     # Même image, ground truth différente
            'o_zero_confusion': lambda img: img,  # Même image, ground truth différente
            'partial_occlusion': self.add_partial_occlusion,
            'low_quality': lambda img: cv2.resize(cv2.GaussianBlur(img, (7, 7), 0), (int(img.shape[1] * 0.3), int(img.shape[0] * 0.3))),
            'inverted_colors': lambda img: cv2.bitwise_not(img)
        }

        for var_name, transform_func in variations.items():
            try:
                transformed = transform_func(image.copy())
                output_path = os.path.join(self.test_images_dir, f"{var_name}.jpg")
                cv2.imwrite(output_path, transformed)
                print(f"Variation créée: {var_name}")
            except Exception as e:
                print(f"Erreur création variation {var_name}: {e}")

        return True

    def rotate_image(self, image, angle):
        """Fait tourner l'image d'un angle donné"""
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        return rotated

    def add_noise(self, image):
        """Ajoute du bruit gaussien à l'image"""
        row, col, ch = image.shape
        mean = 0
        var = 0.1
        sigma = var**0.5
        gauss = np.random.normal(mean, sigma, (row, col, ch))
        gauss = gauss.reshape(row, col, ch)
        noisy = image + gauss
        return np.clip(noisy, 0, 255).astype(np.uint8)

    def add_partial_occlusion(self, image):
        """Ajoute une occultation partielle (simulant un doigt ou un objet)"""
        occluded = image.copy()
        h, w = occluded.shape[:2]
        # Occulter le coin supérieur droit (où pourrait être la photo)
        cv2.rectangle(occluded, (w//2, 0), (w, h//2), (0, 0, 0), -1)
        return occluded

    def create_synthetic_id_card(self):
        """Crée une carte d'identité synthétique avec du texte"""
        # Dimensions typiques d'une carte d'identité (format ID-1)
        width, height = 1016, 642  # pixels pour une résolution de 300 DPI

        # Créer une image blanche
        image = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Ajouter un fond légèrement coloré (bleu pâle comme les cartes officielles)
        cv2.rectangle(image, (0, 0), (width, height), (240, 248, 255), -1)

        # Ajouter une bordure
        cv2.rectangle(image, (20, 20), (width-20, height-20), (0, 0, 0), 2)

        # Police et taille
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        font_color = (0, 0, 0)
        font_thickness = 2

        # Texte de la carte d'identité
        texts = [
            ("REPUBLIQUE DU SENEGAL", (50, 80)),
            ("CARTE D'IDENTITE NATIONALE", (50, 120)),
            ("N° DE LA CARTE D'IDENTITE: 123456789012", (50, 180)),
            ("NOM: DUPONT", (50, 240)),
            ("PRENOMS: JEAN PIERRE", (50, 280)),
            ("DATE DE NAISSANCE: 15/05/1985", (50, 320)),
            ("LIEU DE NAISSANCE: PARIS", (50, 360)),
            ("SEXE: M", (50, 400)),
            ("NATIONALITE: FRANCAISE", (50, 440)),
            ("DATE D'EXPIRATION: 15/05/2030", (50, 480)),
            ("SIGNATURE", (50, 550))
        ]

        # Ajouter le texte à l'image
        for text, position in texts:
            cv2.putText(image, text, position, font, font_scale, font_color, font_thickness)

        # Ajouter une zone pour la photo (rectangle vide)
        cv2.rectangle(image, (width-250, 150), (width-50, 350), (200, 200, 200), -1)
        cv2.putText(image, "PHOTO", (width-200, 260), font, 1.0, (100, 100, 100), 1)

        return image

    def run_accuracy_tests(self):
        """Exécute les tests de précision"""
        print("=== TESTS DE PRÉCISION OCR ===\n")

        for var_name, ground_truth in self.ground_truths.items():
            image_path = os.path.join(self.test_images_dir, f"{var_name}.jpg")

            if not os.path.exists(image_path):
                print(f"Image non trouvée pour {var_name}, création...")
                continue

            print(f"Test de {var_name}...")

            try:
                start_time = time.time()
                ocr_result = OCRService.process_image(image_path)
                processing_time = time.time() - start_time

                # Comparer avec la vérité terrain
                comparison = self.compare_to_ground_truth(ocr_result, ground_truth, var_name)

                test_result = {
                    'nom_fichier': f"{var_name}.jpg",
                    'valeurs_extraites': self.extract_values_from_ocr(ocr_result),
                    'valeurs_attendues': ground_truth,
                    'statut': '✅ Réussi' if comparison['exact_match'] else '❌ Échec',
                    'differences': comparison['differences'],
                    'temps_traitement': round(processing_time, 2),
                    'confiance_ocr': ocr_result.get('confidence', 0.0)
                }

                self.results.append(test_result)
                print(f"   {test_result['statut']} - Confiance: {test_result['confiance_ocr']:.2f}")

            except Exception as e:
                print(f"   Erreur lors du test {var_name}: {e}")
                self.results.append({
                    'nom_fichier': f"{var_name}.jpg",
                    'statut': '❌ Erreur',
                    'erreur': str(e)
                })

    def extract_values_from_ocr(self, ocr_result):
        """Extrait les valeurs du résultat OCR"""
        payload = ocr_result.get('structured_payload', {})

        return {
            'nom': payload.get('nom', ''),
            'prenom': payload.get('prenom', ''),
            'date_naissance': payload.get('date_naissance', ''),
            'numero_doc': payload.get('numero_doc', ''),
            'sexe': payload.get('sexe', ''),
            'nationalite': payload.get('nationalite', ''),
            'date_expiration': payload.get('date_expiration', ''),
            'lieu_naissance': payload.get('lieu_naissance', ''),  # Note: c'est place_of_birth dans structured_info
            'photo_presente': self.detect_photo_presence(ocr_result)
        }

    def detect_photo_presence(self, ocr_result):
        """Détecte la présence de photo (simulation basée sur la confiance)"""
        # Pour cette simulation, on considère qu'une photo est présente si la confiance > 0.5
        # Dans un vrai système, cela nécessiterait une détection d'objet dédiée
        confidence = ocr_result.get('confidence', 0.0)
        return confidence > 0.5

    def compare_to_ground_truth(self, ocr_result, ground_truth, var_name):
        """Compare les résultats OCR avec la vérité terrain"""
        extracted = self.extract_values_from_ocr(ocr_result)
        differences = []
        exact_match = True

        for field in ground_truth.keys():
            expected = str(ground_truth[field]).upper().strip()
            actual = str(extracted.get(field, '')).upper().strip()

            # Normalisation spéciale pour certains champs
            if field in ['date_naissance', 'date_expiration']:
                # Normaliser les formats de date
                expected = self.normalize_date(expected)
                actual = self.normalize_date(actual)
            elif field == 'num_document':
                # Gestion spéciale pour la confusion O/0
                if var_name == 'o_zero_confusion':
                    expected = expected.replace('O', '0')
                    actual = actual.replace('O', '0')

            # Comparaison exacte
            if expected != actual:
                exact_match = False
                differences.append({
                    'champ': field,
                    'attendu': ground_truth[field],
                    'extrait': extracted.get(field, ''),
                    'difference': f"'{extracted.get(field, '')}' != '{ground_truth[field]}'"
                })

        return {
            'exact_match': exact_match,
            'differences': differences
        }

    def normalize_date(self, date_str):
        """Normalise une date au format YYYY-MM-DD"""
        if not date_str:
            return ''

        # Essayer différents formats
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y', '%Y/%m/%d']
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except:
                continue
        return date_str

    def generate_report(self):
        """Génère le rapport final"""
        print("\n=== RAPPORT DE PRÉCISION OCR ===\n")

        successful_tests = sum(1 for r in self.results if r.get('statut') == '✅ Réussi')
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"Tests réussis: {successful_tests}/{total_tests} ({success_rate:.1f}%)")

        if success_rate < 100:
            print("\n❌ L'OCR n'atteint pas 100% de précision. Échecs détaillés:")
            for result in self.results:
                if result.get('statut') == '❌ Échec':
                    print(f"\n--- {result['nom_fichier']} ---")
                    for diff in result.get('differences', []):
                        print(f"  Champ: {diff['champ']}")
                        print(f"    Attendu: {diff['attendu']}")
                        print(f"    Extrait: {diff['extrait']}")

        # Sauvegarder le rapport détaillé
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': success_rate,
                'precision_100_percent': success_rate == 100.0
            },
            'results': self.results
        }

        report_path = "ocr_accuracy_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nRapport détaillé sauvegardé dans: {report_path}")

        # Nettoyer les images de test
        self.cleanup_test_images()

        return success_rate == 100.0

    def cleanup_test_images(self):
        """Nettoie les images de test temporaires"""
        if os.path.exists(self.test_images_dir):
            for filename in os.listdir(self.test_images_dir):
                file_path = os.path.join(self.test_images_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Erreur suppression {file_path}: {e}")

            try:
                os.rmdir(self.test_images_dir)
                print("Images de test nettoyées.")
            except Exception as e:
                print(f"Erreur suppression dossier test: {e}")

def main():
    """Fonction principale"""
    print("Initialisation des tests de précision OCR...")

    tester = OCRAccuracyTester()

    print("Création des variations d'images...")
    if not tester.create_image_variations():
        print("Impossible de créer les variations d'images. Arrêt.")
        return

    print("Exécution des tests OCR...")
    tester.run_accuracy_tests()

    print("Génération du rapport...")
    success = tester.generate_report()

    if success:
        print("\n🎉 L'OCR atteint 100% de précision sur tous les tests!")
    else:
        print("\n⚠️  L'OCR nécessite des améliorations pour atteindre 100% de précision.")

if __name__ == "__main__":
    main()
