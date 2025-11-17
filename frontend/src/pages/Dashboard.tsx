import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import {
  Search,
  Camera,
  Heart,
  Bell,
  AlertCircle
} from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

interface DashboardStats {
  lostItems: number;
  foundItems: number;
  matches: number;
  notifications: number;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    lostItems: 0,
    foundItems: 0,
    matches: 0,
    notifications: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const [lostResponse, foundResponse, matchesResponse, notificationsResponse] = await Promise.all([
        axios.get('/api/lost-items/'),
        axios.get('/api/found-items/'),
        axios.get('/api/matches/'),
        axios.get('/api/notifications/unread_count/'),
      ]);

      setStats({
        lostItems: lostResponse.data.count || 0,
        foundItems: foundResponse.data.count || 0,
        matches: matchesResponse.data.count || 0,
        notifications: notificationsResponse.data.unread_count || 0,
      });
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'J\'ai perdu une pièce',
      description: 'Déclarer la perte d\'une pièce d\'identité',
      icon: Search,
      href: '/lost-item',
      color: 'bg-blue-500',
      textColor: 'text-blue-500',
    },
    {
      title: 'J\'ai trouvé une pièce',
      description: 'Déclarer la trouvaille d\'une pièce d\'identité',
      icon: Camera,
      href: '/found-item',
      color: 'bg-green-500',
      textColor: 'text-green-500',
    },
    {
      title: 'Voir les correspondances',
      description: 'Consulter les correspondances trouvées',
      icon: Heart,
      href: '/matches',
      color: 'bg-pink-500',
      textColor: 'text-pink-500',
    },
    {
      title: 'Notifications',
      description: 'Voir toutes les notifications',
      icon: Bell,
      href: '/notifications',
      color: 'bg-yellow-500',
      textColor: 'text-yellow-500',
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Bonjour, {user?.first_name} !
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Bienvenue sur FindMyID. Retrouvons ensemble vos pièces d'identité perdues.
        </p>
      </div>

      {/* Statistiques */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div
          className="bg-white overflow-hidden shadow rounded-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Search className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Pièces perdues
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.lostItems}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-white overflow-hidden shadow rounded-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Camera className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Pièces trouvées
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.foundItems}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-white overflow-hidden shadow rounded-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Heart className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Correspondances
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.matches}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-white overflow-hidden shadow rounded-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Bell className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Notifications
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.notifications}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Actions rapides */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
      >
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Actions rapides
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action, index) => {
            const Icon = action.icon;
            return (
              <motion.div
                key={action.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 + index * 0.1 }}
                whileHover={{ scale: 1.05, y: -5 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  to={action.href}
                  className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 rounded-lg shadow hover:shadow-md transition-shadow block"
                >
                  <div>
                    <span className={`rounded-lg inline-flex p-3 ${action.color} ring-4 ring-white`}>
                      <Icon className="h-6 w-6 text-white" />
                    </span>
                  </div>
                  <div className="mt-8">
                    <h3 className="text-lg font-medium">
                      <span className="absolute inset-0" aria-hidden="true" />
                      {action.title}
                    </h3>
                    <p className="mt-2 text-sm text-gray-500">
                      {action.description}
                    </p>
                  </div>
                  <span
                    className={`absolute top-6 right-6 ${action.textColor} opacity-0 group-hover:opacity-100 transition-opacity`}
                    aria-hidden="true"
                  >
                    <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16-1.414-1.414z" />
                    </svg>
                  </span>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Conseils */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Conseils pour retrouver votre pièce
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Déclarez rapidement la perte pour maximiser les chances de retrouvailles</li>
                <li>Fournissez des informations précises sur le lieu et la date de perte</li>
                <li>Vérifiez régulièrement vos notifications pour les correspondances</li>
                <li>Si vous trouvez une pièce, prenez une photo claire pour faciliter l'identification</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 