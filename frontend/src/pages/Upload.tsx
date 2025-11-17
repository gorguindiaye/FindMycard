import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, FileImage, X, CheckCircle, AlertCircle, ArrowRight } from 'lucide-react';
import { toast } from 'react-toastify';
import axios from 'axios';
import Loader from '../components/Loader.tsx';

const API_BASE_URL = 'http://localhost:8000/api';

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [ocrResult, setOcrResult] = useState<any>(null);
  const [showResults, setShowResults] = useState(false);

  const handleFileChange = useCallback((selectedFile: File) => {
    if (selectedFile && selectedFile.type.startsWith('image/')) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(selectedFile);
      setOcrResult(null);
      setShowResults(false);
    } else {
      toast.error('Veuillez sélectionner un fichier image valide');
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileChange(files[0]);
    }
  }, [handleFileChange]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileChange(e.target.files[0]);
    }
  };

  const removeFile = () => {
    setFile(null);
    setPreview(null);
    setOcrResult(null);
    setShowResults(false);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      setUploading(true);

      // Create FormData for the API call
      const formData = new FormData();
      formData.append('image', file);

      // Get auth token
      const token = localStorage.getItem('access_token');

      // Call OCR service
      const response = await axios.post(`${API_BASE_URL}/ocr/process/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
      });

      setOcrResult(response.data);
      setShowResults(true);
      toast.success('Analyse OCR terminée avec succès');
    } catch (error: any) {
      console.error('Erreur lors de l\'upload:', error);
      toast.error('Erreur lors de l\'analyse de l\'image');
    } finally {
      setUploading(false);
    }
  };

  const proceedToForm = () => {
    if (ocrResult) {
      // Store OCR result in localStorage or context for the form
      localStorage.setItem('ocrResult', JSON.stringify(ocrResult));
      navigate('/found-item');
    }
  };

  const maxFileSize = 10 * 1024 * 1024; // 10MB
  const acceptedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900">
            Analyser une pièce d'identité
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Téléchargez une photo de votre pièce d'identité trouvée pour extraire automatiquement les informations
          </p>
        </div>

        {/* Upload Form */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          {!showResults ? (
            <form onSubmit={handleUpload} className="space-y-6">
              {/* File Upload Area */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-4">
                  Sélectionner une image
                </label>

                {!file ? (
                  <div
                    className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                      dragActive
                        ? 'border-primary-400 bg-primary-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                  >
                    <FileImage className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <div className="space-y-2">
                      <div className="flex text-sm text-gray-600 justify-center">
                        <label
                          htmlFor="file-upload"
                          className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                        >
                          <span>Cliquez pour sélectionner</span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            className="sr-only"
                            accept={acceptedTypes.join(',')}
                            onChange={handleInputChange}
                          />
                        </label>
                        <span className="pl-1">ou glissez-déposez</span>
                      </div>
                      <p className="text-xs text-gray-500">
                        PNG, JPG, GIF, WebP jusqu'à 10MB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="relative">
                    {/* Image Preview */}
                    <div className="relative bg-gray-100 rounded-lg overflow-hidden">
                      <img
                        src={preview!}
                        alt="Aperçu"
                        className="w-full h-64 object-contain"
                      />
                      <button
                        type="button"
                        onClick={removeFile}
                        className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>

                    {/* File Info */}
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <FileImage className="h-8 w-8 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">{file.name}</p>
                            <p className="text-xs text-gray-500">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        {file.size > maxFileSize && (
                          <div className="flex items-center text-red-600">
                            <AlertCircle className="h-4 w-4 mr-1" />
                            <span className="text-xs">Trop volumineux</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Upload Button */}
              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={!file || uploading || file.size > maxFileSize}
                  className="flex-1 flex justify-center items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? (
                    <>
                      <Loader className="h-4 w-4 mr-2" />
                      Analyse en cours...
                    </>
                  ) : (
                    <>
                      <UploadIcon className="h-5 w-5 mr-2" />
                      Analyser l'image
                    </>
                  )}
                </button>

                {file && (
                  <button
                    type="button"
                    onClick={removeFile}
                    className="px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    Changer
                  </button>
                )}
              </div>
            </form>
          ) : (
            /* OCR Results */
            <div className="space-y-6">
              <div className="text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Analyse terminée
                </h3>
                <p className="text-sm text-gray-600">
                  Les informations suivantes ont été extraites de l'image
                </p>
              </div>

              {/* Extracted Information */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="text-sm font-medium text-gray-900 mb-4">
                  Informations extraites
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {ocrResult?.first_name && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Prénom
                      </label>
                      <p className="mt-1 text-sm text-gray-900">{ocrResult.first_name}</p>
                    </div>
                  )}
                  {ocrResult?.last_name && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Nom
                      </label>
                      <p className="mt-1 text-sm text-gray-900">{ocrResult.last_name}</p>
                    </div>
                  )}
                  {ocrResult?.date_of_birth && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Date de naissance
                      </label>
                      <p className="mt-1 text-sm text-gray-900">{ocrResult.date_of_birth}</p>
                    </div>
                  )}
                  {ocrResult?.document_number && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Numéro de document
                      </label>
                      <p className="mt-1 text-sm text-gray-900">{ocrResult.document_number}</p>
                    </div>
                  )}
                </div>

                {ocrResult?.confidence && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">
                        Précision de l'analyse
                      </span>
                      <span className={`text-sm font-medium ${
                        ocrResult.confidence > 0.8 ? 'text-green-600' :
                        ocrResult.confidence > 0.6 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {(ocrResult.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          ocrResult.confidence > 0.8 ? 'bg-green-500' :
                          ocrResult.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${ocrResult.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-4">
                <button
                  onClick={() => setShowResults(false)}
                  className="flex-1 px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Analyser une autre image
                </button>
                <button
                  onClick={proceedToForm}
                  className="flex-1 flex justify-center items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Continuer
                  <ArrowRight className="h-4 w-4 ml-2" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-4">
            Conseils pour une meilleure analyse
          </h3>
          <div className="text-sm text-blue-800 space-y-2">
            <p>• Prenez la photo dans un endroit bien éclairé</p>
            <p>• Assurez-vous que le document est bien centré et droit</p>
            <p>• Évitez les reflets et les ombres</p>
            <p>• Utilisez une résolution d'au moins 2MP</p>
            <p>• Les formats PNG, JPG et WebP sont acceptés</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
