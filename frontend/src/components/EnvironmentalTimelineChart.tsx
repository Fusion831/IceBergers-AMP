import React from 'react';
import ReactECharts from 'echarts-for-react';

interface EnvironmentalTimelineChartProps {
  station: 'Bharati' | 'Maitri';
}

export const EnvironmentalTimelineChart: React.FC<EnvironmentalTimelineChartProps> = ({ station }) => {
  const horizons = ['Now', '+1d', '+3d', '+7d', '+14d', '+30d', '+60d', '+90d'];

  // Forecast data with confidence envelope
  const medianSIC = station === 'Bharati'
    ? [28, 30, 34, 42, 51, 63, 72, 79]
    : [45, 48, 52, 60, 68, 77, 85, 89];

  const lowerBoundSIC = medianSIC.map(v => Math.max(0, v - (v * 0.2)));
  const upperBoundSIC = medianSIC.map(v => Math.min(100, v + (v * 0.25)));
  const icebergsDetected = station === 'Bharati' ? [2, 3, 5, 8, 12, 18, 25, 31] : [6, 7, 10, 15, 22, 29, 38, 44];

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      textStyle: { color: '#0f172a', fontSize: 11.5, fontFamily: 'var(--font-mono)' },
      formatter: function (params: any) {
        let res = `<strong style="color: #2563eb">${params[0].axisValue} Horizon</strong><br/>`;
        params.forEach((item: any) => {
          if (item.seriesName !== 'P10 Lower Bound') {
            res += `<span style="color: ${item.color};">■</span> ${item.seriesName}: <strong>${item.value}${item.seriesName.includes('SIC') ? '%' : ''}</strong><br/>`;
          }
        });
        return res;
      }
    },
    legend: {
      data: ['Median Forecast SIC', '90% Uncertainty Envelope', 'Iceberg Density Index'],
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
      data: horizons,
      axisLine: { lineStyle: { color: '#94a3b8', width: 1.2 } },
      axisTick: { lineStyle: { color: '#94a3b8' } },
      axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Sea Ice Conc (%)',
        nameTextStyle: { color: '#1e3a8a', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
        axisLabel: { color: '#1e293b', fontSize: 10.5, formatter: '{value}%', fontFamily: 'var(--font-mono)' }
      },
      {
        type: 'value',
        name: 'Iceberg Index',
        nameTextStyle: { color: '#ea580c', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
        position: 'right',
        splitLine: { show: false },
        axisLabel: { color: '#1e293b', fontSize: 10.5, fontFamily: 'var(--font-mono)' }
      }
    ],
    series: [
      {
        name: 'P10 Lower Bound',
        type: 'line',
        data: lowerBoundSIC,
        lineStyle: { opacity: 0 },
        stack: 'confidence-band',
        symbol: 'none'
      },
      {
        name: '90% Uncertainty Envelope',
        type: 'line',
        data: upperBoundSIC.map((val, idx) => val - lowerBoundSIC[idx]),
        lineStyle: { opacity: 0 },
        areaStyle: {
          color: 'rgba(30, 58, 138, 0.18)'
        },
        stack: 'confidence-band',
        symbol: 'none'
      },
      {
        name: 'Median Forecast SIC',
        type: 'line',
        data: medianSIC,
        smooth: false,
        lineStyle: { width: 2, color: '#1e3a8a' },
        itemStyle: { color: '#1e3a8a' },
        symbol: 'rect',
        symbolSize: 4
      },
      {
        name: 'Iceberg Density Index',
        type: 'bar',
        yAxisIndex: 1,
        data: icebergsDetected,
        itemStyle: {
          color: '#ea580c',
          borderRadius: 0
        },
        barWidth: '22%'
      }
    ]
  };

  return (
    <div style={{ width: '100%', height: '240px' }}>
      <ReactECharts option={option} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
