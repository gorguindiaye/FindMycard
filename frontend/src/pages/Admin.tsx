import React, { useState, useEffect } from 'react';
import { Users, FileText, BarChart3, Settings, Shield, AlertTriangle, CheckCircle, Trash2, UserCheck, UserX } from 'lucide-react';
import { toast } from 'react-toastify';
import Loader from '../components/Loader.tsx';
import apiService from '../services/api.ts';



interface AdminStats {
  total_users: number;
  active_users: number;
  total_lost_items: number;
  total_found_items: number;
  total_matches: number;
  pending_reports: number;
}

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  last_login?: string;
}

const Admin: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchStats();
    } else if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'reports') {
      fetchReports();
    }
  }, [activeTab]);

  const fetchStats = async () => {
    try {
      setLoading(true);

      // Fetch data from existing endpoints using apiService
      const [usersResponse, lostResponse, foundResponse, matchesResponse, statsResponse] = await Promise.all([
        apiService.getUsers(),
        apiService.getLostItems(),
        apiService.getFoundItems(),
        apiService.getMatches(),
        apiService.getUsers().then(() => apiService.getCurrentUser()), // For stats, we'll use user count from users endpoint
      ]);

      setStats({
        total_users: usersResponse.data.count || usersResponse.data.results?.length || 0,
        active_users: usersResponse.data.results?.filter((u: any) => u.is_active).length || 0,
        total_lost_items: lostResponse.data.count || lostResponse.data.results?.length || 0,
        total_found_items: foundResponse.data.count || foundResponse.data.results?.length || 0,
        total_matches: matchesResponse.data.count || matchesResponse.data.results?.length || 0,
        pending_reports: 0, // Would come from a reports endpoint
      });
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
      toast.error('Erreur lors du chargement des statistiques');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await apiService.getUsers();
      setUsers(response.data.results || response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des utilisateurs:', error);
      toast.error('Erreur lors du chargement des utilisateurs');
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async () => {
    try {
      setLoading(true);
      // In a real implementation, you'd have a reports endpoint
      // For now, we'll show placeholder data
    } catch (error) {
      console.error('Erreur lors du chargement des rapports:', error);
      toast.error('Erreur lors du chargement des rapports');
    } finally {
      setLoading(false);
    }
  };

  const toggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      setActionLoading(`user-${userId}`);
      await apiService.updateUserStatus(userId, !currentStatus);

      // Update local state
      setUsers(users.map(user =>
        user.id === userId ? { ...user, is_active: !currentStatus } : user
      ));

      toast.success(`Utilisateur ${!currentStatus ? 'activé' : 'désactivé'} avec succès`);
    } catch (error) {
      console.error('Erreur lors de la modification du statut:', error);
      toast.error('Erreur lors de la modification du statut');
    } finally {
      setActionLoading(null);
    }
  };

  const deleteUser = async (userId: number) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) {
      return;
    }

    try {
      setActionLoading(`delete-${userId}`);
      await apiService.deleteUser(userId);

      // Update local state
      setUsers(users.filter(user => user.id !== userId));
      toast.success('Utilisateur supprimé avec succès');
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      toast.error('Erreur lors de la suppression');
    } finally {
      setActionLoading(null);
    }
  };

  const tabs = [
    { id: 'dashboard', name: 'Tableau de bord', icon: BarChart3 },
    { id: 'users', name: 'Utilisateurs', icon: Users },
    { id: 'reports', name: 'Rapports', icon: FileText },
    { id: 'settings', name: 'Paramètres', icon: Settings },
  ];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-sm">
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-center h-16 px-4 bg-primary-600">
              <div className="flex items-center">
                <Shield className="h-8 w-8 text-white mr-2" />
                <h1 className="text-white text-lg font-semibold">Administration</h1>
              </div>
            </div>
            <nav className="flex-1 px-4 py-4 space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900">
                {tabs.find(tab => tab.id === activeTab)?.name}
              </h2>
              <p className="mt-1 text-sm text-gray-600">
                Gérez le système FindMyID
              </p>
            </div>

            {loading ? (
              <div className="flex justify-center py-12">
                <Loader />
              </div>
            ) : (
              <>
                {activeTab === 'dashboard' && stats && (
                  <div className="space-y-6">
                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div className="flex items-center">
                          <Users className="h-8 w-8 text-blue-600" />
                          <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Utilisateurs actifs</p>
                            <p className="text-2xl font-semibold text-gray-900">{stats.active_users}</p>
                            <p className="text-xs text-gray-500">sur {stats.total_users} total</p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div className="flex items-center">
                          <FileText className="h-8 w-8 text-red-600" />
                          <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Objets perdus</p>
                            <p className="text-2xl font-semibold text-gray-900">{stats.total_lost_items}</p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div className="flex items-center">
                          <CheckCircle className="h-8 w-8 text-green-600" />
                          <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Objets trouvés</p>
                            <p className="text-2xl font-semibold text-gray-900">{stats.total_found_items}</p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div className="flex items-center">
                          <BarChart3 className="h-8 w-8 text-purple-600" />
                          <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Correspondances</p>
                            <p className="text-2xl font-semibold text-gray-900">{stats.total_matches}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Recent Activity */}
                    <div className="bg-white shadow-sm border border-gray-200 rounded-lg">
                      <div className="px-6 py-4 border-b border-gray-200">
                        <h3 className="text-lg font-medium text-gray-900">Activité récente</h3>
                      </div>
                      <div className="p-6">
                        <div className="text-center py-12">
                          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                          <p className="text-gray-500">Graphiques et analyses détaillées à implémenter</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'users' && (
                  <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200">
                      <h3 className="text-lg font-medium text-gray-900">Gestion des utilisateurs</h3>
                      <p className="text-sm text-gray-600">Gérez les comptes utilisateurs et leurs permissions</p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Utilisateur
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Statut
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Rôle
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Inscription
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {users.map((user) => (
                            <tr key={user.id}>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">
                                      {user.first_name} {user.last_name}
                                    </div>
                                    <div className="text-sm text-gray-500">{user.email}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                  user.is_active
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-red-100 text-red-800'
                                }`}>
                                  {user.is_active ? 'Actif' : 'Inactif'}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {user.is_staff ? 'Administrateur' : 'Utilisateur'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatDate(user.date_joined)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                <button
                                  onClick={() => toggleUserStatus(user.id, user.is_active)}
                                  disabled={actionLoading === `user-${user.id}`}
                                  className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                                    user.is_active
                                      ? 'bg-red-100 text-red-800 hover:bg-red-200'
                                      : 'bg-green-100 text-green-800 hover:bg-green-200'
                                  }`}
                                >
                                  {actionLoading === `user-${user.id}` ? (
                                    <Loader className="h-3 w-3 mr-1" />
                                  ) : user.is_active ? (
                                    <UserX className="h-3 w-3 mr-1" />
                                  ) : (
                                    <UserCheck className="h-3 w-3 mr-1" />
                                  )}
                                  {user.is_active ? 'Désactiver' : 'Activer'}
                                </button>
                                {user.role !== 'admin_plateforme' && (
                                  <button
                                    onClick={() => deleteUser(user.id)}
                                    disabled={actionLoading === `delete-${user.id}`}
                                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-red-100 text-red-800 hover:bg-red-200"
                                  >
                                    {actionLoading === `delete-${user.id}` ? (
                                      <Loader className="h-3 w-3 mr-1" />
                                    ) : (
                                      <Trash2 className="h-3 w-3 mr-1" />
                                    )}
                                    Supprimer
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {activeTab === 'reports' && (
                  <div className="bg-white shadow-sm border border-gray-200 rounded-lg">
                    <div className="px-6 py-4 border-b border-gray-200">
                      <h3 className="text-lg font-medium text-gray-900">Rapports et signalements</h3>
                      <p className="text-sm text-gray-600">Gérez les rapports d'abus et les signalements</p>
                    </div>
                    <div className="p-6">
                      <div className="text-center py-12">
                        <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun rapport</h3>
                        <p className="text-gray-500">Il n'y a actuellement aucun rapport ou signalement à traiter.</p>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'settings' && (
                  <div className="space-y-6">
                    <div className="bg-white shadow-sm border border-gray-200 rounded-lg">
                      <div className="px-6 py-4 border-b border-gray-200">
                        <h3 className="text-lg font-medium text-gray-900">Paramètres système</h3>
                        <p className="text-sm text-gray-600">Configurez les paramètres globaux du système</p>
                      </div>
                      <div className="p-6">
                        <div className="text-center py-12">
                          <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                          <h3 className="text-lg font-medium text-gray-900 mb-2">Paramètres à implémenter</h3>
                          <p className="text-gray-500">Configuration système, limites, notifications, etc.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Admin;
