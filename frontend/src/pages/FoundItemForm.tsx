import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, AlertCircle, CheckCircle, Upload, X } from 'lucide-react';
import { toast } from 'react-toastify';
import apiService from '../services/api.ts';
import { DocumentType, FoundItemCreate } from '../types/api.ts';

const FoundItemForm: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const [formData, setFormData] = useState<FoundItemCreate>({
    document_type_id: 0,
    image: null as any,
    found_date: '',
    found_location: '',
    description: '',
    contact_phone: '',
    contact_email: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof FoundItemCreate, string>>>({});

  useEffect(() => {
    fetchDocumentTypes();
  }, []);

  const fetchDocumentTypes = async () => {
    try {
      const response = await apiService.getDocumentTypes();
      setDocumentTypes(response.data.results || response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des types de documents:', error);
      toast.error('Erreur lors du chargement des types de documents');
    } finally {
      setLoadingTypes(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof FoundItemCreate, string>> = {};

    if (!formData.document_type_id) {
      newErrors.document_type_id = 'Type de document requis';
    }
    if (!formData.image) {
      newErrors.image = 'Image du document requise';
    }
    if (!formData.found_date) {
      newErrors.found_date = 'Date de trouvaille requise';
    }
    if (!formData.found_location.trim()) {
      newErrors.found_location = 'Lieu de trouvaille requis';
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Description requise';
    }
    if (!formData.contact_phone.trim()) {
      newErrors.contact_phone = 'Téléphone de contact requis';
    }
    if (!formData.contact_email.trim()) {
      newErrors.contact_email = 'Email de contact requis';
    } else if (!/\S+@\S+\.\S+/.test(formData.contact_email)) {
      newErrors.contact_email = 'Email invalide';
    }

    // Validation des dates
    if (formData.found_date && new Date(formData.found_date) > new Date()) {
      newErrors.found_date = 'La date de trouvaille ne peut pas être dans le futur';
    }

    // Validation de l'image
    if (formData.image) {
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
      if (!allowedTypes.includes(formData.image.type)) {
        newErrors.image = 'Format d\'image non supporté (JPEG, PNG, GIF uniquement)';
      }
      if (formData.image.size > 10 * 1024 * 1024) { // 10MB
        newErrors.image = 'L\'image ne doit pas dépasser 10MB';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'document_type_id' ? parseInt(value) || 0 : value
    }));

    // Clear error when user starts typing
    if (errors[name as keyof FoundItemCreate]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData(prev => ({
        ...prev,
        image: file
      }));

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);

      // Clear error
      if (errors.image) {
        setErrors(prev => ({
          ...prev,
          image: undefined
        }));
      }
    }
  };

  const removeImage = () => {
    setFormData(prev => ({
      ...prev,
      image: null as any
    }));
    setImagePreview(null);
    // Clear error
    if (errors.image) {
      setErrors(prev => ({
        ...prev,
        image: undefined
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error('Veuillez corriger les erreurs dans le formulaire');
      return;
    }

    setLoading(true);
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('document_type_id', formData.document_type_id.toString());
      formDataToSend.append('image', formData.image);
      formDataToSend.append('found_date', formData.found_date);
      formDataToSend.append('found_location', formData.found_location);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('contact_phone', formData.contact_phone);
      formDataToSend.append('contact_email', formData.contact_email);

      await apiService.createFoundItem(formDataToSend);
      toast.success('Déclaration de trouvaille enregistrée avec succès !');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Erreur détaillée:', error.response?.data || error);
      
      // Message d'erreur plus détaillé
      const errorMessage = error.response?.data?.detail 
        || error.response?.data?.message 
        || error.message 
        || 'Erreur lors de l\'enregistrement';
      
      toast.error(`Erreur: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  if (loadingTypes) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Retour au tableau de bord
        </button>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Déclarer une trouvaille
        </h1>
        <p className="text-gray-600">
          Vous avez trouvé une pièce d'identité ? Téléchargez une photo claire du document.
          Notre système d'OCR extraira automatiquement les informations pour faciliter les retrouvailles.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white shadow-lg rounded-lg p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Type de document */}
          <div className="md:col-span-2">
            <label htmlFor="document_type_id" className="block text-sm font-medium text-gray-700 mb-2">
              Type de document *
            </label>
            <select
              id="document_type_id"
              name="document_type_id"
              value={formData.document_type_id}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.document_type_id ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value={0}>Sélectionnez un type de document</option>
              {documentTypes.map(type => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
            {errors.document_type_id && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.document_type_id}
              </p>
            )}
          </div>

          {/* Upload d'image */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Photo du document *
            </label>
            {!imagePreview ? (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-500 transition-colors">
                <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <div className="text-sm text-gray-600 mb-2">
                  Cliquez pour sélectionner une image ou glissez-déposez
                </div>
                <div className="text-xs text-gray-500">
                  JPEG, PNG, GIF jusqu'à 10MB
                </div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            ) : (
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Aperçu du document"
                  className="w-full h-64 object-cover rounded-lg border"
                />
                <button
                  type="button"
                  onClick={removeImage}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}
            {errors.image && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.image}
              </p>
            )}
          </div>

          {/* Date de trouvaille */}
          <div>
            <label htmlFor="found_date" className="block text-sm font-medium text-gray-700 mb-2">
              Date de trouvaille *
            </label>
            <input
              type="date"
              id="found_date"
              name="found_date"
              value={formData.found_date}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.found_date ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.found_date && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.found_date}
              </p>
            )}
          </div>

          {/* Lieu de trouvaille */}
          <div>
            <label htmlFor="found_location" className="block text-sm font-medium text-gray-700 mb-2">
              Lieu de trouvaille *
            </label>
            <input
              type="text"
              id="found_location"
              name="found_location"
              value={formData.found_location}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.found_location ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Paris, Métro Châtelet"
            />
            {errors.found_location && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.found_location}
              </p>
            )}
          </div>

          {/* Téléphone de contact */}
          <div>
            <label htmlFor="contact_phone" className="block text-sm font-medium text-gray-700 mb-2">
              Téléphone de contact *
            </label>
            <input
              type="tel"
              id="contact_phone"
              name="contact_phone"
              value={formData.contact_phone}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.contact_phone ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="06 12 34 56 78"
            />
            {errors.contact_phone && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.contact_phone}
              </p>
            )}
          </div>

          {/* Email de contact */}
          <div>
            <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700 mb-2">
              Email de contact *
            </label>
            <input
              type="email"
              id="contact_email"
              name="contact_email"
              value={formData.contact_email}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.contact_email ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="jean.dupont@email.com"
            />
            {errors.contact_email && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.contact_email}
              </p>
            )}
          </div>

          {/* Description */}
          <div className="md:col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              id="description"
              name="description"
              rows={4}
              value={formData.description}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.description ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Décrivez les circonstances de la trouvaille, l'état du document, etc."
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.description}
              </p>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-8 flex justify-end">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="mr-4 px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Annuler
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Enregistrement...
              </>
            ) : (
              <>
                <Save className="h-5 w-5 mr-2" />
                Déclarer la trouvaille
              </>
            )}
          </button>
        </div>
      </form>

      {/* Info Section */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <CheckCircle className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Conseils pour une déclaration réussie
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Prenez une photo claire et nette du document</li>
                <li>Assurez-vous que toutes les informations sont lisibles</li>
                <li>Ne partagez pas d'informations sensibles dans la description</li>
                <li>Notre système OCR extraira automatiquement les données du document</li>
                <li>Vous serez notifié en cas de correspondance avec une déclaration de perte</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FoundItemForm;
