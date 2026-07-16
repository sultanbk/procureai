import jsPDF from 'jspdf';
import { Download, Copy, AlertTriangle, ShieldAlert, Crosshair, ThumbsUp, ShieldCheck } from 'lucide-react';
import Card from './ui/Card';
import Badge from './ui/Badge';
import Button from './ui/Button';

export default function NegotiationBriefCard({ brief }) {
  if (!brief) return null;

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'HIGH': return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'MEDIUM': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'LOW': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getStanceColor = (stance) => {
    switch (stance) {
      case 'AGGRESSIVE': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'FIRM': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'COLLABORATIVE': return 'bg-teal-100 text-teal-800 border-teal-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'HIGH': return <ShieldAlert className="h-4 w-4 text-rose-500 stroke-[1.5]" />;
      case 'MEDIUM': return <AlertTriangle className="h-4 w-4 text-amber-500 stroke-[1.5]" />;
      case 'LOW': return <ShieldCheck className="h-4 w-4 text-emerald-500 stroke-[1.5]" />;
      default: return <AlertTriangle className="h-4 w-4 text-slate-500 stroke-[1.5]" />;
    }
  };

  const copyDemands = () => {
    const text = brief.demands.map((d, i) => `${i + 1}. [${d.priority}] ${d.demand}\n   Evidence: ${d.justification}`).join('\n\n');
    navigator.clipboard.writeText(text);
  };

  const downloadPDF = () => {
    const doc = new jsPDF();
    let y = 20;
    
    doc.setFontSize(20);
    doc.text(`Negotiation Brief: ${brief.supplier_name}`, 20, y);
    y += 15;
    
    doc.setFontSize(12);
    doc.text(`Audits Analysed: ${brief.audits_analysed}`, 20, y);
    y += 10;
    doc.text(`Total Leakage Basis: $${Number(brief.total_leakage_basis).toLocaleString(undefined, {minimumFractionDigits: 2})}`, 20, y);
    y += 15;
    
    doc.setFontSize(14);
    doc.text("Executive Summary", 20, y);
    y += 10;
    doc.setFontSize(10);
    const summaryLines = doc.splitTextToSize(brief.executive_summary, 170);
    doc.text(summaryLines, 20, y);
    y += summaryLines.length * 5 + 10;
    
    doc.setFontSize(14);
    doc.text("Negotiation Demands", 20, y);
    y += 10;
    
    brief.demands.forEach((demand, i) => {
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
      doc.setFontSize(11);
      doc.setFont("helvetica", "bold");
      const title = `${i + 1}. [${demand.priority}] ${demand.demand_type.replace('_', ' ')}`;
      doc.text(title, 20, y);
      y += 7;
      
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      const demandLines = doc.splitTextToSize(demand.demand, 170);
      doc.text(demandLines, 20, y);
      y += demandLines.length * 5 + 3;
      
      doc.setFont("helvetica", "italic");
      doc.setTextColor(100, 100, 100);
      const justifyLines = doc.splitTextToSize(`Evidence: ${demand.justification}`, 170);
      doc.text(justifyLines, 20, y);
      doc.setTextColor(0, 0, 0);
      y += justifyLines.length * 5 + 10;
    });
    
    doc.save(`${brief.supplier_name.replace(/\s+/g, '_')}_Negotiation_Brief.pdf`);
  };

  return (
    <div className="space-y-6">
      {/* Card 1: Header */}
      <Card className="border-l-4 border-l-slate-800">
        <div className="flex flex-wrap gap-3 items-center mb-4">
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getRiskColor(brief.risk_rating)}`}>
            Risk Rating: {brief.risk_rating}
          </span>
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStanceColor(brief.recommended_stance)}`}>
            Stance: {brief.recommended_stance}
          </span>
          <span className="text-xs text-slate-500 ml-auto">
            Based on {brief.audits_analysed} audits ({brief.audit_period})
          </span>
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-2">Executive Summary</h3>
        <p className="text-sm text-slate-700 leading-relaxed">
          {brief.executive_summary}
        </p>
      </Card>

      {/* Card 2: Violation Patterns */}
      <Card>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-4 flex items-center gap-2">
          <Crosshair className="h-4 w-4 stroke-[1.5]" /> Violation Patterns
        </h3>
        <div className="space-y-3">
          {brief.violation_analysis.map((pattern, idx) => (
            <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="flex items-center gap-2 mb-1.5">
                {getSeverityIcon(pattern.severity)}
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700 bg-white border border-slate-200 px-2 py-0.5 rounded-md">
                  {pattern.clause_type.replace('_', ' ')}
                </span>
                <span className="text-sm font-semibold text-slate-900">{pattern.pattern}</span>
              </div>
              <p className="text-xs text-slate-600 italic ml-6">{pattern.evidence}</p>
            </div>
          ))}
          {brief.violation_analysis.length === 0 && (
            <div className="text-sm text-slate-500 italic py-2">No significant violation patterns detected.</div>
          )}
        </div>
      </Card>

      {/* Card 3: Negotiation Demands */}
      <Card>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-4 flex items-center gap-2">
          <ThumbsUp className="h-4 w-4 stroke-[1.5]" /> Core Negotiation Demands
        </h3>
        <div className="space-y-4">
          {brief.demands.map((demand, idx) => {
            const isMustHave = demand.priority === 'MUST_HAVE';
            const borderClass = isMustHave ? 'border-l-rose-500 bg-rose-50/30' : 'border-l-slate-400 bg-slate-50/50';
            
            return (
              <div key={idx} className={`p-4 border border-slate-200 border-l-4 rounded-lg ${borderClass}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant={isMustHave ? 'danger' : 'neutral'}>{demand.priority.replace('_', ' ')}</Badge>
                  <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{demand.demand_type.replace(/_/g, ' ')}</span>
                </div>
                <p className="text-sm font-semibold text-slate-900 mb-2 leading-relaxed">
                  {demand.demand}
                </p>
                <p className="text-xs text-slate-500 italic bg-white/50 p-2 rounded border border-slate-100">
                  <span className="font-semibold text-slate-600 mr-1">Evidence:</span>
                  {demand.justification}
                </p>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Card 4: Actions */}
      <div className="flex gap-4 pt-2">
        <Button onClick={downloadPDF} className="flex-1 flex items-center justify-center gap-2 font-semibold">
          <Download className="h-4 w-4 stroke-[1.5]" />
          Download as PDF
        </Button>
        <Button onClick={copyDemands} variant="secondary" className="flex-1 flex items-center justify-center gap-2 font-semibold">
          <Copy className="h-4 w-4 stroke-[1.5]" />
          Copy All Demands
        </Button>
      </div>
    </div>
  );
}
