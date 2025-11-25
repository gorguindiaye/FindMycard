import React, { useEffect, useMemo, useState } from 'react';
import { ClipboardCheck, Shield, Layers } from 'lucide-react';
import { toast } from 'react-toastify';
import Loader from '../components/Loader.tsx';
import apiService from '../services/api.ts';

interface DocumentSummary {
  document_type?: { name: string };
  first_name?: string;
  last_name?: string;
}

interface MatchSummary {
  id: number;
  confidence_score: number;
  lost_item: DocumentSummary;
  found_item: DocumentSummary;
}

interface VerificationRequest {
  id: number;
  status: 'pending' | 'in_review' | 'confirmed' | 'rejected' | 'supervised';
  notes: string;
  decision_reason: string;
  match: MatchSummary;
  created_at: string;
}

type DecisionType = 'confirm' | 'reject' | 'supervise';

const statusLabels: Record<string, string> = {
  pending: 'En attente',
  in_review: 'En cours',
  confirmed: 'Confirmée',
  rejected: 'Rejetée',
  supervised: 'Restituée',
};

const AdminPublic: React.FC = () => {
  const [requests, setRequests] = useState<VerificationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [decisionNotes, setDecisionNotes] = useState<Record<number, string>>({});

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const response = await apiService.getVerificationRequests();
      setRequests(response.data.results || response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des demandes', error);
      toast.error('Impossible de charger les demandes de vérification');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (type: DecisionType, requestId: number) => {
    try {
      setActionLoading(`${type}-${requestId}`);
      const note = decisionNotes[requestId];

      if (type === 'confirm') {
        await apiService.confirmVerificationRequest(requestId, note ? { reason: note } : undefined);
        toast.success('Authenticité confirmée');
      } else if (type === 'reject') {
        if (!note) {
          toast.error('Veuillez saisir un motif de refus');
          return;
        }
        await apiService.rejectVerificationRequest(requestId, { reason: note });
        toast.info('Correspondance rejetée');
      } else {
        await apiService.superviseVerificationRequest(requestId, note ? { notes: note } : undefined);
        toast.success('Restitution supervisée');
      }

      await fetchRequests();
    } catch (error) {
      console.error('Erreur lors du traitement de la demande', error);
      toast.error('Action impossible, réessayez plus tard');
    } finally {
      setActionLoading(null);
    }
  };

  const cards = useMemo(() => {
    const pending = requests.filter((r) => ['pending', 'in_review'].includes(r.status)).length;
    const confirmed = requests.filter((r) => r.status === 'confirmed').length;
    const supervised = requests.filter((r) => r.status === 'supervised').length;
    return [
      {
        title: 'Demandes en attente',
        value: pending,
        description: 'Pièces à vérifier avant restitution',
        icon: ClipboardCheck,
        accent: 'text-blue-600 bg-blue-100',
      },
      {
        title: 'Vérifications confirmées',
        value: confirmed,
        description: 'Authenticité validée par vos services',
        icon: Shield,
        accent: 'text-green-600 bg-green-100',
      },
      {
        title: 'Restitutions supervisées',
        value: supervised,
        description: 'Remises accompagnées par l’administration',
        icon: Layers,
        accent: 'text-purple-600 bg-purple-100',
      },
    ];
  }, [requests]);

  const history = useMemo(
    () =>
      requests
        .filter((r) => ['confirmed', 'rejected', 'supervised'].includes(r.status))
        .slice(0, 5),
    [requests]
  );

  const updateDecisionNote = (id: number, value: string) => {
    setDecisionNotes((prev) => ({ ...prev, [id]: value }));
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Portail Administration Publique</h1>
        <p className="text-gray-600">
          Validez l’authenticité des documents et suivez les restitutions sensibles.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader />
        </div>
      ) : (
        <>
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {cards.map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.title} className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                  <div className={`inline-flex rounded-full ${card.accent.split(' ')[1]} ${card.accent.split(' ')[0]} p-3`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <p className="mt-4 text-sm font-medium text-gray-500">{card.title}</p>
                  <p className="mt-1 text-3xl font-semibold text-gray-900">{card.value}</p>
                  <p className="mt-1 text-sm text-gray-500">{card.description}</p>
                </div>
              );
            })}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">Demandes de vérification</h2>
              <p className="mt-1 text-sm text-gray-500">
                Gérez les dossiers transmis par l’administrateur plateforme.
              </p>

              <div className="mt-4 space-y-4">
                {requests.length === 0 && (
                  <div className="rounded-lg border border-dashed border-gray-200 p-6 text-center text-gray-500">
                    Aucune demande à traiter.
                  </div>
                )}

                {requests.map((request) => (
                  <div key={request.id} className="rounded-lg border border-gray-100 p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-semibold text-gray-900">Dossier #{request.id}</p>
                        <p className="text-xs text-gray-500">
                          Reçu le {new Date(request.created_at).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                      <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
                        {statusLabels[request.status] || request.status}
                      </span>
                    </div>

                    <div className="mt-3 text-sm text-gray-600">
                      <p className="font-medium text-gray-900">Correspondance #{request.match.id}</p>
                      <p>
                        Perdu : {request.match.lost_item?.first_name} {request.match.lost_item?.last_name} (
                        {request.match.lost_item?.document_type?.name})
                      </p>
                      <p>
                        Trouvé : {request.match.found_item?.first_name || '—'} {request.match.found_item?.last_name || '—'}
                      </p>
                      <p>Score IA : {(request.match.confidence_score * 100).toFixed(1)}%</p>
                    </div>

                    <textarea
                      className="mt-3 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                      placeholder="Ajouter un commentaire ou un motif..."
                      value={decisionNotes[request.id] || ''}
                      onChange={(e) => updateDecisionNote(request.id, e.target.value)}
                    />

                    <div className="mt-4 flex flex-wrap gap-3">
                      {['pending', 'in_review'].includes(request.status) && (
                        <>
                          <button
                            onClick={() => handleDecision('confirm', request.id)}
                            disabled={actionLoading === `confirm-${request.id}`}
                            className="flex-1 rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                          >
                            Confirmer
                          </button>
                          <button
                            onClick={() => handleDecision('reject', request.id)}
                            disabled={actionLoading === `reject-${request.id}`}
                            className="flex-1 rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                          >
                            Refuser
                          </button>
                        </>
                      )}

                      {request.status === 'confirmed' && (
                        <button
                          onClick={() => handleDecision('supervise', request.id)}
                          disabled={actionLoading === `supervise-${request.id}`}
                          className="flex-1 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
                        >
                          Superviser la restitution
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">Historique</h2>
              <p className="mt-1 text-sm text-gray-500">Dernières décisions enregistrées.</p>
              <ul className="mt-4 space-y-4">
                {history.length === 0 && (
                  <li className="rounded-lg border border-dashed border-gray-200 p-6 text-center text-gray-500">
                    Aucune décision récente.
                  </li>
                )}

                {history.map((entry) => (
                  <li key={entry.id} className="flex items-start gap-3 rounded-lg border border-gray-100 p-4">
                    <span className="mt-1 h-2.5 w-2.5 rounded-full bg-primary-500" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Dossier #{entry.id} — {statusLabels[entry.status] || entry.status}
                      </p>
                      <p className="text-xs text-gray-500">
                        {entry.decision_reason || 'Décision enregistrée'}
                      </p>
                      <p className="text-xs text-gray-400">
                        {new Date(entry.created_at).toLocaleString('fr-FR')}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminPublic;

