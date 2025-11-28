/**
 * API client for DCF Valuation Platform backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DCFCalculationRequest {
  ticker: string;
  projection_years?: number;
  growth_rate?: number;
  terminal_growth_rate?: number;
  discount_rate?: number;
  use_intelligent_values?: boolean;
}

export interface DCFResult {
  ticker: string;
  company_name: string;
  calculation_date: string;
  current_price: number;
  fair_value: number;
  upside_percentage: number;
  recommendation: string;
  confidence_score: number;
  projection_years: number;
  growth_rate: number;
  terminal_growth_rate: number;
  discount_rate: number;
  fcf_current?: number;
  revenue_current?: number;
  shares_outstanding?: number;
}

export interface CompanyInfo {
  ticker: string;
  name: string;
  sector: string;
  market_cap?: number;
  current_price?: number;
}

export interface DashboardSummary {
  total_companies: number;
  avg_upside: number;
  strong_buys: number;
  buys: number;
  holds: number;
  sells: number;
  last_updated: string;
  top_opportunities: DCFResult[];
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: 'Request failed',
        detail: response.statusText,
      }));
      throw new Error(error.detail || error.error || 'Request failed');
    }

    return response.json();
  }

  // DCF Endpoints
  async calculateDCF(request: DCFCalculationRequest): Promise<DCFResult> {
    return this.request<DCFResult>('/api/dcf/calculate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getSensitivityAnalysis(
    ticker: string,
    baseGrowth?: number,
    baseDiscount?: number
  ): Promise<any> {
    const params = new URLSearchParams();
    if (baseGrowth !== undefined) params.append('base_growth', String(baseGrowth));
    if (baseDiscount !== undefined) params.append('base_discount', String(baseDiscount));

    return this.request(`/api/dcf/sensitivity/${ticker}?${params}`);
  }

  async getValuationHistory(ticker: string, days: number = 90): Promise<any[]> {
    return this.request(`/api/dcf/history/${ticker}?days=${days}`);
  }

  // Company Endpoints
  async searchCompanies(query: string, limit: number = 20): Promise<CompanyInfo[]> {
    return this.request(`/api/companies/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  async getCompanyInfo(ticker: string): Promise<CompanyInfo> {
    return this.request(`/api/companies/${ticker}`);
  }

  async getCompaniesBySector(sector: string, limit: number = 50): Promise<CompanyInfo[]> {
    return this.request(`/api/companies/sector/${sector}?limit=${limit}`);
  }

  async getAllSectors(): Promise<string[]> {
    return this.request('/api/companies/');
  }

  // Dashboard Endpoints
  async getDashboardSummary(): Promise<DashboardSummary> {
    return this.request('/api/dashboard/summary');
  }

  // Health Check
  async healthCheck(): Promise<any> {
    return this.request('/api/health');
  }
}

export const apiClient = new APIClient();
