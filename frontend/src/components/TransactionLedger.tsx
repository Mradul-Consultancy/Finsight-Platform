import React, { useState, useEffect } from 'react';
import { fetchTransactions } from '../api/client';
import type { Transaction, TransactionResponse } from '../api/client';

export const TransactionLedger: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [perPage, setPerPage] = useState<number>(15);
  const [search, setSearch] = useState<string>('');
  const [selectedChannel, setSelectedChannel] = useState<string>('All');
  const [sortBy, setSortBy] = useState<string>('transaction_date');
  const [sortDir, setSortDir] = useState<string>('desc');
  const [loading, setLoading] = useState<boolean>(false);

  const loadData = async () => {
    setLoading(true);
    try {
      // If a channel filter is chosen, append to search query
      const query = selectedChannel === 'All' ? search : `${search} ${selectedChannel}`.trim();
      const res: TransactionResponse = await fetchTransactions(
        query,
        page,
        perPage,
        sortBy,
        sortDir
      );
      setTransactions(res.transactions);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Error fetching transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, perPage, selectedChannel, sortBy, sortDir]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  const handleExportCSV = () => {
    if (transactions.length === 0) return;
    const headers = [
      'Transaction ID',
      'Customer ID',
      'Merchant ID',
      'Amount ($)',
      'Date',
      'Type',
      'Location',
      'Channel',
      'Balance ($)',
      'Login Attempts',
    ];
    const rows = transactions.map((t) => [
      t.transaction_id,
      t.customer_id,
      t.merchant_id,
      t.transaction_amount,
      t.transaction_date,
      t.transaction_type,
      t.location,
      t.channel,
      t.account_balance,
      t.login_attempts,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute(
      'download',
      `finsight_transactions_page${page}_${new Date().toISOString().split('T')[0]}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="glass-card">
      <div className="chart-card-header" style={{ marginBottom: '1.25rem' }}>
        <div className="chart-title">
          <h2>Transactional Activity Ledger</h2>
          <p>Real-time audit log of multi-channel transactions with anomaly indicators</p>
        </div>
        <button onClick={handleExportCSV} className="btn-secondary" title="Export page to CSV">
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
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export CSV
        </button>
      </div>

      {/* Toolbar: Search, Channel Filters, Sorting */}
      <div className="transactions-toolbar">
        <form onSubmit={handleSearchSubmit} className="search-input-wrap">
          <svg
            className="search-icon"
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
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            className="search-input"
            placeholder="Search account, merchant, city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>

        <div className="filter-pills-group">
          {['All', 'Online', 'ATM', 'Branch'].map((ch) => (
            <button
              key={ch}
              className={`filter-pill ${selectedChannel === ch ? 'active' : ''}`}
              onClick={() => {
                setSelectedChannel(ch);
                setPage(1);
              }}
            >
              {ch}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              background: 'rgba(17, 24, 39, 0.8)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              padding: '0.4rem 0.6rem',
              borderRadius: '0.4rem',
              fontSize: '0.825rem',
              outline: 'none',
            }}
          >
            <option value="transaction_date">Date</option>
            <option value="transaction_amount">Amount</option>
            <option value="account_balance">Balance</option>
          </select>

          <button
            onClick={() => setSortDir((prev) => (prev === 'desc' ? 'asc' : 'desc'))}
            className="pagination-btn"
            title={`Sort Direction: ${sortDir.toUpperCase()}`}
          >
            {sortDir === 'desc' ? '▼ Desc' : '▲ Asc'}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table className="sleek-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Merchant</th>
              <th>Date / Time</th>
              <th>Channel</th>
              <th>Location</th>
              <th>Type</th>
              <th className="text-right">Balance</th>
              <th className="text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '3rem' }}>
                  <div className="loading-spinner" style={{ margin: '0 auto 0.5rem' }}></div>
                  <span style={{ color: 'var(--text-muted)' }}>Loading transactions...</span>
                </td>
              </tr>
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '3rem' }}>
                  No transactions found matching your filter criteria.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => {
                const isHighLogin = tx.login_attempts > 1;
                const channelBadgeClass =
                  tx.channel === 'Online'
                    ? 'badge-online'
                    : tx.channel === 'ATM'
                    ? 'badge-atm'
                    : 'badge-branch';

                return (
                  <tr key={tx.transaction_id}>
                    <td className="font-mono" style={{ color: 'var(--text-muted)' }}>
                      {tx.transaction_id}
                    </td>
                    <td style={{ fontWeight: 600 }}>{tx.customer_id}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{tx.merchant_id}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {tx.transaction_date ? tx.transaction_date.replace('T', ' ') : '-'}
                    </td>
                    <td>
                      <span className={channelBadgeClass}>{tx.channel}</span>
                    </td>
                    <td>{tx.location}</td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          color: tx.transaction_type === 'Credit' ? '#34d399' : '#e5e7eb',
                          fontWeight: 500,
                        }}
                      >
                        {tx.transaction_type}
                      </span>
                      {isHighLogin && (
                        <span
                          title={`Security Flag: ${tx.login_attempts} login attempts recorded`}
                          style={{
                            marginLeft: '0.4rem',
                            color: 'var(--accent-amber)',
                            fontSize: '0.75rem',
                          }}
                        >
                          ⚠️
                        </span>
                      )}
                    </td>
                    <td className="text-right font-mono" style={{ color: 'var(--text-secondary)' }}>
                      ${tx.account_balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td
                      className="text-right font-mono"
                      style={{
                        fontWeight: 700,
                        color: tx.transaction_type === 'Credit' ? '#34d399' : 'var(--text-primary)',
                      }}
                    >
                      ${tx.transaction_amount.toFixed(2)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="pagination-controls">
        <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
          Showing {(page - 1) * perPage + 1} - {Math.min(page * perPage, total)} of {total.toLocaleString()} transactions
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <select
            value={perPage}
            onChange={(e) => {
              setPerPage(Number(e.target.value));
              setPage(1);
            }}
            style={{
              background: 'rgba(17, 24, 39, 0.8)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              padding: '0.35rem 0.5rem',
              borderRadius: '0.35rem',
              fontSize: '0.8rem',
            }}
          >
            <option value={10}>10 / page</option>
            <option value={15}>15 / page</option>
            <option value={25}>25 / page</option>
            <option value={50}>50 / page</option>
          </select>

          <button
            className="pagination-btn"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ← Previous
          </button>
          <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
            Page {page} of {totalPages}
          </span>
          <button
            className="pagination-btn"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
};
