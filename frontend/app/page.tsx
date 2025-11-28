import Link from 'next/link';
import { TrendingUp, BarChart3, Scale, Calendar, Bell } from 'lucide-react';

const features = [
  {
    icon: TrendingUp,
    title: "Individual Analysis",
    description: "Complete DCF calculation for a specific company with detailed analysis and advanced visualizations.",
    href: "/analysis",
    color: "from-blue-500 to-cyan-500"
  },
  {
    icon: BarChart3,
    title: "Executive Dashboard",
    description: "Consolidated overview of all analyzed companies with key metrics and investment recommendations.",
    href: "/dashboard",
    color: "from-purple-500 to-pink-500"
  },
  {
    icon: Scale,
    title: "Comparator",
    description: "Compare multiple companies side by side to identify the best investment opportunities.",
    href: "/comparator",
    color: "from-green-500 to-emerald-500"
  },
  {
    icon: Calendar,
    title: "Historical Analysis",
    description: "Temporal evolution of Fair Value vs Market Price for trend tracking.",
    href: "/historical",
    color: "from-orange-500 to-red-500"
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0A0E27] via-[#0A0E27] to-[#0d1234]">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center space-y-6 max-w-4xl mx-auto">
          <h1 className="text-6xl font-bold gradient-text mb-6">
            DCF Valuation Platform
          </h1>
          <p className="text-2xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
            Professional valuation platform that compares{' '}
            <span className="text-primary-500 font-semibold">Fair Value (DCF)</span> vs{' '}
            <span className="text-accent font-semibold">Market Price</span>.
            Advanced tool for financial analysis and investment decision-making.
          </p>
          <div className="flex gap-4 justify-center mt-8">
            <Link
              href="/analysis"
              className="px-8 py-4 bg-gradient-primary text-white rounded-lg font-semibold text-lg hover:opacity-90 transition-opacity"
            >
              Start Analysis
            </Link>
            <Link
              href="/dashboard"
              className="px-8 py-4 bg-dark-card border border-dark-border text-white rounded-lg font-semibold text-lg hover:border-primary-500 transition-colors"
            >
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Link
                key={index}
                href={feature.href}
                className="group relative overflow-hidden rounded-2xl bg-dark-card border border-dark-border p-6 hover:border-primary-500 transition-all duration-300 hover:scale-105"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 transition-opacity`} />
                <div className="relative z-10 space-y-4">
                  <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">
                    {feature.title}
                  </h3>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Quick Start Section */}
      <section className="container mx-auto px-4 py-16 mb-16">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            🚀 Quick Start
          </h2>
          <div className="bg-dark-card border border-dark-border rounded-2xl p-8 space-y-4">
            {[
              { step: 1, text: "Navigate to Individual Analysis from the menu" },
              { step: 2, text: "Enter the company ticker you want to analyze" },
              { step: 3, text: "Configure DCF parameters (or use intelligent values)" },
              { step: 4, text: "Review the calculated Fair Value and compare with market price" },
            ].map((item) => (
              <div key={item.step} className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0 font-bold">
                  {item.step}
                </div>
                <p className="text-gray-300 text-lg pt-1">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
