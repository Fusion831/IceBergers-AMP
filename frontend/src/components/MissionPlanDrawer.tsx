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
        background: '#0a0f1d',
        border: '1.5px solid #0284c7',
        borderRadius: '6px',
        boxShadow: '0 16px 48px rgba(0, 0, 0, 0.85)',
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
          background: '#131d31',
          borderBottom: '1px solid #1e2c45',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Ship size={18} color="#38bdf8" />
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.3px' }}>
              EXPEDITION MISSION PLAN
            </div>
            <div style={{ fontSize: '10.5px', color: '#38bdf8', fontWeight: 700 }}>
              CANONICAL FIRST GOL // 44th INDIAN ANTARCTIC EXPEDITION
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
        <div style={{ background: '#111a2e', padding: '12px', borderRadius: '5px', border: '1px solid #22324e' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12.5px', fontWeight: 800, color: '#f8fafc' }}>
              44th Indian Antarctic Scientific Expedition (ISE-44)
            </span>
            <span style={{ fontSize: '9.5px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '2px 6px', fontWeight: 700, borderRadius: '3px' }}>
              FIRST GOL
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
            Operating Authority: <strong>National Centre for Polar and Ocean Research (NCPOR / MoES)</strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10.5px', color: '#cbd5e1', marginTop: '6px' }}>
            <Calendar size={12} color="#38bdf8" />
            <span>Austral Summer Season (Departure: January 2024 • Table Bay, Cape Town)</span>
          </div>
        </div>

        {/* Complete Vessel Specifications (EXPOSED COMPLETELY) */}
        <div style={{ background: '#111a2e', padding: '12px', borderRadius: '5px', border: '1px solid #22324e' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Anchor size={14} color="#38bdf8" />
              <span style={{ fontSize: '12px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase' }}>
                ASSIGNED EXPEDITION SHIP SPECIFICATIONS
              </span>
            </div>
            <span style={{ fontSize: '9px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', padding: '2px 5px', fontWeight: 700, borderRadius: '3px' }}>
              ORV SAGAR KANYA
            </span>
          </div>

          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '10px' }}>
            IMO: <strong>8114405</strong> • Call Sign: <strong>VWCX</strong> • Flag: <strong>India</strong> • Home Port: <strong>Mormugao / Goa</strong>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px' }}>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>LENGTH OVERALL (LOA)</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>100.34 meters</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>BEAM (BREADTH)</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>16.39 meters</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>WATER DRAFT (MAX)</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>5.60 meters</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>GROSS TONNAGE</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>4,209 GT (1,328 DWT)</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>SERVICE SPEED</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>9.0 knots (Max: 14.25 kn)</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>BUNKER FUEL CAPACITY</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>368.05 MT (433 m³)</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>CRUISING FUEL BURN</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>8.16 MT / day</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>VOYAGE ENDURANCE</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>45 Days unassisted</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>ICE CAPABILITY</div>
              <div style={{ color: '#10b981', fontWeight: 700 }}>Marginal Ice (&lt;15% SIC)</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '7px 9px', borderRadius: '4px', border: '1px solid #1a263d' }}>
              <div style={{ color: '#64748b', fontSize: '9.5px' }}>CREW & SCIENTISTS</div>
              <div style={{ color: '#f8fafc', fontWeight: 700 }}>91 Berths (31 + 60)</div>
            </div>
          </div>

          <div style={{ marginTop: '8px', padding: '6px 8px', background: '#0a0f1d', borderRadius: '4px', border: '1px solid #1a263d', fontSize: '10px', color: '#94a3b8' }}>
            Propulsion: Twin diesel-electric motors (2 × 1,280 kW) driving twin controllable pitch propellers with 360° bow thruster (590 kW).
          </div>
        </div>

        {/* Start, Waypoints & Endpoint with EXPOSED Latitude & Longitude */}
        <div style={{ background: '#111a2e', padding: '12px', borderRadius: '5px', border: '1px solid #22324e' }}>
          <div style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Compass size={14} color="#10b981" />
            <span>EXPEDITION WAYPOINTS & COORDINATES</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            
            {/* Step 1: Cape Town Departure */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10.5px', fontWeight: 800 }}>1</div>
                <div style={{ width: '2px', flex: 1, background: '#1e2c45', margin: '4px 0' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                    Start: Cape Town Staging Gateway
                  </div>
                  <div style={{ fontSize: '10px', color: '#38bdf8', fontFamily: 'monospace', fontWeight: 800 }}>
                    33.9249° S, 18.4241° E
                  </div>
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                  Port of Cape Town, Table Bay, South Africa • Fuel bunkering & expedition embarkation
                </div>
              </div>
            </div>

            {/* Step 2: Bharati Station */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: '#14b8a6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10.5px', fontWeight: 800 }}>2</div>
                <div style={{ width: '2px', flex: 1, background: '#1e2c45', margin: '4px 0' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                    Waypoint 1: Bharati Maritime Access
                  </div>
                  <div style={{ fontSize: '10px', color: '#14b8a6', fontFamily: 'monospace', fontWeight: 800 }}>
                    69.4000° S, 76.1900° E
                  </div>
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                  Prydz Bay, Larsemann Hills, Princess Elizabeth Land • <strong>48 Hours anchorage dwell</strong> for scientific deployment & cargo offload
                </div>
              </div>
            </div>

            {/* Step 3: Maitri Station */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10.5px', fontWeight: 800 }}>3</div>
                <div style={{ width: '2px', flex: 1, background: '#1e2c45', margin: '4px 0' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                    Waypoint 2: Maitri Maritime Access / India Bay
                  </div>
                  <div style={{ fontSize: '10px', color: '#10b981', fontFamily: 'monospace', fontWeight: 800 }}>
                    69.9500° S, 11.7300° E
                  </div>
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
                  Princess Astrid Coast, Lazarev Sea, Queen Maud Land • <strong>72 Hours shelf mooring</strong> for bulk fuel transfer & overwintering crew handover
                </div>
              </div>
            </div>

            {/* Step 4: Return */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10.5px', fontWeight: 800 }}>4</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                    Endpoint: Cape Town Staging Gateway
                  </div>
                  <div style={{ fontSize: '10px', color: '#f59e0b', fontFamily: 'monospace', fontWeight: 800 }}>
                    33.9249° S, 18.4241° E
                  </div>
                </div>
                <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '2px' }}>
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
