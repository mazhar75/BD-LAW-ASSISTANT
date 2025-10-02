'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { useTranslations } from 'next-intl';
import { FileDown, FileSpreadsheet, Copy, FileText } from 'lucide-react';
import { useSearchStore } from '@/store/searchStore';
import { searchService } from '@/lib/api/search.service';
import { useToast } from '@/components/ui/Toast';
import { ApiError } from '@/types/errors';

interface ExportDialogProps {
  selectedResults: string[];
  onClose: () => void;
}

export function ExportDialog({ selectedResults, onClose }: ExportDialogProps) {
  const t = useTranslations('search.export');
  const { showToast } = useToast();
  const { results } = useSearchStore();
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'excel' | 'json' | 'clipboard'>('pdf');

  const selectedData = results.filter(r => selectedResults.includes(r.id));

  const handleExport = async () => {
    setExporting(true);
    try {
      switch (exportFormat) {
        case 'pdf':
          await exportToPDF();
          break;
        case 'excel':
          await exportToExcel();
          break;
        case 'json':
          await exportToJSON();
          break;
        case 'clipboard':
          await copyToClipboard();
          break;
      }
      showToast({
        title: t('success'),
        description: t('successDescription'),
        type: 'success'
      });
      onClose();
    } catch (error) {
      showToast({
        title: t('error'),
        description: (error as ApiError).message || t('errorDescription'),
        type: 'error'
      });
    } finally {
      setExporting(false);
    }
  };

  const exportToPDF = async () => {
    // In real implementation, this would call an API endpoint
    const response = await searchService.exportResults(selectedResults, 'pdf');
    const blob = response instanceof Blob ? response : new Blob([JSON.stringify(response)], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bd-laws-export-${Date.now()}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToExcel = async () => {
    // In real implementation, this would generate Excel file
    const csvContent = [
      ['Title', 'Law Number', 'Date', 'Court', 'Category', 'Snippet'],
      ...selectedData.map(r => [
        r.title,
        r.lawNumber,
        r.date,
        r.court,
        r.category,
        r.snippet
      ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bd-laws-export-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToJSON = async () => {
    const jsonContent = JSON.stringify(selectedData, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bd-laws-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async () => {
    const text = selectedData.map(r =>
      `${r.title}\\n${r.lawNumber} - ${r.date}\\n${r.snippet}\\n`
    ).join('\\n---\\n\\n');

    await navigator.clipboard.writeText(text);
  };

  const exportOptions = [
    {
      id: 'pdf',
      name: t('formats.pdf'),
      description: t('formats.pdfDescription'),
      icon: FileText
    },
    {
      id: 'excel',
      name: t('formats.excel'),
      description: t('formats.excelDescription'),
      icon: FileSpreadsheet
    },
    {
      id: 'json',
      name: t('formats.json'),
      description: t('formats.jsonDescription'),
      icon: FileDown
    },
    {
      id: 'clipboard',
      name: t('formats.clipboard'),
      description: t('formats.clipboardDescription'),
      icon: Copy
    }
  ];

  return (
    <Modal
      open={true}
      onClose={onClose}
    >
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold">{t('title')}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {t('description', { count: selectedResults.length })}
          </p>
        </div>
        {/* Format Options */}
        <div className="space-y-3">
          {exportOptions.map((option) => {
            const Icon = option.icon;
            return (
              <label
                key={option.id}
                className={`
                  flex items-start gap-3 p-3 rounded-lg border cursor-pointer
                  ${exportFormat === option.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'}
                `}
              >
                <input
                  type="radio"
                  name="exportFormat"
                  value={option.id}
                  checked={exportFormat === option.id}
                  onChange={() => setExportFormat(option.id as 'pdf' | 'excel' | 'json' | 'clipboard')}
                  className="mt-1"
                />
                <Icon className="h-5 w-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <div className="font-medium">{option.name}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {option.description}
                  </div>
                </div>
              </label>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={exporting}
          >
            {t('cancel')}
          </Button>
          <Button
            onClick={handleExport}
            disabled={exporting}
          >
            {exporting ? t('exporting') : t('export')}
          </Button>
        </div>
      </div>
    </Modal>
  );
}