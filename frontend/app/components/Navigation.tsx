"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { TrendingUp, BarChart3, Scale, Calendar, Bell, Home } from 'lucide-react';

const navItems = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/analysis', label: 'Analysis', icon: TrendingUp },
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/comparator', label: 'Comparator', icon: Scale },
  { href: '/historical', label: 'Historical', icon: Calendar },
  { href: '/alerts', label: 'Alerts', icon: Bell },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 bg-dark-card/95 backdrop-blur-sm border-b border-dark-border">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center font-bold text-xl">
              💼
            </div>
            <span className="text-xl font-bold gradient-text hidden md:block">
              DCF Valuation
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg transition-all
                    ${isActive
                      ? 'bg-gradient-primary text-white'
                      : 'text-gray-300 hover:text-white hover:bg-dark-background'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:block font-medium">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
