import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Bell, BellOff, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { toast } from 'react-toastify';
import apiService from '../services/api.ts';
import { Notification } from '../types/api';
import Loader from '../components/Loader.tsx';

const Notifications: React.FC = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getNotifications();
      setNotifications(response.data.results || response.data);
    } catch (err: any) {
      console.error('Erreur lors du chargement des notifications:', err);
      setError('Erreur lors du chargement des notifications');
      toast.error('Erreur lors du chargement des notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: number) => {
    try {
      await apiService.markNotificationAsRead(notificationId);
      setNotifications(prev =>
        prev.map(notif =>
          notif.id === notificationId ? { ...notif, is_read: true } : notif
        )
      );
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour:', err);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiService.markAllNotificationsAsRead();
      setNotifications(prev =>
        prev.map(notif => ({ ...notif, is_read: true }))
      );
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour:', err);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const getNotificationIcon = (type: Notification['notification_type']) => {
    switch (type) {
      case 'match_found':
        return <Bell className="h-5 w-5 text-blue-500" />;
      case 'match_confirmed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'item_returned':
      case 'item_handed_over':
        return <CheckCircle className="h-5 w-5 text-purple-500" />;
      default:
        return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const getNotificationTypeText = (type: Notification['notification_type']) => {
    switch (type) {
      case 'match_found':
        return 'Correspondance trouvée';
      case 'match_confirmed':
        return 'Correspondance confirmée';
      case 'item_returned':
      case 'item_handed_over':
        return 'Objet rendu';
      default:
        return type;
    }
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

  const unreadCount = notifications.filter(n => !n.is_read).length;

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
            onClick={fetchNotifications}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
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
              Notifications
            </h1>
            <p className="text-gray-600 mt-1">
              {notifications.length > 0
                ? `${notifications.length} notification${notifications.length > 1 ? 's' : ''} ${unreadCount > 0 ? `(${unreadCount} non lue${unreadCount > 1 ? 's' : ''})` : '(toutes lues)'}`
                : 'Aucune notification'
              }
            </p>
          </div>
          <div className="flex space-x-2">
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 flex items-center"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Tout marquer comme lu
              </button>
            )}
            <button
              onClick={fetchNotifications}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 flex items-center"
              disabled={loading}
            >
              <span className="sr-only">Actualiser</span>
              ↻
            </button>
          </div>
        </div>
      </div>

      {/* Notifications List */}
      {notifications.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <BellOff className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Aucune notification
          </h3>
          <p className="text-gray-600 mb-4">
            Vous serez notifié ici dès qu'une correspondance sera trouvée ou confirmée.
          </p>
          <div className="space-y-1 text-sm text-gray-500">
            <p>• Nouvelles correspondances détectées</p>
            <p>• Confirmations de correspondances</p>
            <p>• Mises à jour sur vos déclarations</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={`bg-white rounded-lg shadow-sm border p-6 transition-all ${
                notification.is_read
                  ? 'border-gray-200 bg-gray-50'
                  : 'border-primary-200 bg-white shadow-md'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    {getNotificationIcon(notification.notification_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {notification.title}
                      </h3>
                      {!notification.is_read && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                          Nouveau
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 mb-3">
                      {notification.message}
                    </p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span className="flex items-center">
                        <span className="font-medium mr-1">Type:</span>
                        {getNotificationTypeText(notification.notification_type)}
                      </span>
                      <span className="flex items-center">
                        <span className="font-medium mr-1">Date:</span>
                        {formatDate(notification.created_at)}
                      </span>
                    </div>
                    {/* Match Details */}
                    {notification.match && (
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <h4 className="text-sm font-semibold text-gray-900 mb-2">
                          Détails de la correspondance
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="font-medium text-gray-900">Objet perdu</p>
                            <p className="text-gray-600">
                              {notification.match?.lost_item?.first_name} {notification.match?.lost_item?.last_name}
                            </p>
                            <p className="text-gray-600">
                              {notification.match?.lost_item?.document_type?.name}
                            </p>
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">Objet trouvé</p>
                            <p className="text-gray-600">
                              {notification.match?.found_item?.found_date
                                ? `Trouvé le ${formatDate(notification.match.found_item.found_date)}`
                                : 'Date inconnue'}
                            </p>
                            <p className="text-gray-600">
                              {notification.match?.found_item?.found_location || 'Non renseigné'}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2 text-sm text-gray-600">
                          <span className="font-medium">Score de confiance:</span>{' '}
                          {notification.match?.confidence_score !== undefined
                            ? `${(notification.match.confidence_score * 100).toFixed(1)}%`
                            : 'N/A'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex-shrink-0 ml-4">
                  {!notification.is_read && (
                    <button
                      onClick={() => markAsRead(notification.id)}
                      className="text-primary-600 hover:text-primary-800 p-1 rounded-full hover:bg-primary-50"
                      title="Marquer comme lu"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  )}
                  {notification.is_read && (
                    <div className="text-gray-400 p-1">
                      <EyeOff className="h-4 w-4" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Notifications;
