import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import apiService from '../services/api.ts';
import { DocumentType, LostItemCreate } from '../types/api.ts';

const LostItemForm: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(true);

  const [formData, setFormData] = useState<LostItemCreate>({
    document_type_id: 0,
    first_name: '',
    last_name: '',
    date_of_birth: '',
    lost_date: '',
    lost_location: '',
    description: '',
    contact_phone: '',
    contact_email: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof LostItemCreate, string>>>({});

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
    const newErrors: Partial<Record<keyof LostItemCreate, string>> = {};

    if (!formData.document_type_id) {
      newErrors.document_type_id = 'Type de document requis';
    }
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'Prénom requis';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Nom requis';
    }
    if (!formData.date_of_birth) {
      newErrors.date_of_birth = 'Date de naissance requise';
    }

    if (!formData.lost_date) {
      newErrors.lost_date = 'Date de perte requise';
    }
    if (!formData.lost_location.trim()) {
      newErrors.lost_location = 'Lieu de perte requis';
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
    if (formData.date_of_birth && new Date(formData.date_of_birth) > new Date()) {
      newErrors.date_of_birth = 'La date de naissance ne peut pas être dans le futur';
    }
    if (formData.lost_date && new Date(formData.lost_date) > new Date()) {
      newErrors.lost_date = 'La date de perte ne peut pas être dans le futur';
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
    if (errors[name as keyof LostItemCreate]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined
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
      await apiService.createLostItem(formData);
      toast.success('Déclaration de perte enregistrée avec succès !');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Erreur lors de la création:', error);
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.message ||
                          'Erreur lors de l\'enregistrement';
      toast.error(errorMessage);
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
          Déclarer une perte
        </h1>
        <p className="text-gray-600">
          Remplissez ce formulaire pour déclarer la perte d'une pièce d'identité.
          Plus vos informations sont précises, plus les chances de retrouvailles sont élevées.
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

          {/* Prénom */}
          <div>
            <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
              Prénom *
            </label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.first_name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Jean"
            />
            {errors.first_name && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.first_name}
              </p>
            )}
          </div>

          {/* Nom */}
          <div>
            <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
              Nom *
            </label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.last_name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Dupont"
            />
            {errors.last_name && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.last_name}
              </p>
            )}
          </div>

          {/* Date de naissance */}
          <div>
            <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700 mb-2">
              Date de naissance *
            </label>
            <input
              type="date"
              id="date_of_birth"
              name="date_of_birth"
              value={formData.date_of_birth}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.date_of_birth ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.date_of_birth && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.date_of_birth}
              </p>
            )}
          </div>



          {/* Date de perte */}
          <div>
            <label htmlFor="lost_date" className="block text-sm font-medium text-gray-700 mb-2">
              Date de perte *
            </label>
            <input
              type="date"
              id="lost_date"
              name="lost_date"
              value={formData.lost_date}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.lost_date ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.lost_date && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.lost_date}
              </p>
            )}
          </div>

          {/* Lieu de perte */}
          <div>
            <label htmlFor="lost_location" className="block text-sm font-medium text-gray-700 mb-2">
              Lieu de perte *
            </label>
            <input
              type="text"
              id="lost_location"
              name="lost_location"
              value={formData.lost_location}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.lost_location ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Paris, Métro Châtelet"
            />
            {errors.lost_location && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.lost_location}
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
              placeholder="Décrivez les circonstances de la perte, les signes distinctifs du document, etc."
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
                Déclarer la perte
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
              Conseils pour maximiser vos chances de retrouvailles
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Fournissez des informations aussi précises que possible</li>
                <li>Vérifiez régulièrement vos notifications pour les correspondances</li>
                <li>Signalez également la perte auprès des autorités compétentes</li>
                <li>Un document trouvé sera automatiquement comparé avec votre déclaration</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LostItemForm;
