import React, { useMemo } from 'react';
import { 
  BarChart2, 
  PieChart, 
  TrendingUp, 
  RotateCcw, 
  Shirt, 
  Sparkles, 
  Calendar,
  Layers,
  Award
} from 'lucide-react';

export default function AnalyticsDashboard({ clothes = [] }) {
  // Compute analytics dynamically from active clothes list
  const metrics = useMemo(() => {
    const totalItems = clothes.length;
    if (totalItems === 0) {
      return {
        totalItems: 0,
        utilizationScore: 0,
        mostWorn: [],
        leastWorn: [],
        categoryCounts: {},
        colorCounts: {},
        averageUsage: 0
      };
    }

    let totalUsage = 0;
    let itemsWornAtLeastOnce = 0;
    const categoryCounts = {};
    const colorCounts = {};

    clothes.forEach(item => {
      const usage = item.usageCount || 0;
      totalUsage += usage;
      if (usage > 0) itemsWornAtLeastOnce++;

      // Category count
      const cat = (item.category || 'other').toLowerCase();
      categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;

      // Color count
      const color = item.color || 'Neutral';
      colorCounts[color] = (colorCounts[color] || 0) + 1;
    });

    const utilizationScore = Math.round((itemsWornAtLeastOnce / totalItems) * 100);
    const averageUsage = (totalUsage / totalItems).toFixed(1);

    // Sorted items by usage count
    const sorted = [...clothes].sort((a, b) => (b.usageCount || 0) - (a.usageCount || 0));
    const mostWorn = sorted.slice(0, 4);
    const leastWorn = sorted.filter(c => (c.usageCount || 0) <= 2).slice(-4);

    return {
      totalItems,
      utilizationScore,
      mostWorn,
      leastWorn,
      categoryCounts,
      colorCounts,
      averageUsage
    };
  }, [clothes]);

  const categoryIcons = {
    tops: '👕',
    bottoms: '👖',
    outerwear: '🧥',
    footwear: '👟',
    bags: '👜',
    accessories: '💍',
    one_piece: '👗'
  };

  const topColors = Object.entries(metrics.colorCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', paddingBottom: '2rem' }}>
      
      {/* Header Banner */}
      <div style={{
        backgroundColor: '#FAF9FE',
        borderRadius: '24px',
        border: '1px solid #ECE7FE',
        padding: '2rem 2.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 4px 20px rgba(124, 77, 255, 0.04)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
            <BarChart2 size={24} color="#7C4DFF" />
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#7C4DFF', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Phase 7 Analytics
            </span>
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#1C1D21', margin: 0 }}>
            Wardrobe Intelligence & Utilization
          </h2>
          <p style={{ color: '#6A6E7D', fontSize: '0.9rem', marginTop: '0.3rem' }}>
            Data-driven rotation insights to maximize your style efficiency and minimize unworn clothing.
          </p>
        </div>

        <div style={{
          backgroundColor: '#FFFFFF',
          padding: '0.85rem 1.4rem',
          borderRadius: '16px',
          border: '1px solid #EAE6FF',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          boxShadow: '0 2px 10px rgba(0,0,0,0.02)'
        }}>
          <Award size={32} color="#7C4DFF" />
          <div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#1C1D21' }}>
              {metrics.utilizationScore}%
            </div>
            <div style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600 }}>
              Wardrobe Utilization Score
            </div>
          </div>
        </div>
      </div>

      {/* Top Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem' }}>
        
        <div className="card-widget" style={{ borderRadius: '20px', padding: '1.4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.85rem', color: '#8E92A0', fontWeight: 600 }}>Total Wardrobe Items</span>
            <Shirt size={20} color="#7C4DFF" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#1C1D21' }}>{metrics.totalItems}</div>
          <div style={{ fontSize: '0.78rem', color: '#6A6E7D', marginTop: '0.3rem' }}>Digitized clothing items</div>
        </div>

        <div className="card-widget" style={{ borderRadius: '20px', padding: '1.4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.85rem', color: '#8E92A0', fontWeight: 600 }}>Avg. Wear Count</span>
            <RotateCcw size={20} color="#10B981" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#1C1D21' }}>{metrics.averageUsage}x</div>
          <div style={{ fontSize: '0.78rem', color: '#6A6E7D', marginTop: '0.3rem' }}>Average wears per item</div>
        </div>

        <div className="card-widget" style={{ borderRadius: '20px', padding: '1.4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.85rem', color: '#8E92A0', fontWeight: 600 }}>Active Rotation</span>
            <TrendingUp size={20} color="#6366F1" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#1C1D21' }}>{metrics.utilizationScore}%</div>
          <div style={{ fontSize: '0.78rem', color: '#10B981', fontWeight: 600, marginTop: '0.3rem' }}>
            ✓ High Rotation Balance
          </div>
        </div>

        <div className="card-widget" style={{ borderRadius: '20px', padding: '1.4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
            <span style={{ fontSize: '0.85rem', color: '#8E92A0', fontWeight: 600 }}>Underused Items</span>
            <Sparkles size={20} color="#F59E0B" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#1C1D21' }}>{metrics.leastWorn.length}</div>
          <div style={{ fontSize: '0.78rem', color: '#F59E0B', fontWeight: 600, marginTop: '0.3rem' }}>
            Ready for fresh styling
          </div>
        </div>

      </div>

      {/* Main Content Grid: Categories & Color Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)', gap: '1.5rem' }}>
        
        {/* Category Distribution Breakdown */}
        <div className="card-widget" style={{ borderRadius: '24px', padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
            <Layers size={20} color="#7C4DFF" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1C1D21', margin: 0 }}>Category Breakdown</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {Object.entries(metrics.categoryCounts).map(([cat, count]) => {
              const pct = Math.round((count / metrics.totalItems) * 100);
              const icon = categoryIcons[cat] || '👚';
              return (
                <div key={cat} style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', fontWeight: 600, color: '#4A4D5A' }}>
                    <span style={{ textTransform: 'capitalize' }}>{icon} {cat}</span>
                    <span>{count} items ({pct}%)</span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: '#F0EBFF', borderRadius: '4px', overflow: 'hidden' }}>
                    <div 
                      style={{ 
                        height: '100%', 
                        width: `${pct}%`, 
                        backgroundColor: '#7C4DFF', 
                        borderRadius: '4px',
                        transition: 'width 0.4s ease'
                      }} 
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Color Spectrum */}
        <div className="card-widget" style={{ borderRadius: '24px', padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
            <PieChart size={20} color="#7C4DFF" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1C1D21', margin: 0 }}>Color Palette Spectrum</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {topColors.map(([color, count]) => {
              const pct = Math.round((count / metrics.totalItems) * 100);
              return (
                <div key={color} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 0.8rem', backgroundColor: '#FAF9FE', borderRadius: '12px', border: '1px solid #F0EEF8' }}>
                  <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#1C1D21' }}>🎨 {color}</span>
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#7C4DFF' }}>{count} pcs ({pct}%)</span>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* Most Worn vs Underused Items Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        
        {/* Most Worn Heavy Rotation Items */}
        <div className="card-widget" style={{ borderRadius: '24px', padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1C1D21', marginBottom: '1rem' }}>
            🔥 Most Worn Staples
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {metrics.mostWorn.map((item, idx) => (
              <div key={item.id || idx} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', backgroundColor: '#FAF9FE', borderRadius: '14px', border: '1px solid #ECE7FE' }}>
                <img 
                  src={item.imageUrl || 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=200'} 
                  alt={item.title} 
                  style={{ width: '50px', height: '50px', borderRadius: '10px', objectFit: 'cover' }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{item.title}</div>
                  <div style={{ fontSize: '0.78rem', color: '#8E92A0' }}>{item.category} • {item.color}</div>
                </div>
                <div style={{ padding: '0.3rem 0.75rem', backgroundColor: '#EFEAFF', borderRadius: '8px', color: '#7C4DFF', fontWeight: 700, fontSize: '0.8rem' }}>
                  {item.usageCount || 0} Wears
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Underused Hidden Gems */}
        <div className="card-widget" style={{ borderRadius: '24px', padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1C1D21', marginBottom: '1rem' }}>
            💎 Underused Wardrobe Gems
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {metrics.leastWorn.map((item, idx) => (
              <div key={item.id || idx} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', backgroundColor: '#FFFDF5', borderRadius: '14px', border: '1px solid #FDE68A' }}>
                <img 
                  src={item.imageUrl || 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=200'} 
                  alt={item.title} 
                  style={{ width: '50px', height: '50px', borderRadius: '10px', objectFit: 'cover' }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{item.title}</div>
                  <div style={{ fontSize: '0.78rem', color: '#8E92A0' }}>{item.category} • {item.color}</div>
                </div>
                <div style={{ padding: '0.3rem 0.75rem', backgroundColor: '#FEF3C7', borderRadius: '8px', color: '#D97706', fontWeight: 700, fontSize: '0.8rem' }}>
                  {item.usageCount || 0} Wears
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
