import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import type { ChannelData, MonthlyVolume, LocationData } from '../api/client';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface OverviewChartsProps {
  monthlyVolumes: MonthlyVolume[];
  channelDistribution: ChannelData[];
  topLocations: LocationData[];
}

export const OverviewCharts: React.FC<OverviewChartsProps> = ({
  monthlyVolumes,
  channelDistribution,
  topLocations,
}) => {
  // ── Monthly Volume & Spend Dual-Axis Chart ──
  const monthLabels = monthlyVolumes.map((m) => m.month || '');
  const spendData = monthlyVolumes.map((m) => m.total_spend);
  const countData = monthlyVolumes.map((m) => m.txn_count);

  const monthlyChartData = {
    labels: monthLabels,
    datasets: [
      {
        type: 'bar' as const,
        label: 'Total Spend ($)',
        data: spendData,
        backgroundColor: 'rgba(99, 102, 241, 0.45)',
        borderColor: '#6366f1',
        borderWidth: 1.5,
        borderRadius: 4,
        yAxisID: 'ySpend',
      },
      {
        type: 'line' as const,
        label: 'Transaction Count',
        data: countData,
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14, 165, 233, 0.1)',
        borderWidth: 2.5,
        pointBackgroundColor: '#0ea5e9',
        pointBorderColor: '#ffffff',
        pointRadius: 4,
        tension: 0.35,
        yAxisID: 'yCount',
      },
    ],
  };

  const monthlyChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        labels: {
          color: '#9ca3af',
          font: { family: 'Plus Jakarta Sans', size: 12 },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        titleColor: '#f9fafb',
        bodyColor: '#e5e7eb',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#6b7280', font: { size: 11 } },
      },
      ySpend: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        grid: { color: 'rgba(255, 255, 255, 0.06)' },
        ticks: {
          color: '#818cf8',
          font: { size: 11 },
          callback: (value: any) => `$${(value / 1000).toFixed(0)}k`,
        },
      },
      yCount: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        grid: { drawOnChartArea: false },
        ticks: {
          color: '#38bdf8',
          font: { size: 11 },
        },
      },
    },
  };

  // ── Channel Donut Chart ──
  const channelColors = ['#0ea5e9', '#f59e0b', '#10b981'];
  const channelLabels = channelDistribution.map((c) => c.channel);
  const channelCounts = channelDistribution.map((c) => c.count);
  const totalChannelTxns = channelCounts.reduce((acc, v) => acc + v, 0) || 1;

  const donutData = {
    labels: channelLabels,
    datasets: [
      {
        data: channelCounts,
        backgroundColor: channelColors,
        borderColor: '#111827',
        borderWidth: 3,
        hoverOffset: 6,
      },
    ],
  };

  const donutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        titleColor: '#f9fafb',
        bodyColor: '#e5e7eb',
      },
    },
    cutout: '70%',
  };

  // Max location count for bar proportion
  const maxLocationCount = Math.max(...topLocations.map((l) => l.txn_count), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Row: Monthly Volume & Channel Distribution */}
      <div className="charts-grid-2col">
        {/* Monthly Volume & Spend Combo Chart */}
        <div className="glass-card chart-card">
          <div className="chart-card-header" style={{ marginBottom: '1rem' }}>
            <div className="chart-title">
              <h2>Monthly Spend & Transaction Volume</h2>
              <p>Combined dual-axis trajectory across all customer segments</p>
            </div>
          </div>
          <div className="chart-canvas-wrap" style={{ height: '320px' }}>
            {monthlyVolumes.length > 0 ? (
              <Bar data={monthlyChartData as any} options={monthlyChartOptions as any} />
            ) : (
              <div className="empty-state">No monthly volume data available</div>
            )}
          </div>
        </div>

        {/* Channel Distribution Donut */}
        <div className="glass-card chart-card">
          <div className="chart-card-header" style={{ marginBottom: '1rem' }}>
            <div className="chart-title">
              <h2>Channel Distribution</h2>
              <p>Transaction breakdown by channel</p>
            </div>
          </div>
          <div className="channel-donut-layout" style={{ marginTop: '0.5rem' }}>
            <div style={{ position: 'relative', width: '160px', height: '160px', flexShrink: 0 }}>
              <Doughnut data={donutData} options={donutOptions} />
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                }}
              >
                <span style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                  {totalChannelTxns.toLocaleString()}
                </span>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TXNS</div>
              </div>
            </div>

            <div className="channel-legend">
              {channelDistribution.map((ch, idx) => {
                const pct = ((ch.count / totalChannelTxns) * 100).toFixed(1);
                return (
                  <div key={ch.channel} className="channel-legend-item">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <span
                        className="channel-legend-dot"
                        style={{ backgroundColor: channelColors[idx % channelColors.length] }}
                      ></span>
                      <span style={{ fontWeight: 500, fontSize: '0.85rem' }}>{ch.channel}</span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{pct}%</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        ${ch.total_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Top Locations Ranking */}
      <div className="glass-card">
        <div className="chart-card-header" style={{ marginBottom: '1rem' }}>
          <div className="chart-title">
            <h2>Geographic Hubs & High-Density Locations</h2>
            <p>Top operational transaction hubs ranked by total transaction volume</p>
          </div>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem',
          }}
        >
          {topLocations.map((loc, idx) => {
            const pct = Math.round((loc.txn_count / maxLocationCount) * 100);
            return (
              <div
                key={loc.location}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '0.5rem',
                  padding: '0.75rem 1rem',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '0.4rem',
                    fontSize: '0.85rem',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>
                    <span style={{ color: 'var(--text-muted)', marginRight: '0.35rem' }}>
                      #{idx + 1}
                    </span>
                    {loc.location}
                  </span>
                  <span style={{ color: 'var(--accent-teal)', fontWeight: 600 }}>
                    {loc.txn_count} txns
                  </span>
                </div>
                <div className="location-bar-bg">
                  <div className="location-bar-fill" style={{ width: `${pct}%` }}></div>
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    marginTop: '0.35rem',
                  }}
                >
                  <span>Volume density</span>
                  <span>${loc.total_amount.toLocaleString()}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
