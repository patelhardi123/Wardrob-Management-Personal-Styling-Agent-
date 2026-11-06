import React, { useState } from 'react';
import { Plus, Filter, Shirt, Footprints, Shield, ShoppingBag, Watch, Trash2, UploadCloud, AlertCircle } from 'lucide-react';
import ItemDetailModal from './ItemDetailModal';

export default function WardrobeGrid({ clothes, onAddItem, onDeleteItem, onUpdateItem }) {
  const [activeCategory, setActiveCategory] = useState('all');
  const [selectedItem, setSelectedItem] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [savingId, setSavingId] = useState(null);

  const categories = [
    { id: 'all', label: 'All Items', icon: Filter },
    { id: 'tops', label: 'Tops & Shirts', icon: Shirt },
    { id: 'bottoms', label: 'Bottoms & Pants', icon: Shield },
    { id: 'one_piece', label: 'One-Piece & Dresses', icon: Shirt },
    { id: 'outerwear', label: 'Outerwear', icon: Shield },
    { id: 'footwear', label: 'Footwear', icon: Footprints },
    { id: 'bags', label: 'Bags & Purses', icon: ShoppingBag },
    { id: 'accessories', label: 'Accessories', icon: Watch },
  ];

  const filteredClothes = activeCategory === 'all' 
    ? clothes 
    : clothes.filter(item => item.category === activeCategory);

  const handleItemClick = (item) => {
    setSelectedItem(item);
    setIsDetailModalOpen(true);
  };

  const handleCloseDetailModal = () => {
    setIsDetailModalOpen(false);
    setSelectedItem(null);
  };

  const handleEditItem = (item) => {
    // For now, just close the modal. You can extend this to open an edit modal
    handleCloseDetailModal();
    console.log('Edit item:', item);
  };

  const handleMarkMissing = async (item) => {
    setSavingId(item.id);
    try {
      const response = await fetch(`http://localhost:8000/api/clothes/${encodeURIComponent(item.id)}/availability`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          availability_status: 'missing',
          ironing_status: 'ready',
          expected_available_at: null,
          notify_when_ready: false,
          status_note: null,
          user_id: 1,
        }),
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Could not mark item as missing.');
      }
      onUpdateItem(data.item);
    } catch (err) {
      console.error('Failed to mark item as missing:', err);
      alert('Failed to mark item as missing. Please try again.');
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-heading)', lineHeight: 1.1 }}>
            My Digital Closet ({clothes.length} items)
          </h2>
          <p style={{ color: '#64748B', fontSize: '0.88rem', marginTop: '0.25rem' }}>
            Digitized garments used for AI outfit generation.
          </p>
        </div>

        <button onClick={onAddItem} className="btn-primary">
          <UploadCloud size={17} /> Upload New Item
        </button>
      </div>

      {/* Category Tabs */}
      <div style={{ display: 'flex', gap: '0.65rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        {categories.map(cat => {
          const Icon = cat.icon;
          const count = cat.id === 'all' ? clothes.length : clothes.filter(c => c.category === cat.id).length;
          const isActive = activeCategory === cat.id;

          return (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              style={{
                border: isActive ? 'none' : '1px solid #ECEBF5',
                background: isActive ? '#7C4DFF' : '#FFFFFF',
                color: isActive ? '#FFFFFF' : '#606470',
                borderRadius: '12px',
                whiteSpace: 'nowrap',
                padding: '0.65rem 1.1rem',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                boxShadow: isActive ? '0 4px 14px rgba(124, 77, 255, 0.3)' : '0 2px 6px rgba(0, 0, 0, 0.02)',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={16} /> {cat.label} ({count})
            </button>
          );
        })}
      </div>

      {/* Clothes Card Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '1.25rem' }}>
        
        {/* Upload Card Prompt */}
        <div 
          onClick={onAddItem}
          className="card-widget" 
          style={{ 
            border: '2px dashed #7C4DFF', 
            background: '#FAF9FE', 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center', 
            minHeight: '280px', 
            cursor: 'pointer',
            textAlign: 'center',
            padding: '1.5rem',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#F0EBFF'}
          onMouseLeave={(e) => e.currentTarget.style.background = '#FAF9FE'}
        >
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#F0EBFF', color: '#7C4DFF', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.85rem' }}>
            <UploadCloud size={24} />
          </div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.35rem' }}>
            Upload Owned {activeCategory !== 'all' ? activeCategory.toUpperCase() : 'CLOTH'}
          </h4>
          <p style={{ fontSize: '0.78rem', color: '#8E92A0', maxWidth: '180px', lineHeight: 1.4 }}>
            Add photo, category, color, pattern and style tag to your digital wardrobe.
          </p>
        </div>

        {filteredClothes.map(item => (
          <div 
            key={item.id} 
            className="card-widget" 
            style={{ 
              overflow: 'hidden', 
              padding: 0, 
              display: 'flex', 
              flexDirection: 'column',
              cursor: 'pointer',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease'
            }}
            onClick={() => handleItemClick(item)}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 8px 24px rgba(124, 77, 255, 0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'none';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            
            {/* Garment Image */}
            <div style={{ width: '100%', height: '210px', overflow: 'hidden', background: '#FAF9FE', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.75rem', backgroundImage: 'radial-gradient(#ECEBF5 1px, transparent 1px)', backgroundSize: '16px 16px' }}>
              <img 
                src={item.imageUrl} 
                alt={item.title} 
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', transition: 'transform 0.3s ease', filter: 'drop-shadow(0 6px 14px rgba(0, 0, 0, 0.12))' }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.06)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
              />
              <span style={{
                position: 'absolute',
                top: '10px',
                left: '10px',
                padding: '0.2rem 0.6rem',
                borderRadius: '8px',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                color: '#7C4DFF',
                fontSize: '0.72rem',
                fontWeight: 700,
                backdropFilter: 'blur(4px)',
                textTransform: 'capitalize'
              }}>
                {item.category}
              </span>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleMarkMissing(item);
                }}
                disabled={savingId === item.id}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '50px',
                  background: 'rgba(255, 255, 255, 0.95)',
                  border: 'none',
                  borderRadius: '50%',
                  width: '30px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#DC2626',
                  cursor: 'pointer',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
                  opacity: savingId === item.id ? 0.5 : 1
                }}
                title="Mark as missing"
              >
                <AlertCircle size={14} />
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteItem(item.id);
                }}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  background: 'rgba(255, 255, 255, 0.95)',
                  border: 'none',
                  borderRadius: '50%',
                  width: '30px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FF5252',
                  cursor: 'pointer',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
                }}
                title="Remove item"
              >
                <Trash2 size={14} />
              </button>
            </div>

            {/* Details */}
            <div style={{ padding: '1.1rem', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.4rem' }}>{item.title}</h4>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.74rem', color: '#606470', background: '#F3F1FD', padding: '0.2rem 0.55rem', borderRadius: '6px', fontWeight: 600 }}>
                    {item.color}
                  </span>
                  <span style={{ fontSize: '0.74rem', color: '#606470', background: '#F3F1FD', padding: '0.2rem 0.55rem', borderRadius: '6px', fontWeight: 600 }}>
                    {item.style}
                  </span>
                  <span style={{ fontSize: '0.74rem', color: '#606470', background: '#F3F1FD', padding: '0.2rem 0.55rem', borderRadius: '6px', fontWeight: 600 }}>
                    {item.season}
                  </span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid #F0EEF8', paddingTop: '0.6rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#8E92A0' }}>
                <span>Usage: {item.usageCount} times</span>
                <span>Last: {item.lastUsed}</span>
              </div>
            </div>

          </div>
        ))}
      </div>

      {/* Item Detail Modal */}
      <ItemDetailModal
        isOpen={isDetailModalOpen}
        onClose={handleCloseDetailModal}
        item={selectedItem}
        onEdit={handleEditItem}
        onDelete={onDeleteItem}
        onUpdate={(updatedItem) => {
          setSelectedItem(updatedItem);
          if (onUpdateItem) onUpdateItem(updatedItem);
        }}
      />

    </div>
  );
}
