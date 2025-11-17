import React from 'react';
import { FileText, Calendar, User, Eye } from 'lucide-react';
import { motion } from 'framer-motion';

interface Document {
  id: number;
  title: string;
  description: string;
  image_url?: string;
  status: 'lost' | 'found' | 'matched';
  created_at: string;
  user: {
    first_name: string;
    last_name: string;
  };
}

interface CardProps {
  document: Document;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({ document, onClick }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'lost':
        return 'bg-red-100 text-red-800';
      case 'found':
        return 'bg-green-100 text-green-800';
      case 'matched':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'lost':
        return 'Perdu';
      case 'found':
        return 'Trouvé';
      case 'matched':
        return 'Correspondance';
      default:
        return status;
    }
  };

  return (
    <motion.div
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      whileHover={{ scale: 1.02, rotateX: 5 }}
    >
      {document.image_url && (
        <div className="mb-4">
          <img
            src={document.image_url}
            alt={document.title}
            className="w-full h-48 object-cover rounded-md"
          />
        </div>
      )}
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900 truncate">
          {document.title}
        </h3>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(document.status)}`}>
          {getStatusText(document.status)}
        </span>
      </div>
      <p className="text-gray-600 text-sm mb-4 line-clamp-2">
        {document.description}
      </p>
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center">
          <User className="h-4 w-4 mr-1" />
          <span>{document.user.first_name} {document.user.last_name}</span>
        </div>
        <div className="flex items-center">
          <Calendar className="h-4 w-4 mr-1" />
          <span>{new Date(document.created_at).toLocaleDateString()}</span>
        </div>
      </div>
      {onClick && (
        <div className="mt-4 flex items-center text-primary-600 text-sm font-medium">
          <Eye className="h-4 w-4 mr-1" />
          Voir les détails
        </div>
      )}
    </motion.div>
  );
};

export default Card;
