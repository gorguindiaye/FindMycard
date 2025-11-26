import axios, { AxiosInstance, AxiosResponse } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';



class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Intercepteur pour ajouter le token JWT
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Intercepteur pour gérer le refresh du token
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
                refresh: refreshToken,
              });
              const { access } = response.data;
              localStorage.setItem('access_token', access);
              originalRequest.headers.Authorization = `Bearer ${access}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // Si refresh échoue, déconnexion
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/auth';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentification
  async login(credentials: { email: string; password: string }): Promise<AxiosResponse> {
    return this.api.post('/token/', credentials);
  }

  async register(userData: { email: string; password: string; first_name: string; last_name: string; password_confirm: string }): Promise<AxiosResponse> {
    return this.api.post('/register/', userData);
  }

  async refreshToken(refreshToken: string): Promise<AxiosResponse> {
    return this.api.post('/token/refresh/', { refresh: refreshToken });
  }

  // Types de documents
  async getDocumentTypes(): Promise<AxiosResponse> {
    return this.api.get('/document-types/');
  }

  // Objets perdus
  async getLostItems(): Promise<AxiosResponse> {
    return this.api.get('/lost-items/');
  }

  async createLostItem(lostItemData: any): Promise<AxiosResponse> {
    return this.api.post('/lost-items/', lostItemData);
  }

  async updateLostItem(id: number, lostItemData: Partial<any>): Promise<AxiosResponse> {
    return this.api.patch(`/lost-items/${id}/`, lostItemData);
  }

  async deleteLostItem(id: number): Promise<AxiosResponse> {
    return this.api.delete(`/lost-items/${id}/`);
  }

  async confirmLostItemReceipt(id: number): Promise<AxiosResponse> {
    return this.api.post(`/lost-items/${id}/confirm-receipt/`);
  }

  // Objets trouvés
  async getFoundItems(): Promise<AxiosResponse> {
    return this.api.get('/found-items/');
  }

  async createFoundItem(foundItemData: FormData): Promise<AxiosResponse> {
    return this.api.post('/found-items/', foundItemData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async updateFoundItem(id: number, foundItemData: Partial<any>): Promise<AxiosResponse> {
    return this.api.patch(`/found-items/${id}/`, foundItemData);
  }

  async deleteFoundItem(id: number): Promise<AxiosResponse> {
    return this.api.delete(`/found-items/${id}/`);
  }

  async respondToFoundItem(id: number, payload: { message?: string; drop_off_point?: string; availability?: string }): Promise<AxiosResponse> {
    return this.api.post(`/found-items/${id}/respond/`, payload);
  }

  // Correspondances
  async getMatches(): Promise<AxiosResponse> {
    return this.api.get('/matches/');
  }

  async validateMatch(id: number, payload?: { reason?: string }): Promise<AxiosResponse> {
    return this.api.post(`/matches/${id}/validate/`, payload);
  }

  async invalidateMatch(id: number, payload: { reason: string }): Promise<AxiosResponse> {
    return this.api.post(`/matches/${id}/invalidate/`, payload);
  }

  async requestAuthCheck(id: number, payload?: { notes?: string }): Promise<AxiosResponse> {
    return this.api.post(`/matches/${id}/request-auth-check/`, payload);
  }

  // Notifications
  async getNotifications(): Promise<AxiosResponse> {
    return this.api.get('/notifications/');
  }

  async getUnreadNotificationsCount(): Promise<AxiosResponse> {
    return this.api.get('/notifications/unread_count/');
  }

  async markNotificationAsRead(id: number): Promise<AxiosResponse> {
    return this.api.post(`/notifications/${id}/mark_as_read/`);
  }

  async markAllNotificationsAsRead(): Promise<AxiosResponse> {
    return this.api.post('/notifications/mark_all_as_read/');
  }

  async sendNotification(payload: { user_id: number; title: string; message: string; match_id?: number }): Promise<AxiosResponse> {
    return this.api.post('/notifications/send/', payload);
  }

  // Verification requests (admin public)
  async getVerificationRequests(): Promise<AxiosResponse> {
    return this.api.get('/verification-requests/');
  }

  async confirmVerificationRequest(id: number, payload?: { reason?: string }): Promise<AxiosResponse> {
    return this.api.post(`/verification-requests/${id}/confirm/`, payload);
  }

  async rejectVerificationRequest(id: number, payload: { reason: string }): Promise<AxiosResponse> {
    return this.api.post(`/verification-requests/${id}/reject/`, payload);
  }

  async superviseVerificationRequest(id: number, payload?: { notes?: string }): Promise<AxiosResponse> {
    return this.api.post(`/verification-requests/${id}/supervise-restitution/`, payload);
  }

  // Utilisateurs
  async getCurrentUser(): Promise<AxiosResponse> {
    return this.api.get('/auth/user/');
  }

  async updateUser(userData: Partial<any>): Promise<AxiosResponse> {
    return this.api.patch('/users/me/', userData);
  }

  // Historique
  async getHistorique(filters?: { user?: number; action?: string; date_debut?: string; date_fin?: string }): Promise<AxiosResponse> {
    const params = new URLSearchParams();
    if (filters?.user) params.append('user', filters.user.toString());
    if (filters?.action) params.append('action', filters.action);
    if (filters?.date_debut) params.append('date_debut', filters.date_debut);
    if (filters?.date_fin) params.append('date_fin', filters.date_fin);
    return this.api.get(`/historique/?${params.toString()}`);
  }

  async getHistoriqueByUser(userId: number): Promise<AxiosResponse> {
    return this.api.get(`/historique/user/${userId}/`);
  }

  // Admin methods
  async getUsers(): Promise<AxiosResponse> {
    return this.api.get('/users/');
  }

  async updateUserStatus(userId: number, isActive: boolean): Promise<AxiosResponse> {
    return this.api.patch(`/users/${userId}/`, { is_active: isActive });
  }

  async deleteUser(userId: number): Promise<AxiosResponse> {
    return this.api.delete(`/users/${userId}/`);
  }

  // Admin manual matching
  async getAdminLostItems(): Promise<AxiosResponse> {
    return this.api.get('/admin-matching/lost_items/');
  }

  async getAdminFoundItems(): Promise<AxiosResponse> {
    return this.api.get('/admin-matching/found_items/');
  }

  async createManualMatch(lostItemId: number, foundItemId: number): Promise<AxiosResponse> {
    return this.api.post('/admin-matching/create_match/', {
      lost_item_id: lostItemId,
      found_item_id: foundItemId
    });
  }
}

const apiService = new ApiService();
export default apiService;
