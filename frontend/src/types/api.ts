// Types API générés à partir des serializers Django

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Utilisateur extends User {
  // Proxy model pour la classe User de base
}

export interface UtilisateurAyantPerduDocument extends Utilisateur {
  // Proxy model pour les utilisateurs ayant déclaré une perte de document
}

export interface UtilisateurAyantTrouveDocument extends Utilisateur {
  // Proxy model pour les utilisateurs ayant trouvé un document
}

export interface DocumentType {
  id: number;
  name: string;
  description?: string;
}

export interface LostItem {
  id: number;
  user: User;
  document_type: DocumentType;
  document_type_id: number; // write-only
  first_name: string;
  last_name: string;
  date_of_birth: string; // ISO date
  document_number: string;
  lost_date: string; // ISO date
  lost_location: string;
  description: string;
  contact_phone: string;
  contact_email: string;
  status: 'active' | 'closed' | 'resolved';
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface FoundItem {
  id: number;
  user: User;
  document_type: DocumentType;
  document_type_id: number; // write-only
  image: string; // URL
  first_name?: string; // read-only, from OCR
  last_name?: string; // read-only, from OCR
  date_of_birth?: string; // read-only, from OCR
  document_number?: string; // read-only, from OCR
  found_date: string; // ISO date
  found_location: string;
  description: string;
  contact_phone: string;
  contact_email: string;
  status: 'active' | 'matched' | 'returned';
  ocr_confidence?: number; // read-only
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface Match {
  id: number;
  lost_item: LostItem;
  found_item: FoundItem;
  confidence_score: number;
  match_criteria: string[] | Record<string, unknown>;
  status: 'pending' | 'confirmed' | 'rejected' | 'completed';
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface Notification {
  id: number;
  user: number; // User ID
  match?: Match | null;
  notification_type: 'match_found' | 'match_confirmed' | 'item_returned' | 'item_handed_over';
  title: string;
  message: string;
  is_read: boolean;
  created_at: string; // ISO datetime
}

// Types pour les requêtes
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
}

export interface LostItemCreate {
  document_type_id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  lost_date: string;
  lost_location: string;
  description: string;
  contact_phone: string;
  contact_email: string;
}

export interface FoundItemCreate {
  document_type_id: number;
  image: File; // FormData
  found_date: string;
  found_location: string;
  description: string;
  contact_phone: string;
  contact_email: string;
}

// Types pour les réponses API
export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface Historique {
  id: number;
  user: User;
  action: 'login' | 'logout' | 'register' | 'lost_declaration' | 'found_declaration' | 'match_found' | 'match_confirmed' | 'match_rejected' | 'item_handed_over' | 'profile_update';
  description: string;
  related_object_id?: number;
  related_object_type?: string;
  created_at: string; // ISO datetime
}

export interface HistoriqueFilters {
  user?: number;
  action?: string;
  date_debut?: string;
  date_fin?: string;
}
