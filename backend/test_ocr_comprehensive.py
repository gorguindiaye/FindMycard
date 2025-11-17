#!/usr/bin/env python3
"""
Test complet de la fonctionnalité OCR avec différents scénarios
"""
import os
import cv2
import numpy as np
import json
import time
from datetime import datetime
from ocr.services import OCRService

class OCRComprehensiveTester:
    def __init__(self):
        self.test_image_path = "images/Carte.jpg"
        self.results = []

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("=== TESTS COMPREHENSIFS OCR ===\n")

        # Test 1: Image originale
        self.test_original_image()

        # Test 2: Image tournée
        self.test_rotated_image()

        # Test 3: Image avec bruit
        self.test_noisy_image()

        # Test 4: Image floue
        self.test_blurry_image()

        # Test 5: Image sombre
        self.test_dark_image()

        # Test 6: Performance
        self.test_performance()

        # Test 7: Différents types de documents simulés
        self.test_document_types()

        # Test 8: Cas limites
        self.test_edge_cases()

        # Rapport final
        self.generate_report()

    def test_original_image(self):
        """Test avec l'image originale"""
        print("1. Test image originale...")
        if os.path.exists(self.test_image_path):
            start_time = time.time()
            result = OCRService.process_image(self.test_image_path)
            processing_time = time.time() - start_time

            self.results.append({
                'test': 'original_image',
                'result': result,
                'processing_time': processing_time,
                'status': 'success'
            })
            print(f"   ✓ Terminé en {processing_time:.2f}s")
        else:
            print("   ✗ Image test non trouvée")
            self.results.append({
                'test': 'original_image',
                'status': 'failed',
                'error': 'Image not found'
            })

    def test_rotated_image(self):
        """Test avec image tournée"""
        print("2. Test image tournée...")
        if os.path.exists(self.test_image_path):
            # Créer une version tournée
            image = cv2.imread(self.test_image_path)
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 15, 1.0)  # Rotation de 15 degrés
            rotated = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

            rotated_path = "images/test_rotated.jpg"
            cv2.imwrite(rotated_path, rotated)

            start_time = time.time()
            result = OCRService.process_image(rotated_path)
            processing_time = time.time() - start_time

            self.results.append({
                'test': 'rotated_image',
                'result': result,
                'processing_time': processing_time,
                'status': 'success'
            })
            print(f"   ✓ Terminé en {processing_time:.2f}s")

            # Nettoyer
            if os.path.exists(rotated_path):
                os.remove(rotated_path)
        else:
            self.results.append({
                'test': 'rotated_image',
                'status': 'failed',
                'error': 'Base image not found'
            })

    def test_noisy_image(self):
        """Test avec image bruitée"""
        print("3. Test image bruitée...")
        if os.path.exists(self.test_image_path):
            image = cv2.imread(self.test_image_path)

            # Ajouter du bruit gaussien
            row, col, ch = image.shape
            mean = 0
            var = 0.1
            sigma = var**0.5
            gauss = np.random.normal(mean, sigma, (row, col, ch))
            gauss = gauss.reshape(row, col, ch)
            noisy = image + gauss

            # S'assurer que les valeurs sont dans [0, 255]
            noisy = np.clip(noisy, 0, 255).astype(np.uint8)

            noisy_path = "images/test_noisy.jpg"
            cv2.imwrite(noisy_path, noisy)

            start_time = time.time()
            result = OCRService.process_image(noisy_path)
            processing_time = time.time() - start_time

            self.results.append({
                'test': 'noisy_image',
                'result': result,
                'processing_time': processing_time,
                'status': 'success'
            })
            print(f"   ✓ Terminé en {processing_time:.2f}s")

            # Nettoyer
            if os.path.exists(noisy_path):
                os.remove(noisy_path)
        else:
            self.results.append({
                'test': 'noisy_image',
                'status': 'failed',
                'error': 'Base image not found'
            })

    def test_blurry_image(self):
        """Test avec image floue"""
        print("4. Test image floue...")
        if os.path.exists(self.test_image_path):
            image = cv2.imread(self.test_image_path)

            # Appliquer un flou gaussien
            blurred = cv2.GaussianBlur(image, (5, 5), 0)

            blurred_path = "images/test_blurred.jpg"
            cv2.imwrite(blurred_path, blurred)

            start_time = time.time()
            result = OCRService.process_image(blurred_path)
            processing_time = time.time() - start_time

            self.results.append({
                'test': 'blurry_image',
                'result': result,
                'processing_time': processing_time,
                'status': 'success'
            })
            print(f"   ✓ Terminé en {processing_time:.2f}s")

            # Nettoyer
            if os.path.exists(blurred_path):
                os.remove(blurred_path)
        else:
            self.results.append({
                'test': 'blurry_image',
                'status': 'failed',
                'error': 'Base image not found'
            })

    def test_dark_image(self):
        """Test avec image sombre"""
        print("5. Test image sombre...")
        if os.path.exists(self.test_image_path):
            image = cv2.imread(self.test_image_path)

            # Assombrir l'image
            dark = cv2.convertScaleAbs(image, alpha=0.3, beta=0)

            dark_path = "images/test_dark.jpg"
            cv2.imwrite(dark_path, dark)

            start_time = time.time()
            result = OCRService.process_image(dark_path)
            processing_time = time.time() - start_time

            self.results.append({
                'test': 'dark_image',
                'result': result,
                'processing_time': processing_time,
                'status': 'success'
            })
            print(f"   ✓ Terminé en {processing_time:.2f}s")

            # Nettoyer
            if os.path.exists(dark_path):
                os.remove(dark_path)
        else:
            self.results.append({
                'test': 'dark_image',
                'status': 'failed',
                'error': 'Base image not found'
            })

    def test_performance(self):
        """Test de performance"""
        print("6. Test de performance...")
        if os.path.exists(self.test_image_path):
            times = []
            for i in range(5):  # 5 exécutions
                start_time = time.time()
                result = OCRService.process_image(self.test_image_path)
                processing_time = time.time() - start_time
                times.append(processing_time)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            self.results.append({
                'test': 'performance',
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'status': 'success'
            })
            print(f"   ✓ Moyenne: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s")
        else:
            self.results.append({
                'test': 'performance',
                'status': 'failed',
                'error': 'Base image not found'
            })

    def test_document_types(self):
        """Test avec différents types de documents simulés"""
        print("7. Test types de documents...")

        # Simuler différents types de texte
        test_texts = {
            'carte_identite': "CARTE NATIONALE D'IDENTITÉ\nRÉPUBLIQUE FRANÇAISE\nNom: DUPONT\nPrénom: Jean\nNé le: 15/05/1985\nÀ: Paris",
            'passeport': "RÉPUBLIQUE FRANÇAISE\nPASSEPORT\nType: P\nPays: FRA\nNom: DUPONT\nPrénoms: Jean Pierre",
            'permis_conduire': "RÉPUBLIQUE FRANÇAISE\nPERMIS DE CONDUIRE\nNom: DUPONT\nPrénom: Jean\nNé le: 15.05.1985"
        }

        for doc_type, text in test_texts.items():
            # Classification du texte
            classified_type = OCRService.classify_document_type(text)

            self.results.append({
                'test': f'document_type_{doc_type}',
                'expected_type': doc_type,
                'classified_type': classified_type,
                'text': text,
                'status': 'success'
            })
            print(f"   ✓ {doc_type}: {classified_type}")

    def test_edge_cases(self):
        """Test des cas limites"""
        print("8. Test cas limites...")

        # Test avec image vide
        try:
            empty_image = np.zeros((100, 100, 3), dtype=np.uint8)
            empty_path = "images/test_empty.jpg"
            cv2.imwrite(empty_path, empty_image)

            result = OCRService.process_image(empty_path)
            self.results.append({
                'test': 'empty_image',
                'result': result,
                'status': 'success'
            })
            print("   ✓ Image vide gérée")

            if os.path.exists(empty_path):
                os.remove(empty_path)
        except Exception as e:
            self.results.append({
                'test': 'empty_image',
                'status': 'failed',
                'error': str(e)
            })

        # Test avec chemin inexistant
        try:
            result = OCRService.process_image("images/nonexistent.jpg")
            self.results.append({
                'test': 'nonexistent_file',
                'result': result,
                'status': 'success'
            })
            print("   ✓ Fichier inexistant géré")
        except Exception as e:
            self.results.append({
                'test': 'nonexistent_file',
                'status': 'failed',
                'error': str(e)
            })

    def generate_report(self):
        """Génère un rapport des tests"""
        print("\n=== RAPPORT DES TESTS ===\n")

        successful_tests = 0
        total_tests = len(self.results)

        for result in self.results:
            if result['status'] == 'success':
                successful_tests += 1

        print(f"Tests réussis: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")

        # Statistiques de performance
        performance_tests = [r for r in self.results if r['test'] == 'performance']
        if performance_tests:
            perf = performance_tests[0]
            print(f"\nPerformance moyenne: {perf['avg_time']:.2f}s")
            print(f"Performance min/max: {perf['min_time']:.2f}s / {perf['max_time']:.2f}s")

        # Analyse des résultats OCR
        ocr_tests = [r for r in self.results if 'result' in r and 'structured_info' in r.get('result', {})]
        if ocr_tests:
            confidences = [r['result']['confidence'] for r in ocr_tests if r['result']['confidence'] > 0]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                print(f"\nConfiance OCR moyenne: {avg_confidence:.2f}")

        # Sauvegarder les résultats détaillés
        report_path = "ocr_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'success_rate': successful_tests/total_tests*100
                },
                'results': self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\nRapport détaillé sauvegardé dans: {report_path}")

if __name__ == "__main__":
    tester = OCRComprehensiveTester()
    tester.run_all_tests()
