// API client for FinSight – Enhanced Dashboard
const BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8002/api';

// ─── Core KPI Types ───
export interface KPIData {
  month: string | null;
  total_spend: number;
  avg_transaction_amount: number;
  fraud_rate_percent: number;
}

export interface Anomaly {
  month: string;
  segment: string;
  total_spent: number;
  z_score: number;
  flag: boolean;
}

export interface SegmentHistoryItem {
  month: string;
  total_spent: number;
}

export interface SegmentData {
  segment: string;
  history: SegmentHistoryItem[];
}

// ─── Enhanced Analytics Types ───
export interface ChannelData {
  channel: string;
  count: number;
  total_amount: number;
}

export interface MonthlyVolume {
  month: string;
  txn_count: number;
  total_spend: number;
  avg_amount: number;
}

export interface LocationData {
  location: string;
  txn_count: number;
  total_amount: number;
}

export interface Transaction {
  transaction_id: string;
  customer_id: string;
  merchant_id: string;
  transaction_amount: number;
  transaction_date: string | null;
  transaction_type: string;
  location: string;
  channel: string;
  account_balance: number;
  login_attempts: number;
}

export interface TransactionResponse {
  transactions: Transaction[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SegmentOverview {
  segment: string;
  txn_count: number;
  total_spend: number;
  avg_amount: number;
  avg_age: number;
}

// ─── Core Endpoints ───
export const fetchKPIs = async (): Promise<KPIData> => {
  const response = await fetch(`${BASE_URL}/kpis`);
  if (!response.ok) throw new Error('Failed to fetch KPIs');
  return response.json();
};

export const fetchTrends = async (): Promise<{ anomalies: Anomaly[] }> => {
  const response = await fetch(`${BASE_URL}/trends`);
  if (!response.ok) throw new Error('Failed to fetch trends');
  return response.json();
};

export const fetchSegmentData = async (segmentId: string): Promise<SegmentData> => {
  const response = await fetch(`${BASE_URL}/segment/${segmentId}`);
  if (!response.ok) throw new Error(`Failed to fetch segment data for ${segmentId}`);
  return response.json();
};

export const getReportUrl = (): string => {
  return `${BASE_URL}/report/generate`;
};

// ─── Enhanced Analytics Endpoints ───
export const fetchChannelDistribution = async (): Promise<{ channels: ChannelData[] }> => {
  const response = await fetch(`${BASE_URL}/analytics/channel-distribution`);
  if (!response.ok) throw new Error('Failed to fetch channel distribution');
  return response.json();
};

export const fetchMonthlyVolume = async (): Promise<{ months: MonthlyVolume[] }> => {
  const response = await fetch(`${BASE_URL}/analytics/monthly-volume`);
  if (!response.ok) throw new Error('Failed to fetch monthly volume');
  return response.json();
};

export const fetchTopLocations = async (): Promise<{ locations: LocationData[] }> => {
  const response = await fetch(`${BASE_URL}/analytics/top-locations`);
  if (!response.ok) throw new Error('Failed to fetch top locations');
  return response.json();
};

export const fetchTransactions = async (
  search = '',
  page = 1,
  perPage = 15,
  sortBy = 'transaction_date',
  sortDir = 'desc'
): Promise<TransactionResponse> => {
  const params = new URLSearchParams({
    search,
    page: String(page),
    per_page: String(perPage),
    sort_by: sortBy,
    sort_dir: sortDir,
  });
  const response = await fetch(`${BASE_URL}/analytics/transactions?${params}`);
  if (!response.ok) throw new Error('Failed to fetch transactions');
  return response.json();
};

export const fetchSegmentOverview = async (): Promise<{ segments: SegmentOverview[] }> => {
  const response = await fetch(`${BASE_URL}/analytics/segment-overview`);
  if (!response.ok) throw new Error('Failed to fetch segment overview');
  return response.json();
};
