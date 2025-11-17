import React, { useState, useEffect } from 'react';
import { Search as SearchIcon, Filter, MapPin, Calendar, User, Eye } from 'lucide-react';
import { toast } from 'react-toastify';
import axios from 'axios';
import { LostItem, DocumentType } from '../types/api';
import Loader from '../components/Loader.tsx';

const API_BASE_URL = 'http://localhost:8000/api';

const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<LostItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [selectedType, setSelectedType] = useState<number | ''>('');
  const [location, setLocation] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchDocumentTypes();
  }, []);

  const fetchDocumentTypes = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_BASE_URL}/document-types/`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setDocumentTypes(response.data.results || response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des types de documents:', error);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() && !selectedType && !location.trim()) {
      toast.warning('Veuillez saisir au moins un critère de recherche');
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const params: any = {};

      if (query.trim()) {
        params.search = query.trim();
      }

      if (selectedType) {
        params.document_type = selectedType;
      }

      if (location.trim()) {
        params.lost_location = location.trim();
      }

      const response = await axios.get(`${API_BASE_URL}/lost-items/`, {
        params,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setResults(response.data.results || response.data);
    } catch (error: any) {
      console.error('Erreur lors de la recherche:', error);
      toast.error('Erreur lors de la recherche');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const clearFilters = () => {
    setQuery('');
    setSelectedType('');
    setLocation('');
    setResults([]);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900">
            Rechercher des objets perdus
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Trouvez des objets perdus déclarés par d'autres utilisateurs
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            {/* Main Search Input */}
            <div className="flex">
              <div className="relative flex-grow">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <SearchIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-l-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Description, nom, numéro de document..."
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center px-6 py-3 border border-transparent text-sm font-medium rounded-r-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {loading ? 'Recherche...' : 'Rechercher'}
              </button>
            </div>

            {/* Filters Toggle */}
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center text-sm text-gray-600 hover:text-gray-900"
              >
                <Filter className="h-4 w-4 mr-1" />
                {showFilters ? 'Masquer les filtres' : 'Afficher les filtres'}
              </button>
              {(query || selectedType || location) && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Effacer les filtres
                </button>
              )}
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <label htmlFor="documentType" className="block text-sm font-medium text-gray-700 mb-1">
                    Type de document
                  </label>
                  <select
                    id="documentType"
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value ? Number(e.target.value) : '')}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">Tous les types</option>
                    {documentTypes.map((type) => (
                      <option key={type.id} value={type.id}>
                        {type.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                    Lieu de perte
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <MapPin className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      id="location"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Ville, quartier..."
                    />
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>

        {/* Results */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Résultats de recherche
            </h2>
            {results.length > 0 && (
              <span className="text-sm text-gray-600">
                {results.length} résultat{results.length > 1 ? 's' : ''} trouvé{results.length > 1 ? 's' : ''}
              </span>
            )}
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <Loader />
            </div>
          ) : results.length === 0 ? (
            <div className="bg-white shadow rounded-lg p-8 text-center">
              <SearchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Aucun résultat trouvé
              </h3>
              <p className="text-gray-600 mb-4">
                Essayez d'autres mots-clés ou critères de recherche.
              </p>
              <div className="text-sm text-gray-500">
                <p>• Vérifiez l'orthographe des termes recherchés</p>
                <p>• Utilisez des mots-clés plus généraux</p>
                <p>• Essayez de rechercher par type de document</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {results.map((item) => (
                <div key={item.id} className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Perdu
                        </span>
                        <span className="text-sm text-gray-500">
                          {item.document_type.name}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {item.first_name} {item.last_name}
                      </h3>
                      <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center">
                      <MapPin className="h-4 w-4 mr-2 text-gray-400" />
                      <span>Perdu à {item.lost_location}</span>
                    </div>
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                      <span>Le {formatDate(item.lost_date)}</span>
                    </div>
                    <div className="flex items-center">
                      <User className="h-4 w-4 mr-2 text-gray-400" />
                      <span>Contact: {item.contact_phone}</span>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between items-center">
                    <span className="text-xs text-gray-500">
                      Déclaré le {formatDate(item.created_at)}
                    </span>
                    <button
                      onClick={() => toast.info('Fonctionnalité en développement')}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200"
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      Voir détails
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Help Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">
            Conseils de recherche
          </h3>
          <div className="text-sm text-blue-800 space-y-1">
            <p>• Utilisez des mots-clés précis comme "carte d'identité", "passeport", "permis de conduire"</p>
            <p>• Incluez des détails spécifiques comme des numéros ou des noms</p>
            <p>• Filtrez par type de document pour affiner les résultats</p>
            <p>• Recherchez par lieu si vous connaissez l'endroit approximatif</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Search;
