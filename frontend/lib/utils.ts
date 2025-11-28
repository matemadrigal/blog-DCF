import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

export function formatLargeNumber(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

export function getRecommendationColor(recommendation: string): string {
  switch (recommendation.toLowerCase()) {
    case 'strong buy':
      return 'text-green-500';
    case 'buy':
      return 'text-green-400';
    case 'hold':
      return 'text-yellow-500';
    case 'sell':
      return 'text-orange-500';
    case 'strong sell':
      return 'text-red-500';
    default:
      return 'text-gray-500';
  }
}

export function getUpsideColor(upside: number): string {
  if (upside >= 30) return 'text-green-500';
  if (upside >= 15) return 'text-green-400';
  if (upside >= 0) return 'text-blue-400';
  if (upside >= -15) return 'text-orange-400';
  return 'text-red-500';
}
