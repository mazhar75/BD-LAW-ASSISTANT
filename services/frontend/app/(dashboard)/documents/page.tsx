'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FileText, Download, Eye, Search } from 'lucide-react';

interface Document {
  id: string;
  title: string;
  type: 'law' | 'case' | 'regulation' | 'amendment';
  category: string;
  date: string;
  size: string;
  url: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  // Mock data for MVP
  const mockDocuments: Document[] = [
    {
      id: '1',
      title: 'Bangladesh Constitution 1972',
      type: 'law',
      category: 'Constitutional',
      date: '1972-12-16',
      size: '2.5 MB',
      url: '/docs/constitution-1972.pdf'
    },
    {
      id: '2',
      title: 'Criminal Procedure Code',
      type: 'law',
      category: 'Criminal',
      date: '1898-03-22',
      size: '1.8 MB',
      url: '/docs/cpc.pdf'
    },
    {
      id: '3',
      title: 'Labour Act 2006',
      type: 'law',
      category: 'Labor',
      date: '2006-10-11',
      size: '950 KB',
      url: '/docs/labour-act-2006.pdf'
    },
    {
      id: '4',
      title: 'Evidence Act 1872',
      type: 'law',
      category: 'Evidence',
      date: '1872-03-01',
      size: '1.2 MB',
      url: '/docs/evidence-act-1872.pdf'
    },
    {
      id: '5',
      title: 'Contract Act 1872',
      type: 'law',
      category: 'Contract',
      date: '1872-09-01',
      size: '890 KB',
      url: '/docs/contract-act-1872.pdf'
    }
  ];

  useEffect(() => {
    // TODO: Replace with real API call
    const loadDocuments = () => {
      setDocuments(mockDocuments);
    };
    loadDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterType === 'all' || doc.type === filterType;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Legal Documents</h1>
        <p className="mt-2 text-muted-foreground">
          Browse and download legal documents
        </p>
      </div>

      {/* Search & Filters */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="law">Laws</option>
            <option value="case">Cases</option>
            <option value="regulation">Regulations</option>
            <option value="amendment">Amendments</option>
          </select>
        </div>
      </Card>

      {/* Documents List */}
      <div className="space-y-3">
        {filteredDocuments.length === 0 ? (
          <Card className="p-12">
            <div className="text-center">
              <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Documents Found</h3>
              <p className="text-muted-foreground">
                {searchQuery
                  ? `No documents match "${searchQuery}"`
                  : 'No documents available'}
              </p>
            </div>
          </Card>
        ) : (
          filteredDocuments.map((doc) => (
            <Card key={doc.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <FileText className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{doc.title}</h3>
                    <div className="flex flex-wrap gap-4 mt-2 text-sm text-muted-foreground">
                      <span>Type: <span className="text-foreground">{doc.type}</span></span>
                      <span>Category: <span className="text-foreground">{doc.category}</span></span>
                      <span>Date: <span className="text-foreground">{new Date(doc.date).toLocaleDateString()}</span></span>
                      <span>Size: <span className="text-foreground">{doc.size}</span></span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" title="View">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" title="Download">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
