import React, { useState } from 'react';
import { useMission } from '../context/MissionContext';
import { AntarcticMap } from '../components/AntarcticMap';
import { ExplainabilityCard } from '../components/ExplainabilityCard';
import ReactECharts from 'echarts-for-react';
import {
  Layers,
  Navigation,
  Crosshair,
  ExternalLink,
  X,
  Cpu,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';

export const AntarcticMapView: React.FC = () => {
  const {
    timeHorizon,
    setTimeHorizon,
    activeMapLayer,
    setActiveMapLayer,
    routes,
    selectedRouteId,
    setSelectedRouteId,
    setActiveView,
    inspectionPoint
  } = useMission();

  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [showInspectorPopover, setShowInspectorPopover] = useState<boolean>(false);

  // Ensemble Spreads & Quantiles ECharts (P10, P50, P90 Quantiles) - Light Blue & White Theme
  const ensembleChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      padding: [8, 12],
      textStyle: { color: '#0f172a', fontSize: 11, fontFamily: 'var(--font-mono)' }
    },
    legend: {
      data: ['P50 Ensemble Median', '90% Quantile Envelope [P10-P90]'],
      textStyle: { color: '#1e3a8a', fontSize: 10.5, fontFamily: 'var(--font-sans)', fontWeight: 700 },
      top: 0,
      right: 0,
      itemWidth: 12,
      itemHeight: 6
    },
    grid: {
      left: '2%',
      right: '2%',
      bottom: '6%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['T+0', 'T+24H', 'T+72H', 'T+168H', 'T+336H', 'T+30D', 'T+60D', 'T+90D'],
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 600 }
    },
    yAxis: {
      type: 'value',
      name: 'SIC (%)',
      nameTextStyle: { color: '#172554', fontSize: 10, align: 'left', fontWeight: 700 },
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      axisLabel: { color: '#1e293b', fontSize: 10, formatter: '{value}%', fontFamily: 'var(--font-mono)' }
    },
    series: [
      {
        name: 'P10 Lower',
        type: 'line',
        data: [22, 24, 28, 34, 42, 52, 60, 66],
        lineStyle: { opacity: 0 },
        stack: 'ensemble-band',
        symbol: 'none'
      },
      {
        name: '90% Quantile Envelope [P10-P90]',
        type: 'line',
        data: [12, 14, 16, 18, 22, 24, 26, 28],
        lineStyle: { opacity: 0 },
        areaStyle: { color: 'rgba(37, 99, 235, 0.18)' },
        stack: 'ensemble-band',
        symbol: 'none'
      },
      {
        name: 'P50 Ensemble Median',
        type: 'line',
        data: [28, 30, 34, 42, 51, 63, 72, 79],
        smooth: false,
        lineStyle: { width: 2.2, color: '#2563eb' },
        itemStyle: { color: '#2563eb' },
        symbol: 'rect',
        symbolSize: 5
      }
    ]
  };

  return (
    <div style={{ display: 'flex', gap: '10px', height: '100%', overflow: 'hidden', padding: '8px' }}>

      {/* Left Workstation Sidebar (Collapsible) */}
      {isSidebarOpen && (
        <div style={{
          width: '330px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          overflowY: 'auto',
          flexShrink: 0
        }}>

          {/* Intelligence Layer Selector */}
          <div className="ws-panel" style={{ background: 'rgba(240, 248, 255, 0.72)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
            <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.75)', borderBottom: '1px solid rgba(191, 219, 254, 0.85)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={14} color="#2563eb" />
                <span>MAP OVERLAY LAYERS</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="ws-badge ws-badge-info">
                  {timeHorizon} LEAD
                </span>
                <button
                  onClick={() => setIsSidebarOpen(false)}
                  title="Close Sidebar"
                  style={{
                    background: 'rgba(255, 255, 255, 0.85)',
                    border: '1px solid #bfdbfe',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '3px 5px',
                    color: '#2563eb'
                  }}
                >
                  <PanelLeftClose size={13} />
                </button>
              </div>
            </div>

            <div style={{ padding: '8px 10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              {[
                { id: 'sic', label: 'Sea-Ice (SIC)', desc: 'Raster & 15% Edge' },
                { id: 'icebergs', label: 'Iceberg Tracks', desc: 'Observed Scatter' },
                { id: 'risk', label: 'Risk Gradient', desc: 'Stepped Scale Cost' },
                { id: 'weather', label: 'Wind / Waves', desc: 'ERA5 & WW3 Swell' }
              ].map((layer) => {
                const isActive = activeMapLayer === layer.id;
                return (
                  <button
                    key={layer.id}
                    onClick={() => setActiveMapLayer(layer.id as any)}
                    style={{
                      padding: '6px 10px',
                      borderRadius: '0px',
                      border: '1px solid',
                      borderColor: isActive ? '#1d4ed8' : 'rgba(191, 219, 254, 0.85)',
                      borderBottom: isActive ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                      background: isActive ? '#dbeafe' : 'rgba(255, 255, 255, 0.80)',
                      color: isActive ? '#1e3a8a' : '#1e293b',
                      fontSize: '11.5px',
                      fontWeight: isActive ? 800 : 500,
                      cursor: 'pointer',
                      textAlign: 'left',
                      boxShadow: isActive ? '0 2px 0 #1e3a8a, 0 3px 5px rgba(30, 58, 138, 0.2)' : '0 2px 0 #93c5fd, 0 2px 4px rgba(37, 99, 235, 0.08)'
                    }}
                  >
                    <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 700 }}>{layer.label}</div>
                    <div style={{ fontSize: '9.5px', color: isActive ? '#2563eb' : '#64748b', marginTop: '2px' }}>
                      {layer.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Candidate Routes Selector */}
          <div className="ws-panel" style={{ background: 'rgba(240, 248, 255, 0.72)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
            <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.75)', borderBottom: '1px solid rgba(191, 219, 254, 0.85)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Navigation size={14} color="#2563eb" />
                <span>CANDIDATE ROUTES</span>
              </div>
              <button
                onClick={() => setActiveView('route-comparison')}
                style={{
                  fontSize: '10.5px',
                  color: '#2563eb',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontFamily: 'var(--font-sans)',
                  fontWeight: 700
                }}
              >
                <span>COMPARE ALL</span>
                <ExternalLink size={10} />
              </button>
            </div>

            <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {routes.map((r) => {
                const isSelected = selectedRouteId === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => setSelectedRouteId(r.id)}
                    style={{
                      padding: '6px 10px',
                      borderRadius: '0px',
                      border: '1px solid',
                      borderColor: isSelected ? '#2563eb' : 'rgba(191, 219, 254, 0.85)',
                      background: isSelected ? 'rgba(255, 255, 255, 0.90)' : 'rgba(255, 255, 255, 0.65)',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '3px',
                      borderLeft: isSelected ? '4px solid #2563eb' : '1px solid rgba(191, 219, 254, 0.85)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '11.5px', fontWeight: 800, color: isSelected ? '#1e3a8a' : '#0f172a' }}>{r.name}</span>
                      <span style={{ fontSize: '10px', color: r.color, fontWeight: 800, fontFamily: 'var(--font-sans)' }}>{r.tag}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                      <span>ETA: <strong style={{ color: '#0f172a' }}>{r.transitDays}d</strong></span>
                      <span>Fuel: <strong style={{ color: '#0f172a' }}>{r.estimatedFuelMT} MT</strong></span>
                      <span>Risk: <strong style={{ color: r.medianRisk > 0.4 ? '#dc2626' : '#0d9488' }}>{(r.medianRisk * 100).toFixed(0)}%</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Point Inspector Trigger */}
          <div className="ws-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(10px)', border: '1px solid rgba(191, 219, 254, 0.85)', padding: '8px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Crosshair size={14} color="#2563eb" />
              <span style={{ fontSize: '11px', color: '#0f172a', fontWeight: 700, fontFamily: 'var(--font-sans)' }}>
                Prydz Bay Lead (68.4°S, 74.2°E)
              </span>
            </div>
            <button
              onClick={() => setShowInspectorPopover(true)}
              style={{
                padding: '5px 12px',
                borderRadius: '0px',
                background: '#2563eb',
                border: '1px solid #1d4ed8',
                borderBottom: '3px solid #1e3a8a',
                color: '#ffffff',
                fontSize: '10.5px',
                fontFamily: 'var(--font-sans)',
                fontWeight: 800,
                cursor: 'pointer',
                boxShadow: '0 2px 0 #1e3a8a, 0 3px 6px rgba(30, 58, 138, 0.25)'
              }}
            >
              INSPECT ➔
            </button>
          </div>

          {/* Explainability Decision Support Card */}
          <ExplainabilityCard />
        </div>
      )}

      {/* Central Antarctic Map Workspace */}
      <div style={{ flex: 1, position: 'relative', height: '100%', minHeight: '450px', border: '1px solid rgba(191, 219, 254, 0.75)', display: 'flex', flexDirection: 'column' }}>

        {/* Toggle Sidebar Button when closed */}
        {!isSidebarOpen && (
          <button
            onClick={() => setIsSidebarOpen(true)}
            style={{
              position: 'absolute',
              top: '9px',
              left: '8px',
              zIndex: 30,
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
              padding: '6px 5px',
              background: '#2563eb',
              border: '1px solid #1d4ed8',
              borderBottom: '3px solid #1e3a8a',
              color: '#ffffff',
              fontSize: '11px',
              fontFamily: 'var(--font-sans)',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: '0 2px 0 #1e3a8a, 0 3px 5px rgba(30, 58, 138, 0.25)'
            }}
          >
            <PanelLeftOpen size={10} />
            <span></span>
          </button>
        )}

        <AntarcticMap
          selectedHorizon={timeHorizon}
          activeLayer={activeMapLayer}
          selectedRoute={selectedRouteId}
          onHorizonChange={(hz) => setTimeHorizon(hz as any)}
          onInspectPoint={() => setShowInspectorPopover(true)}
        />

        {/* Prediction Inspector Popover / Side Panel */}
        {showInspectorPopover && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            width: '400px',
            zIndex: 40,
            background: 'rgba(255, 255, 255, 0.90)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1.5px solid #2563eb',
            borderRadius: '0px',
            boxShadow: '0 8px 24px rgba(30, 58, 138, 0.2)'
          }}>
            <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.85)', borderBottom: '1px solid #bfdbfe', padding: '8px 12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Cpu size={14} color="#2563eb" />
                <span style={{ color: '#172554', fontWeight: 800 }}>INSPECTOR: CELL #{inspectionPoint.lat}°S, {inspectionPoint.lon}°E</span>
              </div>
              <button
                onClick={() => setShowInspectorPopover(false)}
                style={{ background: 'transparent', border: 'none', color: '#1e293b', cursor: 'pointer', display: 'flex', alignItems: 'center', boxShadow: 'none' }}
              >
                <X size={15} />
              </button>
            </div>

            <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>

              {/* Provenance Metadata Tags with crisp borders */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', background: 'rgba(240, 248, 255, 0.80)', padding: '6px 8px', borderRadius: '0px', border: '1px solid #bfdbfe' }}>
                <div>
                  <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-sans)', fontWeight: 700 }}>Source</div>
                  <div style={{ fontSize: '10.5px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0f172a' }}>[Copernicus Sentinel-1]</div>
                </div>
                <div>
                  <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-sans)', fontWeight: 700 }}>Valid Time</div>
                  <div style={{ fontSize: '10.5px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0d9488' }}>T+{timeHorizon} UTC</div>
                </div>
                <div>
                  <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-sans)', fontWeight: 700 }}>Model Ver</div>
                  <div style={{ fontSize: '10.5px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#2563eb' }}>AMIP-v2.4</div>
                </div>
              </div>

              {/* Ensemble Spreads & Quantiles Chart */}
              <div>
                <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', marginBottom: '4px', fontFamily: 'var(--font-sans)' }}>
                  Ensemble Spreads & P10-P90 Quantiles
                </div>
                <div style={{ width: '100%', height: '175px' }}>
                  <ReactECharts option={ensembleChartOption} style={{ width: '100%', height: '100%' }} />
                </div>
              </div>

              {/* Quick Telemetry Summary */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px', fontFamily: 'var(--font-sans)' }}>
                <div style={{ padding: '6px 10px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid #bfdbfe', borderRadius: '0px' }}>
                  <span style={{ color: '#64748b', fontWeight: 600 }}>P50 Forecast SIC:</span>
                  <div style={{ fontWeight: 800, color: '#0f172a', fontFamily: 'var(--font-mono)' }}>{inspectionPoint.forecastSIC}%</div>
                </div>
                <div style={{ padding: '6px 10px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid #bfdbfe', borderRadius: '0px' }}>
                  <span style={{ color: '#64748b', fontWeight: 600 }}>Confidence:</span>
                  <div style={{ fontWeight: 800, color: '#0d9488', fontFamily: 'var(--font-mono)' }}>{inspectionPoint.modelConfidence}%</div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px', marginTop: '4px' }}>
                <button
                  onClick={() => {
                    setShowInspectorPopover(false);
                    setActiveView('prediction-inspector');
                  }}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '0px',
                    background: '#2563eb',
                    border: '1px solid #1d4ed8',
                    borderBottom: '3px solid #1e3a8a',
                    color: '#ffffff',
                    fontSize: '11px',
                    fontFamily: 'var(--font-sans)',
                    fontWeight: 800,
                    cursor: 'pointer',
                    boxShadow: '0 2px 0 #1e3a8a, 0 3px 6px rgba(30, 58, 138, 0.25)'
                  }}
                >
                  EXPAND FULL BENCHMARKS VIEW ➔
                </button>
              </div>

            </div>
          </div>
        )}
      </div>

    </div>
  );
};
