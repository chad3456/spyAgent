export interface NewsItem {
  title: string;
  url: string;
  source: string;
  publishedAt: string;
  category?: string;
}

export interface TimeSeriesPoint {
  year: number;
  value: number | null;
}

export interface EconomicIndicator {
  name: string;
  value: number;
  unit: string;
  year: number;
  source: string;
}

export interface EconomicData {
  gdp: { value: number; year: number; unit: string } | null;
  gdpGrowth: TimeSeriesPoint[];
  fdi: TimeSeriesPoint[];
  inflation: TimeSeriesPoint[];
  indicators: EconomicIndicator[];
  news: NewsItem[];
  lastUpdated: string;
}

export interface AIInfraData {
  news: NewsItem[];
  lastUpdated: string;
}

export interface InfrastructureData {
  power: TimeSeriesPoint[];
  renewable: TimeSeriesPoint[];
  news: NewsItem[];
  lastUpdated: string;
}

export interface DefenseData {
  militaryExpenditure: TimeSeriesPoint[];
  militaryGdpPercent: TimeSeriesPoint[];
  news: NewsItem[];
  lastUpdated: string;
}

export interface SummaryData {
  lastUpdated: string;
  status: 'healthy' | 'partial' | 'error';
}

export type TabId = 'economy' | 'ai-tech' | 'infrastructure' | 'defence';

export interface TabConfig {
  id: TabId;
  label: string;
  icon: string;
}
