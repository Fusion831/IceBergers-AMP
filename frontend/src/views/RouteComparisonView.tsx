import React from 'react';
import { useMission } from '../context/MissionContext';
import { RouteRadarChart } from '../components/RouteRadarChart';
import ReactECharts from 'echarts-for-react';
import {
  Navigation,
  Shield,
  Fuel,
  ArrowRight
} from 'lucide-react';

export const RouteComparisonView: React.FC = () => {
  const { routes, selectedRouteId, setSelectedRouteId, setActiveView } = useMission();

  // ECharts Bar Chart comparing Route Fuel vs Transit Days - Light Blue & White Theme
  const barOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      textStyle: { color: '#0f172a', fontSize: 11, fontFamily: 'var(--font-mono)' }
    },
    legend: {
      data: ['Transit Duration (Days)', 'Estimated Fuel (Metric Tons)'],
      textStyle: { color: '#172554', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 },
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: routes.map((r) => r.name.replace(' Route', '').replace(' Multi-Objective', '').replace(' Low-Ice Corridor', '').replace(' Direct', '').replace(' Ocean-Current', '')),
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Days',
        nameTextStyle: { color: '#0d9488', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 },
        splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
        axisLabel: { color: '#1e293b', fontFamily: 'var(--font-mono)' }
      },
      {
        type: 'value',
        name: 'Fuel (MT)',
        nameTextStyle: { color: '#ea580c', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 },
        position: 'right',
        splitLine: { show: false },
        axisLabel: { color: '#1e293b', fontFamily: 'var(--font-mono)' }
      }
    ],
    series: [
      {
        name: 'Transit Duration (Days)',
        type: 'bar',
        data: routes.map((r) => r.transitDays),
        itemStyle: { color: '#0d9488', borderRadius: 0 },
        barWidth: '22%'
      },
      {
        name: 'Estimated Fuel (Metric Tons)',
        type: 'bar',
        yAxisIndex: 1,
        data: routes.map((r) => r.estimatedFuelMT),
        itemStyle: { color: '#ea580c', borderRadius: 0 },
        barWidth: '22%'
      }
    ]
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%', overflowY: 'auto', padding: '4px' }}>

      {/* Top Banner */}
      <div className="ws-panel" style={{ padding: '12px 16px', background: 'rgba(240, 248, 255, 0.65)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '10px', fontWeight: 800, padding: '2px 6px', borderRadius: '0px', background: 'rgba(239, 246, 255, 0.85)', color: '#2563eb', border: '1px solid #93c5fd', fontFamily: 'var(--font-mono)' }}>
            CORE VIEW 5 OF 6
          </span>
          <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 800, color: '#172554', margin: 0 }}>
            MULTI-OBJECTIVE ROUTE ALTERNATIVE COMPARISON (PRD §65)
          </h2>
        </div>
        <p style={{ fontSize: '11px', color: '#475569', marginTop: '4px', fontFamily: 'var(--font-mono)', margin: 0 }}>
          Side-by-side quantitative benchmarking across Safest, Fastest, and Balanced Antarctic transit routes.
        </p>
      </div>

      {/* Main PRD Section 65 Comparison Table */}
      <div className="ws-panel" style={{ padding: '14px 16px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Navigation size={14} color="#2563eb" />
          <h3 style={{ fontSize: '12px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
            CANDIDATE NAVIGATION ROUTES TRADE-OFF MATRIX
          </h3>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
            <thead>
              <tr style={{ background: 'rgba(224, 242, 254, 0.75)', color: '#172554', borderBottom: '1.5px solid rgba(191, 219, 254, 0.85)', borderTop: '1px solid rgba(191, 219, 254, 0.85)', textAlign: 'left' }}>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>ROUTE ALTERNATIVE</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>DISTANCE (NM)</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>TRANSIT TIME</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>ESTIMATED FUEL</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>ICE EXPOSURE</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>ICEBERG RISK</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>WEATHER SCORE</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>MEDIAN RISK</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>P95 RISK</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>CONFIDENCE</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {routes.map((r) => {
                const isSelected = selectedRouteId === r.id;
                return (
                  <tr
                    key={r.id}
                    onClick={() => setSelectedRouteId(r.id)}
                    style={{
                      borderBottom: '1px solid rgba(226, 232, 240, 0.8)',
                      background: isSelected ? 'rgba(255, 255, 255, 0.85)' : 'transparent',
                      cursor: 'pointer'
                    }}
                  >
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '0px', backgroundColor: r.color, border: '1px solid #fff', display: 'inline-block' }}></span>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: '12.5px', color: isSelected ? '#2563eb' : '#0f172a' }}>{r.name}</div>
                          <div style={{ fontSize: '10.5px', color: r.color, fontWeight: 700 }}>{r.tag}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#0f172a', fontWeight: 700, fontSize: '12px' }}>{r.distanceNM.toLocaleString()} NM</td>
                    <td style={{ padding: '10px 12px', fontWeight: 800, color: '#0f172a', fontSize: '12.5px' }}>{r.transitDays} Days</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '0px',
                        fontSize: '11px',
                        border: '1px solid rgba(191, 219, 254, 0.85)',
                        background: 'rgba(255, 255, 255, 0.85)',
                        fontWeight: 800,
                        color: '#0f172a'
                      }}>
                        {r.estimatedFuelMT} MT
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontWeight: 800, fontSize: '12px', color: r.seaIceExposurePct > 30 ? '#dc2626' : '#0d9488' }}>{r.seaIceExposurePct}%</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '0px',
                        fontSize: '11px',
                        border: '1px solid rgba(191, 219, 254, 0.85)',
                        background: 'rgba(255, 255, 255, 0.85)',
                        fontWeight: 800,
                        color: r.icebergRiskIndex < 25 ? '#0d9488' : '#dc2626'
                      }}>
                        {r.icebergRiskIndex}/100
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#0f172a', fontSize: '12px', fontWeight: 600 }}>{r.weatherSeverityScore}/100</td>
                    <td style={{ padding: '10px 12px', fontWeight: 800, color: '#0f172a', fontSize: '12px' }}>{r.medianRisk}</td>
                    <td style={{ padding: '10px 12px', color: r.p95Risk > 0.6 ? '#dc2626' : '#0f172a', fontWeight: 800, fontSize: '12px' }}>{r.p95Risk}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '0px',
                        fontSize: '10.5px',
                        fontWeight: 800,
                        border: '1px solid #93c5fd',
                        background: 'rgba(239, 246, 255, 0.85)',
                        color: '#2563eb'
                      }}>
                        {r.confidence}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedRouteId(r.id);
                        }}
                        style={{
                          padding: '5px 12px',
                          borderRadius: '0px',
                          border: '1px solid',
                          borderColor: isSelected ? '#1d4ed8' : '#bfdbfe',
                          borderBottom: isSelected ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                          background: isSelected ? '#2563eb' : 'rgba(255, 255, 255, 0.85)',
                          color: isSelected ? '#ffffff' : '#1e293b',
                          fontSize: '11px',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 800,
                          cursor: 'pointer',
                          boxShadow: isSelected ? 'inset 0 1px 0 rgba(255,255,255,0.35), 0 3px 0 #1e3a8a' : 'inset 0 1px 0 rgba(255,255,255,0.7), 0 3px 0 #93c5fd'
                        }}
                      >
                        {isSelected ? 'ACTIVE' : 'SELECT'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Trade-Offs Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

        {/* Radar Trade-Off Chart */}
        <div className="ws-panel" style={{ padding: '14px 16px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Shield size={14} color="#2563eb" />
            <h3 style={{ fontSize: '12px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
              MULTI-OBJECTIVE RADAR NORMALIZATION
            </h3>
          </div>
          <RouteRadarChart />
        </div>

        {/* Transit Days vs Fuel Consumption Bar Chart */}
        <div className="ws-panel" style={{ padding: '14px 16px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Fuel size={14} color="#2563eb" />
            <h3 style={{ fontSize: '12px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
              TRANSIT DURATION VS ESTIMATED FUEL CONSUMPTION
            </h3>
          </div>
          <div style={{ width: '100%', height: '220px' }}>
            <ReactECharts option={barOption} style={{ width: '100%', height: '100%' }} />
          </div>
        </div>

      </div>

      {/* Bottom Action Bar */}
      <div className="ws-panel" style={{
        padding: '12px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(240, 248, 255, 0.75)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        border: '1px solid rgba(191, 219, 254, 0.75)',
        marginTop: '1px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ width: '8px', height: '8px', backgroundColor: (routes.find((r) => r.id === selectedRouteId) || routes[0]).color, border: '1px solid #fff', display: 'inline-block' }}></span>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#172554', fontFamily: 'var(--font-mono)' }}>
            ACTIVE SELECTION: {(routes.find((r) => r.id === selectedRouteId) || routes[0]).name.toUpperCase()} // {(routes.find((r) => r.id === selectedRouteId) || routes[0]).distanceNM.toLocaleString()} NM // {(routes.find((r) => r.id === selectedRouteId) || routes[0]).transitDays} DAYS // {(routes.find((r) => r.id === selectedRouteId) || routes[0]).estimatedFuelMT} MT FUEL
          </span>
        </div>

        <button
          onClick={() => setActiveView('antarctic-map')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '9px 20px',
            borderRadius: '0px',
            background: '#2563eb',
            color: '#ffffff',
            border: '1px solid #1d4ed8',
            borderBottom: '3px solid #1e3a8a',
            fontSize: '11.5px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 800,
            cursor: 'pointer',
            letterSpacing: '0.03em',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 3px 0 #1e3a8a'
          }}
        >
          <span>PLOT SELECTED ROUTE ON MAP WORKSPACE</span>
          <ArrowRight size={14} />
        </button>
      </div>

    </div>
  );
};
