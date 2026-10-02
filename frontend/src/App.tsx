import { useEffect, useState, useRef } from 'react';
import {
  fetchKPIs,
  fetchTrends,
  fetchSegmentData,
  fetchChannelDistribution,
  fetchMonthlyVolume,
  fetchTopLocations,
  fetchSegmentOverview,
  getReportUrl,
} from './api/client';
import type {
  KPIData,
  Anomaly,
  SegmentHistoryItem,
  ChannelData,
  MonthlyVolume,
  LocationData,
  SegmentOverview,
} from './api/client';
import { OverviewCharts } from './components/OverviewCharts';
import { TransactionLedger } from './components/TransactionLedger';
import { SegmentView } from './components/SegmentView';
import { RiskView } from './components/RiskView';

export default function App() {
  // ─── Active Tab State ───
  const [activeTab, setActiveTab] = useState<'overview' | 'risk' | 'segments' | 'ledger'>(
    'overview'
  );

  // ─── Core Data State ───
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [trends, setTrends] = useState<Anomaly[]>([]);
  const [channelData, setChannelData] = useState<ChannelData[]>([]);
  const [monthlyVolume, setMonthlyVolume] = useState<MonthlyVolume[]>([]);
  const [topLocations, setTopLocations] = useState<LocationData[]>([]);
  const [segmentOverview, setSegmentOverview] = useState<SegmentOverview[]>([]);

  // ─── Segment Selection & Telemetry ───
  const [selectedSegment, setSelectedSegment] = useState<string>('Young');
  const [segmentHistory, setSegmentHistory] = useState<SegmentHistoryItem[]>([]);

  // ─── UI Status States ───
  const [loading, setLoading] = useState<boolean>(true);
  const [chartLoading, setChartLoading] = useState<boolean>(false);
  const [reportLoading, setReportLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshSpin, setRefreshSpin] = useState<boolean>(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(0); // 0 = off, 15, 30, 60
  const autoRefreshTimerRef = useRef<any>(null);

  // ─── Data Loaders ───
  const loadDashboardData = async () => {
    setError(null);
    try {
      const results = await Promise.allSettled([
        fetchKPIs(),
        fetchTrends(),
        fetchChannelDistribution(),
        fetchMonthlyVolume(),
        fetchTopLocations(),
        fetchSegmentOverview(),
      ]);

      if (results[0].status === 'fulfilled') setKpis(results[0].value);
      if (results[1].status === 'fulfilled') setTrends(results[1].value.anomalies);
      if (results[2].status === 'fulfilled') setChannelData(results[2].value.channels);
      if (results[3].status === 'fulfilled') setMonthlyVolume(results[3].value.months);
      if (results[4].status === 'fulfilled') setTopLocations(results[4].value.locations);
      if (results[5].status === 'fulfilled') setSegmentOverview(results[5].value.segments);

      // Check if ALL failed
      const allFailed = results.every((r) => r.status === 'rejected');
      if (allFailed) {
        setError(
          'Could not connect to FinSight Backend. Please verify that the server is running and database is initialized.'
        );
      }

      await loadSegmentData(selectedSegment);
    } catch (err: any) {
      console.error(err);
      setError(
        'Could not connect to FinSight Backend. Please verify that the server is running and database is initialized.'
      );
    } finally {
      setLoading(false);
    }
  };

  const loadSegmentData = async (segmentId: string) => {
    setChartLoading(true);
    try {
      const data = await fetchSegmentData(segmentId);
      setSegmentHistory(data.history);
    } catch (err) {
      console.error('Failed to load segment history', err);
      setSegmentHistory([]);
    } finally {
      setChartLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshSpin(true);
    await loadDashboardData();
    setTimeout(() => setRefreshSpin(false), 700);
  };

  const handleSelectSegment = (seg: string) => {
    setSelectedSegment(seg);
    loadSegmentData(seg);
    setActiveTab('segments');
  };

  // ─── Auto Refresh Mechanism ───
  useEffect(() => {
    if (autoRefreshTimerRef.current) {
      clearInterval(autoRefreshTimerRef.current);
      autoRefreshTimerRef.current = null;
    }

    if (autoRefreshInterval > 0) {
      autoRefreshTimerRef.current = setInterval(() => {
        loadDashboardData();
      }, autoRefreshInterval * 1000);
    }

    return () => {
      if (autoRefreshTimerRef.current) {
        clearInterval(autoRefreshTimerRef.current);
      }
    };
  }, [autoRefreshInterval, selectedSegment]);

  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, []);

  // ─── Report Generator ───
  const downloadReport = async () => {
    setReportLoading(true);
    try {
      const url = getReportUrl();
      const response = await fetch(url);
      if (!response.ok) throw new Error('Report generation failed');
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute(
        'download',
        `finsight_executive_report_${selectedSegment}_${
          new Date().toISOString().split('T')[0]
        }.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error(err);
      alert('Error generating PDF report. Please verify backend connection.');
    } finally {
      setReportLoading(false);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const flaggedAnomaliesCount = trends.filter((t) => t.flag).length;
  const totalVolumeCount = monthlyVolume.reduce((acc, m) => acc + m.txn_count, 0);

  return (
    <div className="dashboard-container">
      {/* ─── Header ─── */}
      <header className="dashboard-header">
        <div className="brand-section">
          <div className="brand-logo">FS</div>
          <div className="brand-title-group">
            <h1>FinSight Executive Intelligence</h1>
            <p>Enterprise Credit Decision Engine & Real-time Risk Surveillance</p>
          </div>
        </div>

        <div className="header-actions">
          {/* API Status Badge */}
          <div className="status-badge">
            <span className="status-dot"></span>
            <span>API Live (8002)</span>
          </div>

          {/* Auto Refresh Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Auto-sync:</span>
            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              style={{
                background: 'rgba(17, 24, 39, 0.8)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '0.35rem 0.6rem',
                borderRadius: '0.4rem',
                fontSize: '0.75rem',
                outline: 'none',
              }}
            >
              <option value={0}>Off</option>
              <option value={15}>15s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
            </select>
          </div>

          {/* Manual Refresh Button */}
          <button
            className={`refresh-button ${refreshSpin ? 'spinning' : ''}`}
            onClick={handleRefresh}
            title="Refresh Intelligence Data"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>

          {/* Download PDF Executive Report */}
          <button
            className={`btn-primary ${reportLoading ? 'loading' : ''}`}
            onClick={downloadReport}
            disabled={reportLoading}
            style={{ width: 'auto', padding: '0.5rem 1.1rem', fontSize: '0.85rem' }}
          >
            {reportLoading ? (
              <>
                <div className="loading-spinner"></div>
                <span>Compiling...</span>
              </>
            ) : (
              <>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <span>Export PDF</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* ─── Error Notification ─── */}
      {error && (
        <div className="error-message">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>⚠️</span>
            <span>{error}</span>
          </div>
          <button className="error-retry-btn" onClick={handleRefresh}>
            Retry Connection
          </button>
        </div>
      )}

      {/* ─── Executive KPI Cards Row ─── */}
      <section className="kpi-grid">
        <div className="glass-card kpi-card teal">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Latest Month Spend</span>
            <div className="kpi-icon-container">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
          <div className="kpi-value">{kpis ? formatCurrency(kpis.total_spend) : '$0'}</div>
          <div className="kpi-footer">Evaluation Cycle: {kpis?.month || 'Active'}</div>
        </div>

        <div className="glass-card kpi-card indigo">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Average Transaction Size</span>
            <div className="kpi-icon-container">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z"
                />
              </svg>
            </div>
          </div>
          <div className="kpi-value">${kpis ? kpis.avg_transaction_amount.toFixed(2) : '0.00'}</div>
          <div className="kpi-footer">Normalized across all active accounts</div>
        </div>

        <div className="glass-card kpi-card rose">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Surveillance Fraud Rate</span>
            <div className="kpi-icon-container">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
          </div>
          <div className="kpi-value">{kpis ? `${kpis.fraud_rate_percent.toFixed(2)}%` : '0.00%'}</div>
          <div className="kpi-footer">Threshold ceiling: 2.0% (Risk Level: Elevated)</div>
        </div>

        <div className="glass-card kpi-card amber">
          <div className="kpi-card-header">
            <span className="kpi-card-title">Audited Telemetry Volume</span>
            <div className="kpi-icon-container">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </div>
          </div>
          <div className="kpi-value">{totalVolumeCount.toLocaleString()}</div>
          <div className="kpi-footer">13 Evaluation cycles tracked</div>
        </div>
      </section>

      {/* ─── Navigation Tabs Bar ─── */}
      <nav className="nav-tabs-container">
        <button
          className={`nav-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
            />
          </svg>
          Executive Overview
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'risk' ? 'active' : ''}`}
          onClick={() => setActiveTab('risk')}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
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
          Risk & Surveillance
          {flaggedAnomaliesCount > 0 && <span className="nav-badge">{flaggedAnomaliesCount}</span>}
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'segments' ? 'active' : ''}`}
          onClick={() => setActiveTab('segments')}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          Cohort Intelligence
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'ledger' ? 'active' : ''}`}
          onClick={() => setActiveTab('ledger')}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
            />
          </svg>
          Transaction Ledger
        </button>
      </nav>

      {/* ─── Active Tab Content ─── */}
      {loading ? (
        <div className="loading-overlay">
          <div className="main-spinner"></div>
          <span>Synchronizing telemetry from FinSight analytics engine...</span>
        </div>
      ) : (
        <main>
          {activeTab === 'overview' && (
            <OverviewCharts
              monthlyVolumes={monthlyVolume}
              channelDistribution={channelData}
              topLocations={topLocations}
            />
          )}

          {activeTab === 'risk' && (
            <RiskView trends={trends} onSelectSegment={handleSelectSegment} />
          )}

          {activeTab === 'segments' && (
            <SegmentView
              overviewList={segmentOverview}
              selectedSegment={selectedSegment}
              onSelectSegment={(seg) => {
                setSelectedSegment(seg);
                loadSegmentData(seg);
              }}
              segmentHistory={segmentHistory}
              chartLoading={chartLoading}
            />
          )}

          {activeTab === 'ledger' && <TransactionLedger />}
        </main>
      )}
    </div>
  );
}
