import React from 'react';
import ReactECharts from 'echarts-for-react';

export const RouteRadarChart: React.FC = () => {
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#ffffff',
      borderColor: '#bfdbfe',
      borderWidth: 1.5,
      textStyle: { color: '#0f172a', fontSize: 11.5, fontFamily: 'var(--font-mono)', fontWeight: 600 }
    },
    legend: {
      data: ['Balanced (Recommended)', 'Safest', 'Fastest'],
      textStyle: { color: '#172554', fontSize: 10.5, fontFamily: 'var(--font-mono)', fontWeight: 700 },
      bottom: 0,
      itemWidth: 10,
      itemHeight: 6
    },
    radar: {
      indicator: [
        { name: 'Safety Score', max: 100 },
        { name: 'Fuel Efficiency', max: 100 },
        { name: 'Transit Speed', max: 100 },
        { name: 'Low Ice Exposure', max: 100 },
        { name: 'Iceberg Clearance', max: 100 },
        { name: 'Weather Robustness', max: 100 }
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#172554',
        fontSize: 10.5,
        fontFamily: 'var(--font-mono)',
        fontWeight: 700
      },
      splitLine: {
        lineStyle: {
          color: '#bfdbfe',
          width: 1
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['#ffffff', '#f0f7ff', '#e0f2fe', '#dbeafe']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#93c5fd',
          width: 1.2
        }
      }
    },
    series: [
      {
        name: 'Route Tradeoffs',
        type: 'radar',
        data: [
          {
            value: [88, 85, 82, 86, 90, 84],
            name: 'Balanced (Recommended)',
            itemStyle: { color: '#0d9488' },
            lineStyle: { width: 2, color: '#0d9488' },
            areaStyle: { color: 'rgba(13, 148, 136, 0.25)' }
          },
          {
            value: [96, 70, 65, 95, 96, 90],
            name: 'Safest',
            itemStyle: { color: '#1e3a8a' },
            lineStyle: { width: 2, color: '#1e3a8a' },
            areaStyle: { color: 'rgba(30, 58, 138, 0.25)' }
          },
          {
            value: [60, 65, 96, 55, 62, 70],
            name: 'Fastest',
            itemStyle: { color: '#ea580c' },
            lineStyle: { width: 2, color: '#ea580c' },
            areaStyle: { color: 'rgba(234, 88, 12, 0.25)' }
          }
        ]
      }
    ]
  };

  return (
    <div style={{ width: '100%', height: '220px' }}>
      <ReactECharts option={option} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
