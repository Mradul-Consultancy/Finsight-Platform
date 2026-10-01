import React from 'react';
import type { Anomaly } from '../api/client';

interface RiskViewProps {
  trends: Anomaly[];
  onSelectSegment: (segment: string) => void;
}

export const RiskView: React.FC<RiskViewProps> = ({ trends, onSelectSegment }) => {
  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(val);

  // Group or sort anomalies: flagged first, then descending absolute z-score
  const sortedAnomalies = [...trends].sort((a, b) => {
    if (a.flag && !b.flag) return -1;
    if (!a.flag && b.flag) return 1;
    return Math.abs(b.z_score) - Math.abs(a.z_score);
  });

  const flaggedCount = trends.filter((t) => t.flag).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Alert Header Banner if anomalies found */}
      {flaggedCount > 0 ? (
        <div className="alert-banner">
          <div className="alert-content">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div>
              <div className="alert-title" style={{ fontSize: '1rem' }}>
                {flaggedCount} Statistical Outlier{flaggedCount > 1 ? 's' : ''} Flagged by Surveillance Engine
              </div>
              <div className="alert-desc">
                High z-score variance (|z| &gt; 2.0) detected across segment spending historical norms.
              </div>
            </div>
          </div>
          <span className="badge-risk" style={{ fontSize: '0.85rem', padding: '0.35rem 0.75rem' }}>
            Action Required
          </span>
        </div>
      ) : (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: '0.75rem',
            padding: '1rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            color: '#34d399',
          }}
        >
          <span>✓</span>
          <div>
            <div style={{ fontWeight: 600 }}>All segment operations within standard tolerances</div>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
              No critical z-score violations observed across active evaluation cycles.
            </div>
          </div>
        </div>
      )}

      {/* Anomaly Table */}
      <div className="glass-card">
        <div className="chart-card-header">
          <div className="chart-title">
            <h2>Segment Spend Variance & Z-Score Telemetry</h2>
            <p>Mathematical deviation from rolling baseline mean (μ ± 2σ)</p>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="sleek-table">
            <thead>
              <tr>
                <th>Evaluation Cycle</th>
                <th>Target Segment</th>
                <th className="text-right">Observed Spend</th>
                <th className="text-right">Z-Score Deviation</th>
                <th>Surveillance Status</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {sortedAnomalies.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}>
                    No telemetry records available.
                  </td>
                </tr>
              ) : (
                sortedAnomalies.map((item, idx) => {
                  const isSevere = item.flag || Math.abs(item.z_score) >= 2.0;
                  const isModerate = Math.abs(item.z_score) >= 1.0;

                  return (
                    <tr
                      key={`${item.month}-${item.segment}-${idx}`}
                      style={{
                        background: item.flag ? 'rgba(244, 63, 94, 0.04)' : undefined,
                      }}
                    >
                      <td className="font-mono" style={{ fontWeight: 600 }}>
                        {item.month}
                      </td>
                      <td>
                        <span className="badge-segment">{item.segment}</span>
                      </td>
                      <td className="text-right font-mono" style={{ fontWeight: 600 }}>
                        {formatCurrency(item.total_spent)}
                      </td>
                      <td className="text-right font-mono">
                        <span
                          style={{
                            fontWeight: 700,
                            color: isSevere
                              ? 'var(--accent-rose)'
                              : isModerate
                              ? 'var(--accent-amber)'
                              : '#34d399',
                          }}
                        >
                          {item.z_score > 0 ? `+${item.z_score.toFixed(2)}` : item.z_score.toFixed(2)}σ
                        </span>
                      </td>
                      <td>
                        {item.flag ? (
                          <span className="badge-risk">CRITICAL FLAG</span>
                        ) : isModerate ? (
                          <span
                            style={{
                              background: 'rgba(245, 158, 11, 0.1)',
                              border: '1px solid rgba(245, 158, 11, 0.25)',
                              color: 'var(--accent-amber)',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              padding: '0.2rem 0.5rem',
                              borderRadius: '0.25rem',
                            }}
                          >
                            MONITOR
                          </span>
                        ) : (
                          <span
                            style={{
                              background: 'rgba(16, 185, 129, 0.1)',
                              border: '1px solid rgba(16, 185, 129, 0.25)',
                              color: '#34d399',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              padding: '0.2rem 0.5rem',
                              borderRadius: '0.25rem',
                            }}
                          >
                            NORMAL
                          </span>
                        )}
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => onSelectSegment(item.segment)}
                          style={{
                            background: 'transparent',
                            border: '1px solid var(--border-color)',
                            color: 'var(--accent-indigo)',
                            padding: '0.25rem 0.65rem',
                            borderRadius: '0.35rem',
                            fontSize: '0.775rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Inspect →
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
