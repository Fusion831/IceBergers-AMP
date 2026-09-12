import React, { useState } from 'react';
import { useMission } from '../context/MissionContext';
import { EnvironmentalTimelineChart } from '../components/EnvironmentalTimelineChart';
import ReactECharts from 'echarts-for-react';
import {
  TrendingUp,
  Clock,
  Wind,
  AlertTriangle,
  Cpu
} from 'lucide-react';

export const EnvironmentalTimelineView: React.FC = () => {
  const { timeHorizon, setTimeHorizon } = useMission();
  const [selectedStation, setSelectedStation] = useState<'Bharati' | 'Maitri'>('Bharati');

  const horizons = ['Now', '+1d', '+3d', '+7d', '+14d', '+30d', '+60d', '+90d'] as const;

  // Wave & Wind ECharts Options - Light Blue & White Theme
  const marineWeatherOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      textStyle: { color: '#0f172a', fontSize: 11.5, fontFamily: 'var(--font-mono)' }
    },
    legend: {
      data: ['Sustained Wind (knots)', 'Peak Wave Height (meters)', 'Gale Probability (%)'],
      textStyle: { color: '#172554', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
      top: 0,
      right: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '8%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['Now', '+1d', '+3d', '+7d', '+14d', '+30d', '+60d', '+90d'],
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Wind (kts) / Wave (m)',
        nameTextStyle: { color: '#172554', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
        splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
        axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)' }
      },
      {
        type: 'value',
        name: 'Gale Prob (%)',
        nameTextStyle: { color: '#dc2626', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
        min: 0,
        max: 100,
        position: 'right',
        splitLine: { show: false },
        axisLabel: { color: '#1e293b', fontSize: 10.5, formatter: '{value}%', fontFamily: 'var(--font-mono)' }
      }
    ],
    series: [
      {
        name: 'Sustained Wind (knots)',
        type: 'line',
        data: selectedStation === 'Bharati' ? [14, 18, 22, 28, 24, 20, 26, 30] : [22, 26, 32, 40, 35, 30, 38, 42],
        smooth: false,
        lineStyle: { width: 2, color: '#ea580c' },
        itemStyle: { color: '#ea580c' },
        symbol: 'rect',
        symbolSize: 4
      },
      {
        name: 'Peak Wave Height (meters)',
        type: 'line',
        data: selectedStation === 'Bharati' ? [1.5, 2.0, 2.8, 3.4, 2.9, 2.2, 3.1, 3.6] : [2.8, 3.5, 4.4, 5.8, 4.6, 3.8, 5.0, 5.5],
        smooth: false,
        lineStyle: { width: 2, color: '#0d9488' },
        itemStyle: { color: '#0d9488' },
        symbol: 'triangle',
        symbolSize: 4
      },
      {
        name: 'Gale Probability (%)',
        type: 'bar',
        yAxisIndex: 1,
        data: selectedStation === 'Bharati' ? [5, 12, 22, 38, 30, 20, 34, 45] : [20, 35, 52, 74, 62, 48, 68, 78],
        itemStyle: {
          color: 'rgba(220, 38, 38, 0.75)',
          borderRadius: 0
        },
        barWidth: '20%'
      }
    ]
  };

  const isExtendedHorizon = timeHorizon === '+30d' || timeHorizon === '+60d' || timeHorizon === '+90d';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%', overflowY: 'auto', padding: '4px' }}>

      {/* Top Banner */}
      <div className="ws-panel" style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(240, 248, 255, 0.65)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '10.5px', fontWeight: 800, padding: '2px 7px', borderRadius: '0px', background: 'rgba(239, 246, 255, 0.85)', color: '#2563eb', border: '1px solid #93c5fd', fontFamily: 'var(--font-mono)' }}>
              CORE VIEW 3 OF 6
            </span>
            <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '14.5px', fontWeight: 800, color: '#172554', margin: 0 }}>
              SPATIOTEMPORAL ENVIRONMENTAL TIMELINE & UNCERTAINTY ENVELOPES (PRD §63)
            </h2>
          </div>
          <p style={{ fontSize: '11.5px', color: '#475569', marginTop: '4px', fontFamily: 'var(--font-mono)', margin: 0 }}>
            Multi-horizon forecast modeling: ConvLSTM predictions (Now to +14d) transitioning into seasonal probability climatology (+30d to +90d).
          </p>
        </div>

        {/* Station Toggle */}
        <div style={{ display: 'flex', gap: '6px', background: 'rgba(224, 242, 254, 0.75)', padding: '4px', borderRadius: '0px', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
          {(['Bharati', 'Maitri'] as const).map((st) => {
            const isActive = selectedStation === st;
            return (
              <button
                key={st}
                onClick={() => setSelectedStation(st)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '0px',
                  fontSize: '11.5px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: isActive ? 800 : 600,
                  border: '1px solid',
                  borderColor: isActive ? '#1d4ed8' : 'rgba(191, 219, 254, 0.85)',
                  borderBottom: isActive ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                  background: isActive ? '#2563eb' : 'rgba(255, 255, 255, 0.85)',
                  color: isActive ? '#ffffff' : '#1e293b',
                  cursor: 'pointer',
                  boxShadow: isActive ? 'inset 0 1px 0 rgba(255,255,255,0.35), 0 3px 0 #1e3a8a' : 'inset 0 1px 0 rgba(255,255,255,0.7), 0 3px 0 #93c5fd'
                }}
              >
                {st.toUpperCase()} SECTOR
              </button>
            );
          })}
        </div>
      </div>

      {/* Horizon-Specific Capability Alert (PRD Section 63) */}
      {isExtendedHorizon ? (
        <div style={{
          padding: '10px 14px',
          borderRadius: '0px',
          background: 'rgba(255, 247, 237, 0.85)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          border: '1px solid #ea580c',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#ea580c',
          fontFamily: 'var(--font-mono)'
        }}>
          <AlertTriangle size={16} color="#ea580c" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '11.5px', lineHeight: '1.5', color: '#0f172a' }}>
            <strong style={{ color: '#ea580c' }}>PRD §63 HORIZON PRINCIPLE:</strong> Deterministic forecast is not physically valid at <strong>{timeHorizon}</strong> lead. Displaying <strong>Seasonal Probability Climatology & Ensemble Range</strong>.
          </div>
        </div>
      ) : (
        <div style={{
          padding: '10px 14px',
          borderRadius: '0px',
          background: 'rgba(240, 253, 250, 0.85)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          border: '1px solid #0d9488',
          borderLeft: '4px solid #0d9488',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#0f172a',
          fontFamily: 'var(--font-mono)'
        }}>
          <Cpu size={16} color="#0d9488" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '11.5px', lineHeight: '1.5' }}>
            <strong style={{ color: '#0d9488' }}>ACTIVE AI MODEL:</strong> High-resolution Spatiotemporal ConvLSTM + Ocean Current Advection active for <strong>{timeHorizon}</strong> lead horizon.
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

        {/* Sea Ice Concentration & Uncertainty Chart */}
        <div className="ws-panel" style={{ padding: '14px 16px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <TrendingUp size={15} color="#2563eb" />
            <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
              SEA-ICE CONCENTRATION (SIC %) & P10–P90 UNCERTAINTY ENVELOPE
            </h3>
          </div>
          <p style={{ fontSize: '11px', color: '#475569', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>
            Dark blue envelope depicts 90% uncertainty spread across ensemble runs for {selectedStation} sector.
          </p>
          <EnvironmentalTimelineChart station={selectedStation} />
        </div>

        {/* Marine Meteorology & Wavewatch Chart */}
        <div className="ws-panel" style={{ padding: '14px 16px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Wind size={15} color="#2563eb" />
            <h3 style={{ fontSize: '12.5px', fontWeight: 800, color: '#172554', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
              MARINE WINDS, SWELL HEIGHTS & GALE PROBABILITIES
            </h3>
          </div>
          <p style={{ fontSize: '11px', color: '#475569', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>
            WaveWatch III ocean swell forcing and ERA5 surface wind hazards across approach corridor.
          </p>
          <div style={{ width: '100%', height: '240px' }}>
            <ReactECharts option={marineWeatherOption} style={{ width: '100%', height: '100%' }} />
          </div>
        </div>

      </div>

      {/* Horizon Controller Quick Bar */}
      <div className="ws-panel" style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(240, 248, 255, 0.75)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={15} color="#2563eb" />
          <span style={{ fontSize: '11.5px', fontWeight: 800, color: '#172554', fontFamily: 'var(--font-mono)' }}>
            ACTIVE TIMELINE HORIZON STEPPER:
          </span>
        </div>

        <div style={{ display: 'flex', gap: '5px' }}>
          {horizons.map((hz) => {
            const isActive = timeHorizon === hz;
            return (
              <button
                key={hz}
                onClick={() => setTimeHorizon(hz)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '0px',
                  fontSize: '11.5px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: isActive ? 800 : 600,
                  border: '1px solid',
                  borderColor: isActive ? '#1d4ed8' : '#bfdbfe',
                  borderBottom: isActive ? '3px solid #1e3a8a' : '3px solid #93c5fd',
                  background: isActive ? '#2563eb' : 'rgba(255, 255, 255, 0.85)',
                  color: isActive ? '#ffffff' : '#1e293b',
                  cursor: 'pointer',
                  boxShadow: isActive ? 'inset 0 1px 0 rgba(255,255,255,0.35), 0 3px 0 #1e3a8a' : 'inset 0 1px 0 rgba(255,255,255,0.7), 0 3px 0 #93c5fd'
                }}
              >
                {hz}
              </button>
            );
          })}
        </div>
      </div>

    </div>
  );
};
