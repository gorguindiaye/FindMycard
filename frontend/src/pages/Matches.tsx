import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle, Clock, AlertCircle, Eye } from 'lucide-react';
import { toast } from 'react-toastify';
import apiService from '../services/api.ts';
import { Match } from '../types/api';
import Loader from '../components/Loader.tsx';

const Matches: React.FC = () => {
  const navigate = useNavigate();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMatches();
  }, []);

  const fetchMatches = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getMatches();
      setMatches(response.data.results || response.data);
    } catch (err: any) {
      console.error('Erreur lors du chargement des correspondances:', err);
      setError('Erreur lors du chargement des correspondances');
      toast.error('Erreur lors du chargement des correspondances');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: Match['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'confirmed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'completed':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: Match['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'confirmed':
        return <CheckCircle className="h-4 w-4" />;
      case 'rejected':
        return <XCircle className="h-4 w-4" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const renderCriteria = (criteria: Match['match_criteria']) => {
    if (!criteria) return [];
    if (Array.isArray(criteria)) {
      return criteria;
    }
    if (typeof criteria === 'object') {
      return Object.entries(criteria).map(([key, value]) => {
        if (value && typeof value === 'object') {
          return `${key}`;
        }
        return `${key}: ${String(value)}`;
      });
    }
    return [];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const viewMatchDetails = (matchId: number) => {
    // Pour l'instant, navigation vers une page de détails (à implémenter)
    toast.info('Détails de la correspondance en cours de développement');
    // navigate(`/matches/${matchId}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Erreur</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchMatches}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Retour au tableau de bord
        </button>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Correspondances
            </h1>
            <p className="text-gray-600 mt-1">
              {matches.length > 0
                ? `${matches.length} correspondance${matches.length > 1 ? 's' : ''} trouvée${matches.length > 1 ? 's' : ''}`
                : 'Aucune correspondance trouvée'
              }
            </p>
          </div>
          <button
            onClick={fetchMatches}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 flex items-center"
            disabled={loading}
          >
            <span className="sr-only">Actualiser</span>
            ↻
          </button>
        </div>
      </div>

      {/* Matches List */}
      {matches.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Aucune correspondance pour le moment
          </h3>
          <p className="text-gray-600 mb-4">
            Les correspondances apparaîtront ici dès qu'une correspondance est détectée entre vos déclarations.
          </p>
          <div className="space-y-1 text-sm text-gray-500">
            <p>• Ajoutez plus de déclarations de perte ou de trouvaille</p>
            <p>• Le système analyse automatiquement les correspondances</p>
            <p>• Vous serez notifié par email en cas de correspondance</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {matches.map((match) => (
            <div key={match.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-2">
                  <div className={`px-2 py-1 rounded-full text-xs font-medium border flex items-center space-x-1 ${getStatusColor(match.status)}`}>
                    {getStatusIcon(match.status)}
                    <span>{match.status === 'pending' ? 'En attente' : match.status === 'confirmed' ? 'Confirmée' : match.status === 'rejected' ? 'Rejetée' : 'Terminée'}</span>
                  </div>
                </div>
                <button
                  onClick={() => viewMatchDetails(match.id)}
                  className="text-primary-600 hover:text-primary-800 p-1 rounded-full hover:bg-primary-50"
                  title="Voir les détails"
                >
                  <Eye className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Confidence Score */}
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-900">
                    Score de confiance: {(match.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>

                {/* Match Criteria */}
                {renderCriteria(match.match_criteria).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Critères de correspondance</h4>
                    <div className="flex flex-wrap gap-1">
                      {renderCriteria(match.match_criteria).map((criterion, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full"
                        >
                          {criterion}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Lost Item Summary */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                    <span className="mr-2">📄</span>
                    Objet perdu
                  </h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Propriétaire:</strong> {match.lost_item.first_name} {match.lost_item.last_name}</p>
                    <p><strong>Type:</strong> {match.lost_item.document_type.name}</p>
                    <p><strong>Perdu le:</strong> {formatDate(match.lost_item.lost_date)}</p>
                    <p><strong>Lieu:</strong> {match.lost_item.lost_location}</p>
                  </div>
                </div>

                {/* Found Item Summary */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                    <span className="mr-2">🔍</span>
                    Objet trouvé
                  </h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Trouvé le:</strong> {formatDate(match.found_item.found_date)}</p>
                    <p><strong>Lieu:</strong> {match.found_item.found_location}</p>
                    {match.found_item.first_name && (
                      <p><strong>Nom (OCR):</strong> {match.found_item.first_name} {match.found_item.last_name}</p>
                    )}
                    <p><strong>Confiance OCR:</strong> {match.found_item.ocr_confidence ? `${(match.found_item.ocr_confidence * 100).toFixed(1)}%` : 'N/A'}</p>
                  </div>
                </div>

                {/* Timestamps */}
                <div className="text-xs text-gray-500 space-y-1 pt-2 border-t border-gray-200">
                  <p><strong>Créée:</strong> {formatDate(match.created_at)}</p>
                  {match.updated_at !== match.created_at && (
                    <p><strong>Mise à jour:</strong> {formatDate(match.updated_at)}</p>
                  )}
                </div>
              </div>

              {/* Actions based on status */}
              <div className="mt-4 pt-4 border-t border-gray-200 flex justify-end space-x-2">
                {match.status === 'pending' && (
                  <>
                    <button
                      onClick={() => toast.info('Fonctionnalité en développement')}
                      className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-md hover:bg-green-200 flex items-center"
                    >
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Confirmer
                    </button>
                    <button
                      onClick={() => toast.info('Fonctionnalité en développement')}
                      className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded-md hover:bg-red-200 flex items-center"
                    >
                      <XCircle className="h-3 w-3 mr-1" />
                      Rejeter
                    </button>
                  </>
                )}
                {match.status === 'confirmed' && (
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-md">
                    Correspondance confirmée
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Matches;
