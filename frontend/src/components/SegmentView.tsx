import React from 'react';
import type { SegmentOverview, SegmentHistoryItem } from '../api/client';

interface SegmentViewProps {
  overviewList: SegmentOverview[];
  selectedSegment: string;
  onSelectSegment: (segment: string) => void;
  segmentHistory: SegmentHistoryItem[];
  chartLoading: boolean;
}

export const SegmentView: React.FC<SegmentViewProps> = ({
  overviewList,
  selectedSegment,
  onSelectSegment,
  segmentHistory,
  chartLoading,
}) => {
  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(val);

  // SVG Chart Dimensions
  const svgWidth = 760;
  const svgHeight = 260;
  const paddingX = 65;
  const paddingY = 40;

  const getChartCoordinates = () => {
    if (!segmentHistory || segmentHistory.length === 0) {
      return { path: '', areaPath: '', points: [], minVal: 0, maxVal: 1000 };
    }

    const values = segmentHistory.map((item) => item.total_spent);
    const maxVal = Math.max(...values, 1) * 1.1;
    const minVal = Math.max(0, Math.min(...values, 0) * 0.9);

    const points = segmentHistory.map((item, idx) => {
      const x =
        paddingX +
        (idx / Math.max(segmentHistory.length - 1, 1)) * (svgWidth - 2 * paddingX);
      const denominator = maxVal - minVal || 1;
      const y =
        svgHeight -
        paddingY -
        ((item.total_spent - minVal) / denominator) * (svgHeight - 2 * paddingY);
      return { x, y, item, idx };
    });

    const path = points.reduce((acc, pt, idx) => {
      return idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`;
    }, '');

    const areaPath =
      points.length > 0
        ? `${path} L ${points[points.length - 1].x} ${svgHeight - paddingY} L ${points[0].x} ${
            svgHeight - paddingY
          } Z`
        : '';

    return { path, areaPath, points, minVal, maxVal };
  };

  const { path, areaPath, points, minVal, maxVal } = getChartCoordinates();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 3 Demographic Segment Cards */}
      <div className="segment-cards-row">
        {overviewList.map((seg) => {
          const isSelected = seg.segment.toLowerCase() === selectedSegment.toLowerCase();
          return (
            <div
              key={seg.segment}
              className={`glass-card ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectSegment(seg.segment)}
              style={{
                cursor: 'pointer',
                border: isSelected
                  ? '2px solid var(--accent-indigo)'
                  : '1px solid var(--border-color)',
                boxShadow: isSelected ? '0 0 20px rgba(99, 102, 241, 0.25)' : undefined,
                position: 'relative',
              }}
            >
              {isSelected && (
                <span
                  style={{
                    position: 'absolute',
                    top: '0.75rem',
                    right: '0.75rem',
                    background: 'var(--accent-indigo)',
                    color: 'white',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    padding: '0.15rem 0.45rem',
                    borderRadius: '9999px',
                  }}
                >
                  ACTIVE
                </span>
              )}
              <div style={{ marginBottom: '1rem' }}>
                <span
                  style={{
                    fontSize: '0.8rem',
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Demographic Cohort
                </span>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 700, marginTop: '0.15rem' }}>
                  {seg.segment} Cohort
                </h3>
              </div>

              <div>
                <div className="segment-metric-item">
                  <span style={{ color: 'var(--text-secondary)' }}>Total Expenditure</span>
                  <span style={{ fontWeight: 700, color: 'var(--accent-teal)' }}>
                    {formatCurrency(seg.total_spend)}
                  </span>
                </div>
                <div className="segment-metric-item">
                  <span style={{ color: 'var(--text-secondary)' }}>Avg Ticket Size</span>
                  <span style={{ fontWeight: 600 }}>${seg.avg_amount.toFixed(2)}</span>
                </div>
                <div className="segment-metric-item">
                  <span style={{ color: 'var(--text-secondary)' }}>Cohort Avg Age</span>
                  <span style={{ fontWeight: 600 }}>{seg.avg_age} yrs</span>
                </div>
                <div className="segment-metric-item">
                  <span style={{ color: 'var(--text-secondary)' }}>Total Transactions</span>
                  <span style={{ fontWeight: 600 }}>{seg.txn_count.toLocaleString()}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Historical Spend Trend Curve for Selected Cohort */}
      <div className="glass-card">
        <div className="chart-card-header">
          <div className="chart-title">
            <h2>{selectedSegment} Cohort Historical Trajectory</h2>
            <p>Monthly aggregate spend curve and variance across evaluation cycles</p>
          </div>
          <div className="segment-selector">
            {['Young', 'Mid', 'Senior'].map((seg) => (
              <button
                key={seg}
                className={`segment-tab ${
                  selectedSegment.toLowerCase() === seg.toLowerCase() ? 'active' : ''
                }`}
                onClick={() => onSelectSegment(seg)}
              >
                {seg}
              </button>
            ))}
          </div>
        </div>

        {chartLoading ? (
          <div className="loading-overlay">
            <div className="main-spinner"></div>
            <span>Evaluating segment telemetry...</span>
          </div>
        ) : segmentHistory.length === 0 ? (
          <div className="empty-state">No historical telemetry for this segment.</div>
        ) : (
          <div className="chart-container">
            <svg className="chart-svg" viewBox={`0 0 ${svgWidth} ${svgHeight}`}>
              <defs>
                <linearGradient id="chart-gradient-seg" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="var(--accent-indigo)" />
                  <stop offset="100%" stopColor="var(--accent-teal)" />
                </linearGradient>
                <linearGradient id="area-gradient-seg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent-indigo)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="var(--accent-indigo)" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Horizontal Gridlines */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
                const y = paddingY + ratio * (svgHeight - 2 * paddingY);
                const gridVal = maxVal - ratio * (maxVal - minVal);
                return (
                  <g key={idx}>
                    <line
                      x1={paddingX}
                      y1={y}
                      x2={svgWidth - paddingX}
                      y2={y}
                      className="grid-line"
                    />
                    <text
                      x={paddingX - 10}
                      y={y + 3}
                      className="chart-axis-text"
                      textAnchor="end"
                    >
                      {formatCurrency(gridVal)}
                    </text>
                  </g>
                );
              })}

              {/* Area & Line */}
              <path d={areaPath} fill="url(#area-gradient-seg)" opacity="0.3" />
              <path
                d={path}
                fill="none"
                stroke="url(#chart-gradient-seg)"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="drop-shadow(0px 8px 12px rgba(99, 102, 241, 0.25))"
              />

              {/* Points */}
              {points.map((pt) => (
                <g key={pt.idx}>
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r={5}
                    className="chart-point"
                  />
                  <text
                    x={pt.x}
                    y={svgHeight - paddingY + 18}
                    className="chart-axis-text"
                    textAnchor="middle"
                  >
                    {pt.item.month ? pt.item.month.slice(5) : ''}
                  </text>
                </g>
              ))}
            </svg>
          </div>
        )}
      </div>
    </div>
  );
};
