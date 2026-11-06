import React, { useState } from 'react';
import { X, Edit2, Calendar, Activity, Tag, Palette, Shirt, Shield, Footprints, ShoppingBag, Watch, RotateCcw, RotateCw } from 'lucide-react';

// Helper function to convert color names to hex codes
const getColorHex = (colorName) => {
  const colorMap = {
    'black': '#000000',
    'white': '#FFFFFF',
    'red': '#FF0000',
    'blue': '#0000FF',
    'green': '#008000',
    'yellow': '#FFFF00',
    'pink': '#FFC0CB',
    'purple': '#800080',
    'orange': '#FFA500',
    'brown': '#A52A2A',
    'grey': '#808080',
    'gray': '#808080',
    'navy': '#000080',
    'beige': '#F5F5DC',
    'cream': '#FFFDD0',
    'gold': '#FFD700',
    'silver': '#C0C0C0',
    'teal': '#008080',
    'maroon': '#800000',
    'lavender': '#E6E6FA',
    'mint': '#98FF98',
    'coral': '#FF7F50',
    'turquoise': '#40E0D0'
  };
  
  const lowerColor = colorName.toLowerCase();
  return colorMap[lowerColor] || '#7C4DFF'; // Default to purple if color not found
};

export default function ItemDetailModal({ isOpen, onClose, item, onEdit, onDelete, onUpdate }) {
  if (!isOpen || !item) return null;

  const handleRotate = (degrees) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const canvas = document.createElement('canvas');
      if (degrees === 90 || degrees === 270 || degrees === -90) {
        canvas.width = img.height;
        canvas.height = img.width;
      } else {
        canvas.width = img.width;
        canvas.height = img.height;
      }
      const ctx = canvas.getContext('2d');
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((degrees * Math.PI) / 180);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);
      const rotatedUrl = canvas.toDataURL('image/png');
      if (onUpdate) {
        onUpdate({ ...item, imageUrl: rotatedUrl });
      }
    };
    img.src = item.imageUrl;
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'tops': return Shirt;
      case 'bottoms': return Shield;
      case 'outerwear': return Shield;
      case 'footwear': return Footprints;
      case 'bags': return ShoppingBag;
      case 'accessories': return Watch;
      default: return Shirt;
    }
  };

  const CategoryIcon = getCategoryIcon(item.category);

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 20, 30, 0.75)',
      backdropFilter: 'blur(8px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem'
    }}>
      <div 
        style={{ 
          maxWidth: '900px', 
          width: '100%', 
          maxHeight: '90vh',
          background: '#FFFFFF',
          borderRadius: '24px',
          boxShadow: '0 24px 60px rgba(0, 0, 0, 0.3)',
          border: '1px solid #ECEBF5',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header */}
        <div style={{ 
          padding: '1.25rem 1.75rem', 
          borderBottom: '1px solid #ECEBF5',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#FAF9FE'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ 
              width: '40px', 
              height: '40px', 
              borderRadius: '12px', 
              background: '#F0EBFF', 
              color: '#7C4DFF', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center' 
            }}>
              <CategoryIcon size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1C1D21', margin: 0 }}>
                {item.title}
              </h3>
              <p style={{ fontSize: '0.8rem', color: '#8E92A0', margin: 0, textTransform: 'capitalize' }}>
                {item.category}
              </p>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => onEdit && onEdit(item)}
              style={{
                padding: '0.6rem 1rem',
                borderRadius: '10px',
                border: '1px solid #ECEBF5',
                background: '#FFFFFF',
                color: '#7C4DFF',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#F0EBFF'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#FFFFFF'}
            >
              <Edit2 size={16} /> Edit
            </button>
            <button 
              onClick={onClose}
              style={{ 
                background: '#FAF9FE', 
                border: '1px solid #ECE7FE', 
                color: '#606470', 
                cursor: 'pointer',
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#F0EBFF'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#FAF9FE'}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div style={{ 
          padding: '1.75rem',
          overflowY: 'auto',
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '2rem'
        }}>
          {/* Image Section */}
          <div>
            <div style={{ 
              position: 'relative',
              borderRadius: '16px', 
              overflow: 'hidden', 
              border: '2px solid #ECEBF5',
              background: '#FAF9FE',
              aspectRatio: '1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img 
                src={item.imageUrl} 
                alt={item.title} 
                style={{ 
                  width: '100%', 
                  height: '100%', 
                  objectFit: 'contain',
                  background: '#FFFFFF'
                }} 
              />
              <div style={{ position: 'absolute', bottom: '10px', right: '10px', display: 'flex', gap: '0.4rem' }}>
                <button
                  type="button"
                  onClick={() => handleRotate(-90)}
                  title="Rotate Left 90°"
                  style={{ background: 'rgba(28, 29, 33, 0.85)', color: '#FFFFFF', border: 'none', padding: '0.45rem 0.8rem', borderRadius: '999px', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem', backdropFilter: 'blur(4px)' }}
                >
                  <RotateCcw size={14} /> Rotate Left
                </button>
                <button
                  type="button"
                  onClick={() => handleRotate(90)}
                  title="Rotate Right 90°"
                  style={{ background: 'rgba(28, 29, 33, 0.85)', color: '#FFFFFF', border: 'none', padding: '0.45rem 0.8rem', borderRadius: '999px', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem', backdropFilter: 'blur(4px)' }}
                >
                  <RotateCw size={14} /> Rotate Right
                </button>
              </div>
            </div>
            
            {/* Usage Stats */}
            <div style={{ 
              marginTop: '1.25rem',
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '1rem'
            }}>
              <div style={{ 
                padding: '1rem',
                borderRadius: '12px',
                background: '#F3F1FD',
                border: '1px solid #ECE7FE'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <Activity size={16} color="#7C4DFF" />
                  <span style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600 }}>Usage Count</span>
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1C1D21' }}>
                  {item.usageCount} times
                </div>
              </div>
              
              <div style={{ 
                padding: '1rem',
                borderRadius: '12px',
                background: '#F3F1FD',
                border: '1px solid #ECE7FE'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <Calendar size={16} color="#7C4DFF" />
                  <span style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600 }}>Last Used</span>
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1C1D21' }}>
                  {item.lastUsed}
                </div>
              </div>
            </div>
          </div>

          {/* Details Section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* Item Attributes */}
            <div>
              <h4 style={{ 
                fontSize: '0.9rem', 
                fontWeight: 800, 
                color: '#1C1D21', 
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Tag size={18} color="#7C4DFF" />
                AI Extracted Garment Attributes
              </h4>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ padding: '0.85rem', borderRadius: '12px', background: '#FAF9FE', border: '1px solid #ECEBF5' }}>
                  <div style={{ fontSize: '0.72rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.2rem' }}>Color</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1C1D21', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <div style={{ width: '16px', height: '16px', borderRadius: '50%', background: getColorHex(item.color), border: '1px solid #CCC' }} />
                    {item.color}
                  </div>
                </div>

                <div style={{ padding: '0.85rem', borderRadius: '12px', background: '#FAF9FE', border: '1px solid #ECEBF5' }}>
                  <div style={{ fontSize: '0.72rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.2rem' }}>Garment Type</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1C1D21', textTransform: 'capitalize' }}>
                    {(item.attributes?.type || item.style || 'Standard').replace(/_/g, ' ')}
                  </div>
                </div>

                <div style={{ padding: '0.85rem', borderRadius: '12px', background: '#FAF9FE', border: '1px solid #ECEBF5' }}>
                  <div style={{ fontSize: '0.72rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.2rem' }}>Fit Cut</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#7C4DFF', textTransform: 'capitalize' }}>
                    {item.attributes?.fit || 'Regular'}
                  </div>
                </div>

                <div style={{ padding: '0.85rem', borderRadius: '12px', background: '#FAF9FE', border: '1px solid #ECEBF5' }}>
                  <div style={{ fontSize: '0.72rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.2rem' }}>Silhouette Profile</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1C1D21', textTransform: 'capitalize' }}>
                    {item.attributes?.silhouette || 'Straight'}
                  </div>
                </div>

                <div style={{ padding: '0.85rem', borderRadius: '12px', background: '#FAF9FE', border: '1px solid #ECEBF5' }}>
                  <div style={{ fontSize: '0.72rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.2rem' }}>Formality Rating</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1C1D21' }}>
                    {item.attributes?.formality || 5}/10
                  </div>
                </div>

                <div style={{ padding: '0.85rem', borderRadius: '12px', background: '#FAF9FE', border: '1px solid #ECEBF5' }}>
                  <div style={{ fontSize: '0.72rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.2rem' }}>
                    {item.category === 'bottoms' ? 'Leg Shape & Rise' : 'Length & Cut'}
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1C1D21', textTransform: 'capitalize' }}>
                    {item.category === 'bottoms' ? `${item.attributes?.leg_shape || 'straight'} (${item.attributes?.rise || 'mid'} rise)` : (item.attributes?.length || item.season || 'Regular')}
                  </div>
                </div>
              </div>
            </div>

            {/* Category Badge */}
            <div style={{
              padding: '1rem',
              borderRadius: '12px',
              background: '#F0EBFF',
              border: '1px solid #ECE7FE',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem'
            }}>
              <CategoryIcon size={24} color="#7C4DFF" />
              <div>
                <div style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600 }}>
                  Category
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#7C4DFF', textTransform: 'capitalize' }}>
                  {item.category}
                </div>
              </div>
            </div>

            {/* Availability Status */}
            <div style={{
              padding: '1rem',
              borderRadius: '12px',
              background: '#F0EBFF',
              border: '1px solid #ECE7FE'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.5rem' }}>
                Availability Status
              </div>
              <select
                value={item.availability_status || 'available'}
                onChange={(e) => onUpdate && onUpdate({ ...item, availability_status: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.6rem',
                  borderRadius: '8px',
                  border: '1px solid #ECE7FE',
                  background: '#FFFFFF',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  color: '#1C1D21',
                  cursor: 'pointer'
                }}
              >
                <option value="available">Available</option>
                <option value="in_wash">In Wash</option>
                <option value="drying">Drying</option>
                <option value="unavailable">Unavailable</option>
              </select>
            </div>

            {/* Ironing Status */}
            <div style={{
              padding: '1rem',
              borderRadius: '12px',
              background: '#F0EBFF',
              border: '1px solid #ECE7FE'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600, marginBottom: '0.5rem' }}>
                Ironing Status
              </div>
              <select
                value={item.ironing_status || 'ready'}
                onChange={(e) => onUpdate && onUpdate({ ...item, ironing_status: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.6rem',
                  borderRadius: '8px',
                  border: '1px solid #ECE7FE',
                  background: '#FFFFFF',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  color: '#1C1D21',
                  cursor: 'pointer'
                }}
              >
                <option value="ready">Ready to Wear</option>
                <option value="needs_ironing">Needs Ironing</option>
                <option value="being_ironed">Being Ironed</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div style={{ 
              display: 'flex', 
              gap: '0.75rem',
              marginTop: 'auto'
            }}>
              <button
                onClick={() => onDelete && onDelete(item.id)}
                style={{
                  flex: 1,
                  padding: '0.85rem 1.5rem',
                  borderRadius: '12px',
                  border: '1px solid #FFEBEE',
                  background: '#FFEBEE',
                  color: '#FF5252',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#FFCDD2'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#FFEBEE'}
              >
                Delete Item
              </button>
              
              <button
                onClick={onClose}
                style={{
                  flex: 1,
                  padding: '0.85rem 1.5rem',
                  borderRadius: '12px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #7C4DFF 0%, #6366F1 100%)',
                  color: '#FFFFFF',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(124, 77, 255, 0.3)',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}