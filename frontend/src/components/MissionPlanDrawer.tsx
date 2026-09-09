import React from 'react';
import { X, Ship, Calendar, Compass, Anchor } from 'lucide-react';

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
        width: '440px',
        maxWidth: 'calc(100vw - 24px)',
        zIndex: 50,
        background: '#0d1117',
        border: '1px solid #30363d',
        borderRadius: '8px',
        boxShadow: '0 20px 48px rgba(0, 0, 0, 0.65)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        color: '#f0f6fc',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '14px 16px',
          background: '#161b22',
          borderBottom: '1px solid #21262d',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Ship size={18} color="#58a6ff" />
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#f0f6fc', letterSpacing: '0.2px' }}>
              Expedition Mission Plan
            </div>
            <div style={{ fontSize: '11px', color: '#8b949e', fontWeight: 500 }}>
              44th Indian Antarctic Scientific Expedition (ISE-44)
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
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        
        {/* Expedition Organization Card */}
        <div style={{ background: '#161b22', padding: '12px', borderRadius: '6px', border: '1px solid #30363d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12.5px', fontWeight: 700, color: '#f0f6fc' }}>
              44th Indian Antarctic Scientific Expedition (ISE-44)
            </span>
            <span style={{ fontSize: '10px', background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', padding: '2px 8px', fontWeight: 600, borderRadius: '4px', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
              PRIMARY VOYAGE
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '4px' }}>
            Operating Authority: <strong style={{ color: '#c9d1d9' }}>National Centre for Polar and Ocean Research (NCPOR / MoES)</strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#8b949e', marginTop: '6px' }}>
            <Calendar size={12} color="#58a6ff" />
            <span>Austral Summer Season (Departure: January 2024 • Table Bay, Cape Town)</span>
          </div>
        </div>

        {/* Complete Vessel Specifications */}
        <div style={{ background: '#161b22', padding: '12px', borderRadius: '6px', border: '1px solid #30363d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Anchor size={14} color="#58a6ff" />
              <span style={{ fontSize: '11.5px', fontWeight: 700, color: '#f0f6fc', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                Assigned Expedition Vessel Specifications
              </span>
            </div>
            <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.12)', color: '#34d399', padding: '2px 8px', fontWeight: 600, borderRadius: '4px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
              ORV SAGAR KANYA
            </span>
          </div>

          <div style={{ fontSize: '11px', color: '#8b949e', marginBottom: '10px' }}>
            IMO: <strong style={{ color: '#c9d1d9' }}>8114405</strong> • Call Sign: <strong style={{ color: '#c9d1d9' }}>VWCX</strong> • Flag: <strong style={{ color: '#c9d1d9' }}>India</strong> • Home Port: <strong style={{ color: '#c9d1d9' }}>Mormugao / Goa</strong>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px' }}>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Length Overall (LOA)</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>100.34 meters</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Beam (Breadth)</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>16.39 meters</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Water Draft (Max)</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>5.60 meters</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Gross Tonnage</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>4,209 GT (1,328 DWT)</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Service Speed</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>9.0 knots (Max: 14.25 kn)</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Bunker Fuel Capacity</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>368.05 MT (433 m³)</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Cruising Fuel Burn</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>8.16 MT / day</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Voyage Endurance</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>45 Days unassisted</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Ice Capability</div>
              <div style={{ color: '#34d399', fontWeight: 600 }}>Marginal Ice (&lt;15% SIC)</div>
            </div>
            <div style={{ background: '#0d1117', padding: '8px 10px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ color: '#8b949e', fontSize: '9.5px', textTransform: 'uppercase', letterSpacing: '0.2px' }}>Crew & Scientific Berths</div>
              <div style={{ color: '#f0f6fc', fontWeight: 600 }}>91 Berths (31 + 60)</div>
            </div>
          </div>

          <div style={{ marginTop: '8px', padding: '8px 10px', background: '#0d1117', borderRadius: '4px', border: '1px solid #21262d', fontSize: '10.5px', color: '#8b949e' }}>
            Propulsion: Twin diesel-electric motors (2 × 1,280 kW) driving twin controllable pitch propellers with 360° bow thruster (590 kW).
          </div>
        </div>

        {/* Start, Waypoints & Endpoint */}
        <div style={{ background: '#161b22', padding: '12px', borderRadius: '6px', border: '1px solid #30363d' }}>
          <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#f0f6fc', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
            <Compass size={14} color="#34d399" />
            <span>Expedition Waypoints & Coordinates</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            
            {/* Step 1: Cape Town Departure */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#2563eb', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>1</div>
                <div style={{ width: '2px', flex: 1, background: '#21262d', margin: '4px 0' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#f0f6fc' }}>
                    Start: Cape Town Staging Gateway
                  </div>
                  <div style={{ fontSize: '11px', color: '#58a6ff', fontWeight: 600 }}>
                    33.9249° S, 18.4241° E
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', lineHeight: '1.4' }}>
                  Port of Cape Town, Table Bay, South Africa • Fuel bunkering & expedition embarkation
                </div>
              </div>
            </div>

            {/* Step 2: Bharati Station */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#0d9488', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>2</div>
                <div style={{ width: '2px', flex: 1, background: '#21262d', margin: '4px 0' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#f0f6fc' }}>
                    Waypoint 1: Bharati Maritime Access
                  </div>
                  <div style={{ fontSize: '11px', color: '#2dd4bf', fontWeight: 600 }}>
                    69.4000° S, 76.1900° E
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', lineHeight: '1.4' }}>
                  Prydz Bay, Larsemann Hills, Princess Elizabeth Land • <strong style={{ color: '#c9d1d9' }}>48 Hours anchorage dwell</strong> for scientific deployment & cargo offload
                </div>
              </div>
            </div>

            {/* Step 3: Maitri Station */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#059669', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>3</div>
                <div style={{ width: '2px', flex: 1, background: '#21262d', margin: '4px 0' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#f0f6fc' }}>
                    Waypoint 2: Maitri Maritime Access / India Bay
                  </div>
                  <div style={{ fontSize: '11px', color: '#34d399', fontWeight: 600 }}>
                    69.9500° S, 11.7300° E
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', lineHeight: '1.4' }}>
                  Princess Astrid Coast, Lazarev Sea, Queen Maud Land • <strong style={{ color: '#c9d1d9' }}>72 Hours shelf mooring</strong> for bulk fuel transfer & overwintering crew handover
                </div>
              </div>
            </div>

            {/* Step 4: Return */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#d97706', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>4</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#f0f6fc' }}>
                    Endpoint: Cape Town Staging Gateway
                  </div>
                  <div style={{ fontSize: '11px', color: '#fbbf24', fontWeight: 600 }}>
                    33.9249° S, 18.4241° E
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', lineHeight: '1.4' }}>
                  Table Bay Harbor • Safe return arrival, scientific sample demobilization & expedition completion
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};
