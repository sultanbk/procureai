/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Button to trigger JSON/CSV data downloads and PDF generation.
 * 
 * What it means:
 * Export utility.
 * 
 * Importance in Project:
 * Medium. Facilitates external audit reporting.
 */

import { useState } from 'react';
import { Printer, FileJson, Download } from 'lucide-react';
import Button from './ui/Button';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

export default function ExportButton({ report }) {
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const downloadJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `procureai_report_${report.audit_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const downloadPDF = async () => {
    const reportElement = document.getElementById('audit-report-content');
    if (!reportElement) return;

    setIsDownloadingPdf(true);

    try {
      // Find all buttons and print:hidden elements to hide
      const nonPrintableElements = reportElement.querySelectorAll('.print\\:hidden, button');
      const originalDisplayMap = new Map();
      
      nonPrintableElements.forEach((el, index) => {
        originalDisplayMap.set(index, el.style.display);
        el.style.display = 'none';
      });

      // Show print-only cover block temporarily
      const printOnlyCover = reportElement.querySelector('.print\\:block');
      let originalCoverDisplay = '';
      if (printOnlyCover) {
        originalCoverDisplay = printOnlyCover.style.display;
        printOnlyCover.style.display = 'block';
      }

      // Add temporarily cleaner padding and layout overrides
      const originalPadding = reportElement.style.padding;
      reportElement.style.padding = '0px';

      const canvas = await html2canvas(reportElement, {
        scale: 2, // High-fidelity scaling
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      });

      // Restore elements display, cover block, and padding
      nonPrintableElements.forEach((el, index) => {
        el.style.display = originalDisplayMap.get(index) || '';
      });
      if (printOnlyCover) {
        printOnlyCover.style.display = originalCoverDisplay;
      }
      reportElement.style.padding = originalPadding;

      const imgData = canvas.toDataURL('image/jpeg', 0.95);
      
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 210; // A4 size width in mm
      const pageHeight = 297; // A4 size height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      // Draw the first page
      pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      // Draw subsequent pages if content overflows A4 height
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      pdf.save(`procureai_audit_report_${report.audit_id}.pdf`);
    } catch (err) {
      console.error('Failed to generate PDF:', err);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <div className="flex items-center gap-2 print:hidden">
      <Button variant="secondary" size="sm" className="flex items-center gap-1.5 font-semibold" onClick={downloadJSON}>
        <FileJson className="h-4 w-4 stroke-[1.5]" /> Export JSON
      </Button>
      <Button variant="secondary" size="sm" className="flex items-center gap-1.5 font-semibold" onClick={downloadPDF} disabled={isDownloadingPdf}>
        <Download className="h-4 w-4 stroke-[1.5]" /> {isDownloadingPdf ? 'Generating PDF...' : 'Download PDF'}
      </Button>
      <Button size="sm" className="flex items-center gap-1.5 font-semibold" onClick={() => window.print()}>
        <Printer className="h-4 w-4 stroke-[1.5]" /> Print Report
      </Button>
    </div>
  );
}
