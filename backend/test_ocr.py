import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findmyid.settings')
import django
django.setup()
from ocr.services import OCRService
result = OCRService.process_image(r'c:/Users/Administrator/Desktop/FindMyCard/images/Carte.jpg')
import json
print(json.dumps(result, default=str, indent=2))
