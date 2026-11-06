import React from 'react';

// Fallback high-resolution Pinterest-style cutouts if a stored item has no image
const DEFAULT_LOOK_IMAGES = {
  top: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=400&q=80',
  bottom: 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=400&q=80',
  footwear: 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=400&q=80',
  bag: 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=400&q=80',
  accessory: 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=400&q=80',
  outerwear: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=400&q=80'
};

export const checkIsOnePiece = (topObj) => {
  if (!topObj) return false;
  const title = (topObj.title || '').toLowerCase();
  const cat = (topObj.category || '').toLowerCase();
  const style = (topObj.style || '').toLowerCase();
  const keywords = ['dress', 'maxi', 'gown', 'jumpsuit', 'romper', 'one-piece', 'one piece', 'anarkali', 'saree', 'frock', 'derss'];
  return keywords.some(kw => title.includes(kw) || cat.includes(kw) || style.includes(kw));
};

export default function OutfitFlatLayBoard({ slotItems, title, height = 340 }) {
  // slotItems: { topObj, bottomObj, shoeObj, bagObj, accObj, outerObj, isBagExcluded, isAccExcluded }
  const isOnePiece = checkIsOnePiece(slotItems?.topObj);
  const hasBottom = !isOnePiece && slotItems?.bottomObj !== null && slotItems?.bottomObj !== undefined;

  const isBagExcluded = slotItems?.bagObj === null || slotItems?.isBagExcluded;
  const isAccExcluded = slotItems?.accObj === null || slotItems?.isAccExcluded;

  const topImg = slotItems?.topObj?.imageUrl || DEFAULT_LOOK_IMAGES.top;
  const bottomImg = slotItems?.bottomObj?.imageUrl || DEFAULT_LOOK_IMAGES.bottom;
  const shoeImg = slotItems?.shoeObj?.imageUrl || DEFAULT_LOOK_IMAGES.footwear;
  const bagImg = isBagExcluded ? null : (slotItems?.bagObj?.imageUrl || DEFAULT_LOOK_IMAGES.bag);
  const accImg = isAccExcluded ? null : (slotItems?.accObj?.imageUrl || DEFAULT_LOOK_IMAGES.accessory);

  return (
    <div 
      style={{
        position: 'relative',
        width: '100%',
        height: `${height}px`,
        background: 'linear-gradient(145deg, #F5F5F7 0%, #EAEAEA 100%)',
        borderRadius: '18px',
        overflow: 'hidden',
        border: '1px solid #E1E1E6',
        boxShadow: 'inset 0 0 20px rgba(0,0,0,0.02)',
        display: 'flex',
        padding: '12px',
        gap: '10px'
      }}
    >
      {/* Soft E-Commerce Background Overlay Grid */}
      <div 
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.15,
          backgroundImage: 'radial-gradient(#8E92A0 1px, transparent 1px)',
          backgroundSize: '16px 16px',
          pointerEvents: 'none'
        }}
      />

      {/* Left Column: Active Items (Footwear, Purse/Bag if allowed, Jewellery if allowed) */}
      <div style={{ width: '42%', display: 'flex', flexDirection: 'column', justifyContent: 'space-around', zIndex: 1 }}>
        {/* Accessory / Jewellery (Only rendered if NOT excluded) */}
        {!isAccExcluded && (
          <div style={{ position: 'relative', flex: 1, minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <img 
              src={accImg} 
              alt="Accessory / Jewellery"
              title={slotItems?.accObj?.title || 'Jewellery'}
              style={{
                maxHeight: '92%',
                maxWidth: '90%',
                objectFit: 'contain',
                filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.12))',
                transition: 'transform 0.25s ease'
              }}
            />
            <span style={{ position: 'absolute', bottom: '2px', left: '4px', fontSize: '0.65rem', background: 'rgba(255,255,255,0.85)', padding: '1px 5px', borderRadius: '4px', color: '#606470', fontWeight: 700 }}>
              💎 Jewellery
            </span>
          </div>
        )}

        {/* Purse / Bag (Only rendered if NOT excluded) */}
        {!isBagExcluded && (
          <div style={{ position: 'relative', flex: 1, minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <img 
              src={bagImg} 
              alt="Purse / Bag"
              title={slotItems?.bagObj?.title || 'Purse / Bag'}
              style={{
                maxHeight: '92%',
                maxWidth: '92%',
                objectFit: 'contain',
                filter: 'drop-shadow(0 8px 14px rgba(0,0,0,0.15))',
                transition: 'transform 0.25s ease'
              }}
            />
            <span style={{ position: 'absolute', bottom: '2px', left: '4px', fontSize: '0.65rem', background: 'rgba(255,255,255,0.85)', padding: '1px 5px', borderRadius: '4px', color: '#606470', fontWeight: 700 }}>
              👜 Purse / Bag
            </span>
          </div>
        )}

        {/* Footwear */}
        <div style={{ position: 'relative', flex: 1, minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <img 
            src={shoeImg} 
            alt="Footwear"
            title={slotItems?.shoeObj?.title || 'Footwear'}
            style={{
              maxHeight: '92%',
              maxWidth: '95%',
              objectFit: 'contain',
              filter: 'drop-shadow(0 8px 12px rgba(0,0,0,0.14))',
              transition: 'transform 0.25s ease'
            }}
          />
          <span style={{ position: 'absolute', bottom: '2px', left: '4px', fontSize: '0.65rem', background: 'rgba(255,255,255,0.85)', padding: '1px 5px', borderRadius: '4px', color: '#606470', fontWeight: 700 }}>
            👟 Footwear
          </span>
        </div>
      </div>

      {/* Right Column: Top / One-Piece Dress & Bottom Trousers (if applicable) */}
      <div style={{ width: '58%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', zIndex: 1 }}>
        {/* Top Right: One-Piece Dress (Full Height) OR Top Shirt (Half Height) */}
        <div style={{ position: 'relative', height: isOnePiece ? '100%' : '46%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <img 
            src={topImg} 
            alt={isOnePiece ? "One-Piece Dress" : "Top Garment"}
            title={slotItems?.topObj?.title || 'Top'}
            style={{
              maxHeight: '100%',
              maxWidth: '96%',
              objectFit: 'contain',
              filter: 'drop-shadow(0 10px 16px rgba(0,0,0,0.15))',
              transition: 'transform 0.25s ease'
            }}
          />
          <span style={{ position: 'absolute', top: '4px', right: '4px', fontSize: '0.65rem', background: 'rgba(255,255,255,0.9)', padding: '1px 6px', borderRadius: '4px', color: '#7C4DFF', fontWeight: 800 }}>
            {isOnePiece ? '👗 One-Piece Dress' : '👔 Top'}
          </span>
        </div>

        {/* Bottom Right: Pants / Skirt (Omitted for One-Piece Dress!) */}
        {hasBottom && (
          <div style={{ position: 'relative', height: '52%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <img 
              src={bottomImg} 
              alt="Bottom Trousers"
              title={slotItems?.bottomObj?.title || 'Bottom'}
              style={{
                maxHeight: '100%',
                maxWidth: '95%',
                objectFit: 'contain',
                filter: 'drop-shadow(0 10px 18px rgba(0,0,0,0.15))',
                transition: 'transform 0.25s ease'
              }}
            />
            <span style={{ position: 'absolute', bottom: '4px', right: '4px', fontSize: '0.65rem', background: 'rgba(255,255,255,0.85)', padding: '1px 5px', borderRadius: '4px', color: '#606470', fontWeight: 700 }}>
              👖 Bottom
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
