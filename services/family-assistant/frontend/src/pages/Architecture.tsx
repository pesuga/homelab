import React, { useState } from 'react';
import { FileText, RefreshCw, Search, ExternalLink, Clock, Tag } from 'lucide-react';

interface ArchitectureSection {
  title: string;
  content: string;
}

interface ArchitectureDoc {
  title: string;
  content: string;
  last_updated: string;
  sections: ArchitectureSection[];
}

interface ArchitectureProps {}

export const Architecture: React.FC<ArchitectureProps> = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);

  // Mock architecture data
  const mockDocs: ArchitectureDoc[] = [
    {
      title: 'README.md',
      content: '# Homelab Infrastructure\n\nThis project is a comprehensive homelab setup for running AI agents and workflows with local LLM inference.',
      last_updated: new Date().toISOString(),
      sections: [
        {
          title: 'Overview',
          content: 'Homelab infrastructure with two-node architecture for AI workloads'
        },
        {
          title: 'Architecture',
          content: 'Compute Node for LLM inference and Service Node for orchestration'
        },
        {
          title: 'Services',
          content: 'Ollama, PostgreSQL, Redis, N8n workflows, monitoring stack'
        }
      ]
    },
    {
      title: 'CLAUDE.md',
      content: '# Project Documentation\n\nComprehensive guide for the Family Assistant project architecture and development.',
      last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      sections: [
        {
          title: 'Project Overview',
          content: 'Family Assistant with multimodal AI capabilities and privacy focus'
        },
        {
          title: 'Architecture Overview',
          content: 'Two-node setup with dedicated compute and service nodes'
        },
        {
          title: 'Technology Stack',
          content: 'FastAPI, React, Kubernetes, Ollama, PostgreSQL, Redis'
        }
      ]
    }
  ];

  const docs = mockDocs; // In real app, this would be fetched from API

  const filteredDocs = docs.filter(doc =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.sections.some(section =>
      section.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      section.content.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const formatLastUpdated = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const selectedDocument = selectedDoc
    ? docs.find(doc => doc.title === selectedDoc)
    : null;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Architecture</h1>
          <p className="text-gray-600 mt-2">
            System documentation and architecture overview
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search documentation..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document List */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Documents</h2>

          {filteredDocs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No documents found</p>
            </div>
          ) : (
            filteredDocs.map((doc) => (
              <div
                key={doc.title}
                onClick={() => setSelectedDoc(doc.title)}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                  selectedDoc === doc.title
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-900 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-gray-500" />
                    {doc.title}
                  </h3>
                </div>

                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {doc.content.substring(0, 100)}...
                </p>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatLastUpdated(doc.last_updated)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Tag className="w-3 h-3" />
                    {doc.sections.length} sections
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Document Content */}
        <div className="lg:col-span-2">
          {selectedDocument ? (
            <div className="bg-white border border-gray-200 rounded-lg">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                    <FileText className="w-6 h-6 text-gray-500" />
                    {selectedDocument.title}
                  </h2>
                  <button className="text-primary-600 hover:text-primary-800 flex items-center gap-1">
                    <ExternalLink className="w-4 h-4" />
                    Open
                  </button>
                </div>
                <p className="text-sm text-gray-500">
                  Last updated: {formatLastUpdated(selectedDocument.last_updated)}
                </p>
              </div>

              <div className="p-6">
                {/* Document Content */}
                <div className="prose prose-sm max-w-none mb-8">
                  <div className="whitespace-pre-wrap text-gray-700">
                    {selectedDocument.content}
                  </div>
                </div>

                {/* Sections */}
                {selectedDocument.sections.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Sections</h3>
                    <div className="space-y-4">
                      {selectedDocument.sections.map((section, index) => (
                        <div key={index} className="border-l-4 border-primary-500 pl-4">
                          <h4 className="font-medium text-gray-900 mb-2">
                            {section.title}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {section.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a Document
              </h3>
              <p className="text-gray-500">
                Choose a document from the sidebar to view its contents
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};