import React from 'react';
import { useMission } from '../context/MissionContext';
import ReactECharts from 'echarts-for-react';
import {
  Crosshair,
  Cpu,
  Layers,
  ShieldCheck,
  BarChart2,
  Database,
  Calendar,
  Tag
} from 'lucide-react';

export const PredictionInspectorView: React.FC = () => {
  const { inspectionPoint, timeHorizon } = useMission();

  // Ensemble Spreads & Quantiles ECharts (PRD Section 66) - Light Blue Theme
  const ensembleQuantileOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      padding: [6, 10],
      textStyle: { color: '#0f172a', fontSize: 11.5, fontFamily: 'var(--font-mono)' }
    },
    legend: {
      data: ['P50 Ensemble Median', '90% Quantile Envelope [P10-P90]', 'Ensemble Spread (σ)'],
      textStyle: { color: '#172554', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
      top: 0,
      right: 0,
      itemWidth: 10,
      itemHeight: 6
    },
    grid: {
      left: '2%',
      right: '2%',
      bottom: '6%',
      top: '16%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['T+0', 'T+24H', 'T+72H', 'T+168H', 'T+336H', 'T+30D', 'T+60D', 'T+90D'],
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'SIC (%)',
        nameTextStyle: { color: '#172554', fontSize: 10.5, align: 'left', fontFamily: 'var(--font-mono)', fontWeight: 700 },
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
        axisLabel: { color: '#1e293b', fontSize: 10.5, formatter: '{value}%', fontFamily: 'var(--font-mono)' }
      },
      {
        type: 'value',
        name: 'Spread σ (%)',
        nameTextStyle: { color: '#ea580c', fontSize: 10.5, align: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700 },
        position: 'right',
        splitLine: { show: false },
        axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)' }
      }
    ],
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
        symbolSize: 4
      },
      {
        name: 'Ensemble Spread (σ)',
        type: 'bar',
        yAxisIndex: 1,
        data: [2.1, 2.8, 3.9, 5.2, 7.8, 11.4, 14.8, 18.2],
        itemStyle: {
          color: 'rgba(234, 88, 12, 0.45)',
          borderRadius: 0
        },
        barWidth: '16%'
      }
    ]
  };

  // Waterfall/Bar Chart for Feature Attribution (SHAP / Integrated Gradients representation)
  const attributionChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      padding: [6, 10],
      textStyle: { color: '#0f172a', fontSize: 11.5, fontFamily: 'var(--font-mono)' },
      formatter: '{b}: <strong>{c}%</strong> attribution weight'
    },
    grid: {
      left: '2%',
      right: '6%',
      bottom: '4%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: 'Weight (%)',
      nameTextStyle: { color: '#172554', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)' }
    },
    yAxis: {
      type: 'category',
      data: inspectionPoint.featureAttributions.map((f) => f.feature),
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 600 }
    },
    series: [
      {
        name: 'Contribution',
        type: 'bar',
        data: inspectionPoint.featureAttributions.map((f) => ({
          value: f.contributionPct,
          itemStyle: {
            color: f.impact === 'positive' ? '#0d9488' : f.impact === 'negative' ? '#dc2626' : '#64748b',
            borderRadius: 0
          }
        })),
        barWidth: '40%'
      }
    ]
  };

  // Baseline Comparison Chart (PRD Section 70)
  const baselineChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      padding: [6, 10],
      textStyle: { color: '#0f172a', fontSize: 11.5, fontFamily: 'var(--font-mono)' }
    },
    legend: {
      data: ['AMIP Hybrid AI (Ours)', 'Persistence Baseline', 'Climatology Baseline', 'Ice-kNN Analog'],
      textStyle: { color: '#172554', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
      top: 0,
      right: 0,
      itemWidth: 10,
      itemHeight: 6
    },
    grid: {
      left: '2%',
      right: '2%',
      bottom: '6%',
      top: '16%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['MAE (SIC %)', 'RMSE (%)', 'Edge Err (km)', 'Brier (x100)'],
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)' }
    },
    series: [
      {
        name: 'AMIP Hybrid AI (Ours)',
        type: 'bar',
        data: [4.2, 6.8, 14.5, 8.2],
        itemStyle: { color: '#0d9488', borderRadius: 0 },
        barWidth: '16%'
      },
      {
        name: 'Persistence Baseline',
        type: 'bar',
        data: [11.5, 16.4, 42.0, 24.5],
        itemStyle: { color: '#94a3b8', borderRadius: 0 },
        barWidth: '16%'
      },
      {
        name: 'Climatology Baseline',
        type: 'bar',
        data: [14.2, 19.8, 55.0, 31.0],
        itemStyle: { color: '#ea580c', borderRadius: 0 },
        barWidth: '16%'
      },
      {
        name: 'Ice-kNN Analog',
        type: 'bar',
        data: [8.6, 12.1, 28.0, 16.4],
        itemStyle: { color: '#2563eb', borderRadius: 0 },
        barWidth: '16%'
      }
    ]
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%', overflowY: 'auto', padding: '4px' }}>
      
      {/* Workstation Console Header */}
      <div className="ws-panel" style={{ padding: '12px 16px', background: 'rgba(240, 248, 255, 0.65)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '10.5px', fontWeight: 800, padding: '2px 7px', borderRadius: '0px', background: 'rgba(239, 246, 255, 0.85)', color: '#2563eb', border: '1px solid #93c5fd', fontFamily: 'var(--font-mono)' }}>
                CORE VIEW 6 OF 6
              </span>
              <h2 style={{ fontSize: '14.5px', fontWeight: 800, color: '#172554', letterSpacing: '0.04em', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: 0 }}>
                PREDICTION INSPECTOR & CRYOSPHERIC MODEL DIAGNOSTICS (PRD §66 & §70)
              </h2>
            </div>
            <div style={{ fontSize: '11.5px', color: '#475569', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
              NCPOR/OP-26059 // SHAP ATTRIBUTION ENGINE // RESIDUAL DECOMPOSITION // EPSG:3031
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 14px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid rgba(191, 219, 254, 0.85)', borderRadius: '0px' }}>
            <Crosshair size={15} color="#2563eb" />
            <span style={{ fontSize: '11.5px', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#2563eb' }}>
              GRID CELL: {inspectionPoint.lat}°S, {inspectionPoint.lon}°E (HORIZON: {timeHorizon})
            </span>
          </div>
        </div>
      </div>

      {/* Data Provenance Metadata Tags Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
        <div className="ws-card" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(10px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <Database size={16} color="#2563eb" />
          <div>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>DATA PROVENANCE</div>
            <div style={{ fontSize: '12px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0f172a', marginTop: '2px' }}>
              [Source: Copernicus Sentinel-1]
            </div>
          </div>
        </div>

        <div className="ws-card" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(10px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <Calendar size={16} color="#0d9488" />
          <div>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>VALID FORECAST TIMESTAMP</div>
            <div style={{ fontSize: '12px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0d9488', marginTop: '2px' }}>
              2026-12-15 00:00 UTC (T+{timeHorizon})
            </div>
          </div>
        </div>

        <div className="ws-card" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(10px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <Tag size={16} color="#2563eb" />
          <div>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>OPERATIONAL MODEL VERSION</div>
            <div style={{ fontSize: '12px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#2563eb', marginTop: '2px' }}>
              [AMIP-CryoNet v2.4-S2S]
            </div>
          </div>
        </div>

        <div className="ws-card" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', background: 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(10px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <ShieldCheck size={16} color="#0d9488" />
          <div>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>CALIBRATION STATUS</div>
            <div style={{ fontSize: '12px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0d9488', marginTop: '2px' }}>
              50-Member CRPS Verified
            </div>
          </div>
        </div>
      </div>

      {/* Grid Cell Environmental Telemetry Strip */}
      <div className="ws-panel" style={{ padding: '12px 14px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div className="ws-panel-header" style={{ marginBottom: '8px', background: 'rgba(224, 242, 254, 0.75)', padding: '8px 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={15} color="#2563eb" />
            <span style={{ fontSize: '12px', fontWeight: 800 }}>GRID CELL TELEMETRY & BIOPHYSICAL STATE: {inspectionPoint.sectorName.toUpperCase()}</span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', color: '#64748b', fontSize: '10.5px' }}>2.5° × 2.5° MESH</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '8px' }}>
          <div className="ws-card" style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>P50 Forecast SIC</span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#2563eb', marginTop: '3px' }}>
              {inspectionPoint.forecastSIC}%
            </div>
            <div style={{ fontSize: '10.5px', color: '#0d9488', fontFamily: 'var(--font-mono)', fontWeight: 700, marginTop: '2px' }}>Manageable pack</div>
          </div>

          <div className="ws-card" style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Level Ice Thickness</span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0f172a', marginTop: '3px' }}>
              {inspectionPoint.iceThicknessMeters} m
            </div>
            <div style={{ fontSize: '10.5px', color: '#64748b', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>First-year level ice</div>
          </div>

          <div className="ws-card" style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Iceberg Frequency</span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#ea580c', marginTop: '3px' }}>
              {inspectionPoint.icebergCount100km2} / 100km²
            </div>
            <div style={{ fontSize: '10.5px', color: '#0d9488', fontFamily: 'var(--font-mono)', fontWeight: 700, marginTop: '2px' }}>Low collision risk</div>
          </div>

          <div className="ws-card" style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Sea Surface Temp</span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0f172a', marginTop: '3px' }}>
              {inspectionPoint.seaSurfaceTempC} °C
            </div>
            <div style={{ fontSize: '10.5px', color: '#64748b', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>OSTIA Foundation SST</div>
          </div>

          <div className="ws-card" style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>10m Surface Wind</span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0f172a', marginTop: '3px' }}>
              {inspectionPoint.windSpeedKnots} kts
            </div>
            <div style={{ fontSize: '10.5px', color: '#64748b', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>ERA5 Drift Vector</div>
          </div>

          <div className="ws-card" style={{ padding: '10px 12px', background: 'rgba(255, 255, 255, 0.80)', border: '1px solid rgba(191, 219, 254, 0.85)' }}>
            <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Model Confidence</span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0d9488', marginTop: '3px' }}>
              {inspectionPoint.modelConfidence}%
            </div>
            <div style={{ fontSize: '10.5px', color: '#0d9488', fontFamily: 'var(--font-mono)', fontWeight: 700, marginTop: '2px' }}>50-member converged</div>
          </div>
        </div>
      </div>

      {/* Ensemble Spreads & Quantiles Graph Panel */}
      <div className="ws-panel" style={{ padding: '12px 14px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.75)', padding: '8px 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart2 size={15} color="#2563eb" />
            <span style={{ fontSize: '12px', fontWeight: 800 }}>ENSEMBLE SPREAD EVOLUTION & P10-P90 QUANTILE ENVELOPE (PRD §66)</span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', color: '#64748b', fontSize: '10.5px' }}>PROBABILISTIC DENSITY FUNCTION</span>
        </div>
        <div style={{ width: '100%', height: '210px' }}>
          <ReactECharts option={ensembleQuantileOption} style={{ width: '100%', height: '100%' }} />
        </div>
      </div>

      {/* Dual Deep Diagnostics Grid: SHAP Attribution & Benchmark Baselines */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        
        {/* Feature Attribution Panel */}
        <div className="ws-panel" style={{ padding: '12px 14px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.75)', padding: '8px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={15} color="#2563eb" />
              <span style={{ fontSize: '12px', fontWeight: 800 }}>SHAP FEATURE ATTRIBUTION & FORCING WEIGHTS</span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', color: '#64748b', fontSize: '10.5px' }}>GRAD-CAM / SHAP</span>
          </div>
          <div style={{ width: '100%', height: '210px' }}>
            <ReactECharts option={attributionChartOption} style={{ width: '100%', height: '100%' }} />
          </div>
        </div>

        {/* Model Evaluation vs Baselines Panel */}
        <div className="ws-panel" style={{ padding: '12px 14px', background: 'rgba(255, 255, 255, 0.70)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
          <div className="ws-panel-header" style={{ background: 'rgba(224, 242, 254, 0.75)', padding: '8px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart2 size={15} color="#2563eb" />
              <span style={{ fontSize: '12px', fontWeight: 800 }}>COMPARATIVE BENCHMARK ERROR QUANTILES (PRD §68 & §70)</span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', color: '#64748b', fontSize: '10.5px' }}>LOWER IS BETTER</span>
          </div>
          <div style={{ width: '100%', height: '210px' }}>
            <ReactECharts option={baselineChartOption} style={{ width: '100%', height: '100%' }} />
          </div>
        </div>

      </div>

      {/* Epistemic vs Aleatoric Uncertainty Breakdown */}
      <div className="ws-panel" style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(240, 248, 255, 0.75)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', border: '1px solid rgba(191, 219, 254, 0.75)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={18} color="#0d9488" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: '12px', fontWeight: 800, color: '#172554', fontFamily: 'var(--font-mono)' }}>
              UNCERTAINTY QUANTIFICATION: ALEATORIC (ENVIRONMENTAL) VS EPISTEMIC (MODEL DEFICIENCY)
            </div>
            <div style={{ fontSize: '11px', color: '#475569', marginTop: '3px', fontFamily: 'var(--font-mono)' }}>
              Aleatoric variance (σ²={inspectionPoint.aleatoricUncertainty}) dominates model epistemic variance (σ²={inspectionPoint.epistemicUncertainty}), indicating stable neural network convergence.
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <div style={{ padding: '6px 14px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid rgba(191, 219, 254, 0.85)', borderRadius: '0px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Aleatoric σ</div>
            <div style={{ fontSize: '13.5px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0f172a', marginTop: '2px' }}>0.08</div>
          </div>
          <div style={{ padding: '6px 14px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid rgba(191, 219, 254, 0.85)', borderRadius: '0px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Epistemic σ</div>
            <div style={{ fontSize: '13.5px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#0d9488', marginTop: '2px' }}>0.04</div>
          </div>
          <div style={{ padding: '6px 14px', background: 'rgba(255, 255, 255, 0.85)', border: '1px solid rgba(191, 219, 254, 0.85)', borderRadius: '0px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>Entropy (bits)</div>
            <div style={{ fontSize: '13.5px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#ea580c', marginTop: '2px' }}>0.14</div>
          </div>
        </div>
      </div>

    </div>
  );
};
