import React from 'react';
import { X, Ship, Calendar, Info } from 'lucide-react';

interface MissionPlanDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MissionPlanDrawer: React.FC<MissionPlanDrawerProps> = ({
  isOpen,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        left: '12px',
        bottom: '60px',
        width: '390px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 50,
        background: '#0f172a',
        border: '1.5px solid #38bdf8',
        borderRadius: '6px',
        boxShadow: '0 12px 36px rgba(0, 0, 0, 0.75)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        color: '#f8fafc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          background: '#1e293b',
          borderBottom: '1px solid #334155',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Ship size={18} color="#38bdf8" />
          <div>
            <div style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc' }}>
              EXPEDITION MISSION PLAN
            </div>
            <div style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 700 }}>
              FIRST GOL // CANONICAL NCPOR VOYAGE
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          title="Close Mission Plan"
          style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
            borderRadius: '4px'
          }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Body Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* Expedition Banner */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '4px', border: '1px solid #334155' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc' }}>
              44th Indian Antarctic Scientific Expedition
            </span>
            <span style={{ fontSize: '10px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '2px 6px', fontWeight: 700, borderRadius: '3px' }}>
              ISE-44
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
            Lead Agency: <strong>National Centre for Polar and Ocean Research (NCPOR)</strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10.5px', color: '#cbd5e1', marginTop: '8px' }}>
            <Calendar size={12} color="#38bdf8" />
            <span>Season: Austral Summer (January 2024 Departure)</span>
          </div>
        </div>

        {/* Assigned Ship Specs */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '4px', border: '1px solid #334155' }}>
          <div style={{ fontSize: '12px', fontWeight: 800, color: '#38bdf8', marginBottom: '8px' }}>
            ASSIGNED EXPEDITION SHIP
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
            <span style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>ORV Sagar Kanya</span>
            <span style={{ fontSize: '10.5px', color: '#22c55e', fontWeight: 700 }}>Open Water / MIZ (&lt;15% Ice)</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px' }}>
            <div style={{ background: '#0f172a', padding: '6px 8px', borderRadius: '3px' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>SHIP LENGTH</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>100.34 meters</div>
            </div>
            <div style={{ background: '#0f172a', padding: '6px 8px', borderRadius: '3px' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>WATER DRAFT</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>5.60 meters</div>
            </div>
            <div style={{ background: '#0f172a', padding: '6px 8px', borderRadius: '3px' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>CRUISING SPEED</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>9.0 knots (16.7 km/h)</div>
            </div>
            <div style={{ background: '#0f172a', padding: '6px 8px', borderRadius: '3px' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>FUEL CAPACITY</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>368.0 Tons</div>
            </div>
          </div>
        </div>

        {/* Voyage Route Steps (First GOL) */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '4px', border: '1px solid #334155' }}>
          <div style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc', marginBottom: '10px' }}>
            EXPEDITION ITINERARY (FIRST GOL)
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            
            {/* Step 1: Cape Town Departure */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800 }}>1</div>
                <div style={{ width: '2px', flex: 1, background: '#334155', margin: '3px 0' }} />
              </div>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Departure Port: Cape Town, South Africa
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                  Coordinates: 33.92°S, 18.42°E • Fuel, supply & science crew embarkation
                </div>
              </div>
            </div>

            {/* Step 2: Bharati Station */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#14b8a6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800 }}>2</div>
                <div style={{ width: '2px', flex: 1, background: '#334155', margin: '3px 0' }} />
              </div>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Waypoint 1: Bharati Maritime Access
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                  Prydz Bay, East Antarctica • <strong>48 Hours planned stay</strong> for science deployment & cargo offload
                </div>
              </div>
            </div>

            {/* Step 3: Maitri Station */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#22c55e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800 }}>3</div>
                <div style={{ width: '2px', flex: 1, background: '#334155', margin: '3px 0' }} />
              </div>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Waypoint 2: Maitri Maritime Access / India Bay
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                  Queen Maud Land • <strong>72 Hours planned stay</strong> for winter crew handover & bulk resupply
                </div>
              </div>
            </div>

            {/* Step 4: Return */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 800 }}>4</div>
              </div>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                  Return Destination: Cape Town Port
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                  Expedition completion • Safe arrival & sample offload
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Note on Custom GOL */}
        <div style={{ background: '#090d16', padding: '10px 12px', borderRadius: '4px', border: '1px solid #1e293b', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Info size={16} color="#94a3b8" />
          <span style={{ fontSize: '10.5px', color: '#94a3b8' }}>
            Currently locked to the canonical <strong>First GOL</strong>. Custom waypoint planner will be available in future releases.
          </span>
        </div>

      </div>
    </div>
  );
};
