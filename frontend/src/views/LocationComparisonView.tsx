import React from 'react';
import { useMission } from '../context/MissionContext';
import ReactECharts from 'echarts-for-react';
import {
  MapPin,
  CheckCircle2,
  AlertCircle,
  XCircle,
  TrendingUp,
  ExternalLink
} from 'lucide-react';

export const LocationComparisonView: React.FC = () => {
  const { locations, selectedLocationId, setSelectedLocationId, setActiveView } = useMission();

  const selectedLoc = locations.find((l) => l.id === selectedLocationId) || locations[0];

  // ECharts Bar Chart comparing Location Operating Favorable Probabilities & SIC - Light Blue Theme
  const comparisonChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      textStyle: { color: '#0f172a', fontSize: 11.5, fontFamily: 'var(--font-mono)' }
    },
    legend: {
      data: ['Favorable Probability (%)', 'Median SIC (%)', 'P90 SIC (%)'],
      textStyle: { color: '#172554', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
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
      data: locations.map((l) => l.name.split(' (')[0]),
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, interval: 0, fontFamily: 'var(--font-mono)', fontWeight: 700 }
    },
    yAxis: {
      type: 'value',
      max: 100,
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, formatter: '{value}%', fontFamily: 'var(--font-mono)' }
    },
    series: [
      {
        name: 'Favorable Probability (%)',
        type: 'bar',
        data: locations.map((l) => l.favorableProbability),
        itemStyle: { color: '#0d9488', borderRadius: 0 },
        barWidth: '20%'
      },
      {
        name: 'Median SIC (%)',
        type: 'bar',
        data: locations.map((l) => l.medianSIC),
        itemStyle: { color: '#1e3a8a', borderRadius: 0 },
        barWidth: '20%'
      },
      {
        name: 'P90 SIC (%)',
        type: 'bar',
        data: locations.map((l) => l.p90SIC),
        itemStyle: { color: '#ea580c', borderRadius: 0 },
        barWidth: '20%'
      }
    ]
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%', overflowY: 'auto', padding: '4px' }}>

      {/* Top Banner */}
      <div className="ws-panel" style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(240, 248, 255, 0.65)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '10.5px', fontWeight: 800, padding: '2px 7px', borderRadius: '0px', background: 'rgba(239, 246, 255, 0.85)', color: '#2563eb', border: '1px solid #93c5fd', fontFamily: 'var(--font-mono)' }}>
              CORE VIEW 4 OF 6
            </span>
            <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '14.5px', fontWeight: 800, color: '#172554', margin: 0 }}>
              CANDIDATE OPERATING LOCATION COMPARISON MATRIX (PRD §64)
            </h2>
          </div>
          <p style={{ fontSize: '11.5px', color: '#475569', marginTop: '4px', fontFamily: 'var(--font-mono)', margin: 0 }}>
            Multi-site comparative analysis across Indian Antarctic research stations and auxiliary scientific field landing sites.
          </p>
        </div>

        <button
          onClick={() => setActiveView('route-comparison')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '0px',
            background: 'rgba(255, 255, 255, 0.9)',
            border: '1px solid #2563eb',
            borderBottom: '3px solid #1d4ed8',
            color: '#2563eb',
            fontSize: '11.5px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 800,
            cursor: 'pointer',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.7), 0 3px 0 #93c5fd'
          }}
        >
          <span>VIEW ROUTE ALTERNATIVES</span>
          <ExternalLink size={13} />
        </button>
      </div>

      {/* Main Comparison Table */}
      <div className="ws-panel" style={{ padding: '14px 16px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <MapPin size={15} color="#2563eb" />
          <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
            LOCATION FEASIBILITY & ENVIRONMENTAL ACCESSIBILITY MATRIX
          </h3>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
            <thead>
              <tr style={{ background: 'rgba(224, 242, 254, 0.75)', color: '#172554', borderBottom: '1.5px solid rgba(191, 219, 254, 0.85)', borderTop: '1px solid rgba(191, 219, 254, 0.85)', textAlign: 'left' }}>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>SITE / STATION NAME</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>SECTOR</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>FAVORABLE WINDOW</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>FAVORABLE PROB.</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>MEDIAN SIC</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>P90 SIC</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>ICEBERG EXPOSURE</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>TRANSIT DISTANCE</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>EST. FUEL BURN</th>
                <th style={{ padding: '10px 12px', fontSize: '11px', fontWeight: 800 }}>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {locations.map((loc) => {
                const isSelected = selectedLocationId === loc.id;
                return (
                  <tr
                    key={loc.id}
                    onClick={() => setSelectedLocationId(loc.id)}
                    style={{
                      borderBottom: '1px solid rgba(226, 232, 240, 0.8)',
                      background: isSelected ? 'rgba(255, 255, 255, 0.85)' : 'transparent',
                      cursor: 'pointer'
                    }}
                  >
                    <td style={{ padding: '10px 12px', fontWeight: 800, color: isSelected ? '#2563eb' : '#0f172a' }}>
                      {loc.name}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#0f172a' }}>{loc.sector}</td>
                    <td style={{ padding: '10px 12px', color: '#2563eb', fontWeight: 700 }}>{loc.operatingWindow}</td>
                    <td style={{ padding: '10px 12px', fontWeight: 800, color: loc.favorableProbability >= 75 ? '#0d9488' : loc.favorableProbability >= 60 ? '#ea580c' : '#dc2626' }}>
                      {loc.favorableProbability}%
                    </td>
                    <td style={{ padding: '10px 12px', color: '#0f172a' }}>{loc.medianSIC}%</td>
                    <td style={{ padding: '10px 12px', color: '#0f172a' }}>{loc.p90SIC}%</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '0px',
                        fontSize: '10px',
                        fontWeight: 700,
                        border: '1px solid rgba(191, 219, 254, 0.85)',
                        background: 'rgba(255, 255, 255, 0.85)',
                        color: loc.icebergExposure === 'Low' ? '#0d9488' : loc.icebergExposure === 'Moderate' ? '#ea580c' : '#dc2626'
                      }}>
                        {loc.icebergExposure.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#0f172a' }}>{loc.transitDistanceNM} NM</td>
                    <td style={{ padding: '10px 12px', color: '#0f172a' }}>{loc.estimatedFuelMT} MT</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '11px',
                        fontWeight: 800,
                        color: loc.status === 'Recommended' ? '#0d9488' : loc.status === 'Caution' ? '#ea580c' : '#dc2626'
                      }}>
                        {loc.status === 'Recommended' && <CheckCircle2 size={13} />}
                        {loc.status === 'Caution' && <AlertCircle size={13} />}
                        {loc.status === 'Unfavorable' && <XCircle size={13} />}
                        {loc.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deep Dive & Comparative ECharts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '12px' }}>

        {/* Probability & SIC Comparison Chart */}
        <div className="ws-panel" style={{ padding: '14px 16px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <TrendingUp size={15} color="#2563eb" />
            <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
              COMPARATIVE ACCESSIBILITY PROBABILITIES & ICE CONCENTRATION
            </h3>
          </div>
          <div style={{ width: '100%', height: '240px' }}>
            <ReactECharts option={comparisonChartOption} style={{ width: '100%', height: '100%' }} />
          </div>
        </div>

        {/* Selected Station Deep Dive Details */}
        <div className="ws-panel" style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Selected Operating Station</span>
              <h4 style={{ fontSize: '14px', fontWeight: 800, color: '#2563eb', marginTop: '2px', fontFamily: 'var(--font-mono)', margin: 0 }}>
                {selectedLoc.name.toUpperCase()}
              </h4>
            </div>
            <span style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '3px 8px',
              borderRadius: '0px',
              background: 'rgba(255, 255, 255, 0.85)',
              color: '#0f172a',
              border: '1px solid rgba(191, 219, 254, 0.85)',
              fontFamily: 'var(--font-mono)'
            }}>
              {selectedLoc.coords[1]}°S, {selectedLoc.coords[0]}°E
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)', borderRadius: '0px' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', fontWeight: 700, textTransform: 'uppercase' }}>Optimal Arrival Window</span>
              <div style={{ fontSize: '13.5px', fontWeight: 800, color: '#0d9488', marginTop: '3px', fontFamily: 'var(--font-mono)' }}>
                {selectedLoc.operatingWindow}
              </div>
            </div>
            <div style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)', borderRadius: '0px' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-mono)', fontWeight: 700, textTransform: 'uppercase' }}>Weather Severity Score</span>
              <div style={{ fontSize: '13.5px', fontWeight: 800, color: '#ea580c', marginTop: '3px', fontFamily: 'var(--font-mono)' }}>
                {selectedLoc.weatherExposureScore} / 100
              </div>
            </div>
          </div>

          <div style={{ fontSize: '11.5px', color: '#1e293b', lineHeight: '1.5', background: 'rgba(255, 255, 255, 0.85)', padding: '10px 12px', border: '1px solid rgba(191, 219, 254, 0.85)', borderRadius: '0px', fontFamily: 'var(--font-mono)' }}>
            <strong style={{ color: '#0f172a', fontWeight: 800 }}>MISSION RECOMMENDATION:</strong> {selectedLoc.id === 'bharati'
              ? 'Bharati Station in Larsemann Hills provides the most favorable early-season ice breakout in Prydz Bay. Staging arrival between 10 Dec and 05 Jan minimizes fast-ice cutting requirements.'
              : selectedLoc.id === 'maitri'
                ? 'Maitri Station via Lazarev Sea approaches experiences persistent heavy pack ice through December. Delayed staging in late January is strongly advised for non-icebreaking vessels.'
                : 'Auxiliary scientific landing site suitable for short helicopter resupply and coastal glaciological surveys.'}
          </div>
        </div>

      </div>

    </div>
  );
};
