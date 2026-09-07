import React from 'react';
import { HelpCircle, CheckCircle2, AlertCircle } from 'lucide-react';

export const ExplainabilityCard: React.FC = () => {
  return (
    <div className="ws-panel" style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(240, 248, 255, 0.72)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <HelpCircle size={14} color="#2563eb" />
          <h3 style={{ fontSize: '11.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
            RECOMMENDATION RATIONALE
          </h3>
        </div>
        <span style={{
          fontSize: '10px',
          fontWeight: 700,
          padding: '2px 6px',
          borderRadius: '0px',
          backgroundColor: 'rgba(240, 253, 250, 0.85)',
          color: '#0d9488',
          border: '1px solid #5eead4',
          fontFamily: 'var(--font-mono)'
        }}>
          CONFIDENCE: 88% (HIGH)
        </span>
      </div>

      <div style={{
        padding: '8px 10px',
        borderRadius: '0px',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        borderLeft: '4px solid #0d9488',
        borderTop: '1px solid rgba(191, 219, 254, 0.85)',
        borderRight: '1px solid rgba(191, 219, 254, 0.85)',
        borderBottom: '1px solid rgba(191, 219, 254, 0.85)',
        fontSize: '11.5px',
        fontFamily: 'var(--font-mono)',
        color: '#0f172a'
      }}>
        <strong style={{ color: '#0d9488' }}>STRATEGY:</strong> Bharati-first Transit via East-Sector Indian Ocean Corridor (Balanced Route).
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11px' }}>
        <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>PRIMARY EXPLAINABILITY FACTORS:</span>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', color: '#1e293b' }}>
          <CheckCircle2 size={13} color="#0d9488" style={{ marginTop: '2px', flexShrink: 0 }} />
          <span><strong style={{ color: '#0f172a' }}>Reduced SIC Risk:</strong> Prydz Bay leads show 22% lower median SIC during early January window vs Lazarev Sea.</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', color: '#1e293b' }}>
          <CheckCircle2 size={13} color="#0d9488" style={{ marginTop: '2px', flexShrink: 0 }} />
          <span><strong style={{ color: '#0f172a' }}>Iceberg Clearance:</strong> Drift ensemble projects mean trajectory east of 65°E, maintaining safe clearance.</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', color: '#1e293b' }}>
          <CheckCircle2 size={13} color="#0d9488" style={{ marginTop: '2px', flexShrink: 0 }} />
          <span><strong style={{ color: '#0f172a' }}>Current Optimization:</strong> Favorable Southern Ocean current vector yields ~4.8 MT fuel savings over 1,200 NM.</span>
        </div>
      </div>

      <div style={{
        padding: '6px 8px',
        borderRadius: '0px',
        backgroundColor: 'rgba(255, 247, 237, 0.85)',
        border: '1px solid #fdba74',
        fontSize: '10.5px',
        fontFamily: 'var(--font-mono)',
        color: '#ea580c',
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
      }}>
        <AlertCircle size={13} color="#ea580c" style={{ flexShrink: 0 }} />
        <span><strong>UNCERTAINTY:</strong> Forecast dispersion widens beyond +14d lead. Rolling re-forecast active.</span>
      </div>
    </div>
  );
};
