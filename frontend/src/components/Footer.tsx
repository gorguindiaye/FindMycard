import React from 'react';
import { Heart } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center mb-4 md:mb-0">
            <img src="/logo.jpg" alt="Logo" className="h-16 w-20 mr-2" />
            <span className="text-gray-600">FindMyCard - Aide à retrouver vos documents perdus</span>
          </div>
          <div className="text-sm text-gray-500">
            © 2023 FindMyCard. Tous droits réservés.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
