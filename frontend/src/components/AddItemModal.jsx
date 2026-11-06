import React, { useState, useRef, useEffect } from 'react';
import { X, Plus, Image as ImageIcon, Check } from 'lucide-react';

export default function AddItemModal({ isOpen, onClose, onSave }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('tops');
  const [color, setColor] = useState('Black');
  const [pattern, setPattern] = useState('Solid');
  const [style, setStyle] = useState('casual');
  const [season, setSeason] = useState('all-season');
  const [imageUrl, setImageUrl] = useState('');
  // Image input options: 'url' | 'file' | 'camera'
  const [imageInputMode, setImageInputMode] = useState('camera');
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [rawFile, setRawFile] = useState(null);
  const [cleanBgImage, setCleanBgImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [useGhostMannequin, setUseGhostMannequin] = useState(false);
  const [ghostStyle, setGhostStyle] = useState('hollow_man');
  const [isGeneratingGhost, setIsGeneratingGhost] = useState(false);
  const rotateImageCanvas = (degrees) => {
    if (!capturedImage) return;
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
      const rotatedDataUrl = canvas.toDataURL('image/png');
      setCapturedImage(rotatedDataUrl);
      setImageUrl(rotatedDataUrl);
      setCleanBgImage(rotatedDataUrl);
      
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], 'rotated-clothing.png', { type: 'image/png' });
          setRawFile(file);
        }
      }, 'image/png');
    };
    img.src = capturedImage;
  };

  const startCamera = async () => {
    setIsCameraActive(true);
    setImageInputMode('camera');
    setCapturedImage(null);
    setRawFile(null);
    setCleanBgImage(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(e => console.log("Play error:", e));
      }
    } catch (err) {
      console.warn("Camera permission denied or unavailable", err);
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const capturePhoto = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth || 640;
      canvas.height = videoRef.current.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/png');
      setCapturedImage(dataUrl);
      setImageUrl(dataUrl);
      stopCamera();
      
      canvas.toBlob(async (blob) => {
        if (blob) {
          const file = new File([blob], 'camera-photo.png', { type: 'image/png' });
          setRawFile(file);
          analyzeClothingImage(file);
        }
      }, 'image/png');
    } else {
      const mockCaptured = "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=600&q=80";
      setCapturedImage(mockCaptured);
      setImageUrl(mockCaptured);
      setIsCameraActive(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setRawFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setCapturedImage(reader.result);
        setImageUrl(reader.result);
        analyzeClothingImage(file);
      };
      reader.readAsDataURL(file);
    }
  };

  const applyGhostMannequin = async (fileToProcess, styleToUse = ghostStyle) => {
    if (!fileToProcess) return;
    setIsGeneratingGhost(true);
    try {
      const ghostFormData = new FormData();
      ghostFormData.append('clothing_image', fileToProcess);
      ghostFormData.append('style', styleToUse);
      
      console.log('Sending request to /api/ghost-mannequin...');
      const ghostResponse = await fetch('http://localhost:8000/api/ghost-mannequin', {
        method: 'POST',
        body: ghostFormData
      });
      
      const ghostData = await ghostResponse.json();
      console.log('Ghost mannequin result:', ghostData);
      
      if (ghostData.ghost_mannequin_image) {
        setCapturedImage(ghostData.ghost_mannequin_image);
        setImageUrl(ghostData.ghost_mannequin_image);
      }
    } catch (ghostError) {
      console.warn('Ghost mannequin endpoint error:', ghostError);
    } finally {
      setIsGeneratingGhost(false);
    }
  };

  const analyzeClothingImage = async (file) => {
    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (category) {
        formData.append('category', category);
      }

      console.log('Sending image to backend for processing...');
      const response = await fetch('http://localhost:8000/api/process-clothing', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      console.log('Backend response:', data);
      
      if (data.status === 'success') {
        if (data.processed_image) {
          setCleanBgImage(data.processed_image);
          setCapturedImage(data.processed_image);
          setImageUrl(data.processed_image);
        }

        if (useGhostMannequin) {
          await applyGhostMannequin(file);
        }
      }
    } catch (err) {
      console.warn('AI processing failed, using manual entry', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Re-run ghost mannequin when user toggles the checkbox or changes style
  const handleGhostToggle = (checked) => {
    setUseGhostMannequin(checked);
    if (checked) {
      if (rawFile) {
        applyGhostMannequin(rawFile, ghostStyle);
      } else if (cleanBgImage || capturedImage) {
        fetch(cleanBgImage || capturedImage)
          .then(res => res.blob())
          .then(blob => {
            const f = new File([blob], 'item.png', { type: 'image/png' });
            setRawFile(f);
            applyGhostMannequin(f, ghostStyle);
          });
      }
    } else {
      if (cleanBgImage) {
        setCapturedImage(cleanBgImage);
        setImageUrl(cleanBgImage);
      }
    }
  };

  const handleGhostStyleChange = (newStyle) => {
    setGhostStyle(newStyle);
    if (useGhostMannequin) {
      if (rawFile) {
        applyGhostMannequin(rawFile, newStyle);
      }
    }
  };

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleClose = () => {
    stopCamera();
    onClose();
  };

  const handleSave = (e) => {
    e.preventDefault();
    stopCamera();
    // Use the processed image (capturedImage contains the background-removed version)
    const finalImage = capturedImage || imageUrl || 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=400&q=80';
    console.log('Saving item with image:', finalImage.substring(0, 50) + '...');
    
    onSave({
      id: Date.now(),
      title: title || `${color} ${category.slice(0, -1)}`,
      category,
      color,
      pattern,
      style,
      season,
      usageCount: 0,
      lastUsed: 'Never',
      imageUrl: finalImage
    });
    handleClose();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 20, 30, 0.72)',
      backdropFilter: 'blur(12px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem'
    }}>
      <div 
        style={{ 
          maxWidth: '560px', 
          width: '100%', 
          padding: '2.25rem',
          background: '#FFFFFF',
          borderRadius: '28px',
          boxShadow: '0 24px 60px rgba(0, 0, 0, 0.25)',
          border: '1px solid #ECEBF5',
          animation: 'fadeInUp 0.25s ease-out forwards'
        }}
      >
        {/* Header section */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: 800, color: '#1C1D21', lineHeight: 1.2 }}>
              Add Cloth / Accessory
            </h3>
            <p style={{ color: '#8E92A0', fontSize: '0.88rem', marginTop: '0.25rem', fontWeight: 500 }}>
              {isGeneratingGhost ? '👻 Generating ghost mannequin effect...' : 
               isAnalyzing ? '✂️ Removing background...' : 
               (capturedImage ? '✅ Image ready! Enter item details manually below.' : 'Upload photo & enter item details manually below')}
            </p>

            {/* Ghost Mannequin Toggle */}
            <div style={{ 
              marginTop: '0.5rem',
              padding: '0.75rem',
              borderRadius: '10px',
              background: '#E3F2FD',
              border: '1px solid #BBDEFB',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <input
                  type="checkbox"
                  id="ghost-mannequin"
                  checked={useGhostMannequin}
                  onChange={(e) => handleGhostToggle(e.target.checked)}
                  style={{
                    width: '18px',
                    height: '18px',
                    accentColor: '#2196F3',
                    cursor: 'pointer'
                  }}
                />
                <label 
                  htmlFor="ghost-mannequin"
                  style={{ 
                    fontSize: '0.8rem', 
                    color: '#1C1D21', 
                    fontWeight: 600,
                    cursor: 'pointer',
                    margin: 0
                  }}
                >
                  👻 Ghost Mannequin Effect (industry standard e-commerce look)
                </label>
              </div>
              
              {useGhostMannequin && (
                <div style={{ 
                  marginLeft: '2.4rem',
                  display: 'flex', 
                  gap: '1rem',
                  alignItems: 'center'
                }}>
                  <span style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600 }}>
                    Style:
                  </span>
                  <select
                    value={ghostStyle}
                    onChange={(e) => handleGhostStyleChange(e.target.value)}
                    style={{
                      padding: '0.4rem 0.6rem',
                      borderRadius: '8px',
                      border: '1px solid #BBDEFB',
                      background: '#FFFFFF',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    <option value="hollow_man">Hollow Man (3D effect)</option>
                    <option value="flat_lay">Flat Lay (2D effect)</option>
                  </select>
                </div>
              )}
            </div>
          </div>
          <button 
            onClick={onClose} 
            style={{ 
              background: '#FAF9FE', 
              border: '1px solid #ECE7FE', 
              color: '#606470', 
              cursor: 'pointer',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
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

        {/* Form Body */}
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Item Name */}
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 800, color: '#1C1D21', display: 'block', marginBottom: '0.45rem', letterSpacing: '0.3px', textTransform: 'uppercase' }}>
              Item Name / Description
            </label>
            <input
              type="text"
              placeholder="e.g. Vintage Leather Trench Coat"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                width: '100%',
                padding: '0.85rem 1.1rem',
                borderRadius: '14px',
                border: '1.5px solid #ECEBF5',
                backgroundColor: '#FAF9FE',
                fontSize: '0.95rem',
                outline: 'none',
                color: '#1C1D21',
                fontFamily: 'var(--font-body)',
                transition: 'border 0.2s ease, background 0.2s ease'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#7C4DFF';
                e.target.style.backgroundColor = '#FFFFFF';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#ECEBF5';
                e.target.style.backgroundColor = '#FAF9FE';
              }}
            />
          </div>

          {/* Category & Color */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.1rem' }}>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 800, color: '#1C1D21', display: 'block', marginBottom: '0.45rem', letterSpacing: '0.3px', textTransform: 'uppercase' }}>Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.85rem 1rem',
                  borderRadius: '14px',
                  border: '1.5px solid #ECEBF5',
                  backgroundColor: '#FAF9FE',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  outline: 'none',
                  color: '#1C1D21',
                  cursor: 'pointer'
                }}
              >
                <option value="tops">Tops & Shirts</option>
                <option value="bottoms">Bottoms & Pants</option>
                <option value="one_piece">One-Piece & Dresses</option>
                <option value="outerwear">Outerwear</option>
                <option value="footwear">Footwear</option>
                <option value="bags">Bags & Purses</option>
                <option value="accessories">Accessories</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 800, color: '#1C1D21', display: 'block', marginBottom: '0.45rem', letterSpacing: '0.3px', textTransform: 'uppercase' }}>Color</label>
              <input
                type="text"
                placeholder="e.g. Black"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.85rem 1.1rem',
                  borderRadius: '14px',
                  border: '1.5px solid #ECEBF5',
                  backgroundColor: '#FAF9FE',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  outline: 'none',
                  color: '#1C1D21',
                  transition: 'border 0.2s ease, background 0.2s ease'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#7C4DFF';
                  e.target.style.backgroundColor = '#FFFFFF';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#ECEBF5';
                  e.target.style.backgroundColor = '#FAF9FE';
                }}
              />
            </div>
          </div>

          {/* Style & Season */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.1rem' }}>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 800, color: '#1C1D21', display: 'block', marginBottom: '0.45rem', letterSpacing: '0.3px', textTransform: 'uppercase' }}>Style Aesthetics</label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.85rem 1rem',
                  borderRadius: '14px',
                  border: '1.5px solid #ECEBF5',
                  backgroundColor: '#FAF9FE',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  outline: 'none',
                  color: '#1C1D21',
                  cursor: 'pointer'
                }}
              >
                <option value="casual">Casual</option>
                <option value="formal">Formal</option>
                <option value="smart-casual">Smart Casual</option>
                <option value="streetwear">Streetwear</option>
                <option value="ethnic">Ethnic</option>
                <option value="sporty">Sporty / Athleisure</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 800, color: '#1C1D21', display: 'block', marginBottom: '0.45rem', letterSpacing: '0.3px', textTransform: 'uppercase' }}>Season Suitability</label>
              <select
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.85rem 1rem',
                  borderRadius: '14px',
                  border: '1.5px solid #ECEBF5',
                  backgroundColor: '#FAF9FE',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  outline: 'none',
                  color: '#1C1D21',
                  cursor: 'pointer'
                }}
              >
                <option value="all-season">All Season</option>
                <option value="summer">Summer</option>
                <option value="winter">Winter</option>
                <option value="monsoon">Monsoon / Rainy</option>
              </select>
            </div>
          </div>

          {/* Item Photo Input Section (Camera / File Upload / URL) */}
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 800, color: '#1C1D21', display: 'block', marginBottom: '0.45rem', letterSpacing: '0.3px', textTransform: 'uppercase' }}>
              Item Photo (Camera / Upload)
            </label>

            {/* Selector Pills */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <button
                type="button"
                onClick={startCamera}
                style={{
                  flex: 1,
                  padding: '0.55rem',
                  borderRadius: '12px',
                  border: imageInputMode === 'camera' ? '1.5px solid #7C4DFF' : '1px solid #ECEBF5',
                  background: imageInputMode === 'camera' ? '#F0EBFF' : '#FAF9FE',
                  color: imageInputMode === 'camera' ? '#7C4DFF' : '#606470',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.4rem'
                }}
              >
                📷 Take Photo (Camera)
              </button>

              <label
                style={{
                  flex: 1,
                  padding: '0.55rem',
                  borderRadius: '12px',
                  border: imageInputMode === 'file' ? '1.5px solid #7C4DFF' : '1px solid #ECEBF5',
                  background: imageInputMode === 'file' ? '#F0EBFF' : '#FAF9FE',
                  color: imageInputMode === 'file' ? '#7C4DFF' : '#606470',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.4rem',
                  textAlign: 'center'
                }}
                onClick={() => setImageInputMode('file')}
              >
                📁 Upload Local File
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
              </label>

              <button
                type="button"
                onClick={() => { stopCamera(); setImageInputMode('url'); }}
                style={{
                  flex: 1,
                  padding: '0.55rem',
                  borderRadius: '12px',
                  border: imageInputMode === 'url' ? '1.5px solid #7C4DFF' : '1px solid #ECEBF5',
                  background: imageInputMode === 'url' ? '#F0EBFF' : '#FAF9FE',
                  color: imageInputMode === 'url' ? '#7C4DFF' : '#606470',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                🔗 Image URL
              </button>
            </div>

            {/* LIVE CAMERA VIEWPORT */}
            {imageInputMode === 'camera' && (
              <div style={{ borderRadius: '16px', overflow: 'hidden', border: '1.5px solid #ECE7FE', background: '#F8F9FC', position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '180px' }}>
                {capturedImage ? (
                  <div style={{ position: 'relative', width: '100%', height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.5rem', backgroundImage: 'radial-gradient(#E2E8F0 1px, transparent 1px)', backgroundSize: '12px 12px' }}>
                    <img src={capturedImage} alt="Captured preview" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.15))' }} />
                    <div style={{ position: 'absolute', bottom: '10px', right: '10px', display: 'flex', gap: '0.4rem' }}>
                      <button
                        type="button"
                        onClick={() => rotateImageCanvas(-90)}
                        title="Rotate 90° Left"
                        style={{ background: 'rgba(0,0,0,0.75)', color: '#FFF', border: 'none', padding: '0.4rem 0.75rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        ↺ Rotate Left
                      </button>
                      <button
                        type="button"
                        onClick={() => rotateImageCanvas(90)}
                        title="Rotate 90° Right"
                        style={{ background: 'rgba(0,0,0,0.75)', color: '#FFF', border: 'none', padding: '0.4rem 0.75rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        ↻ Rotate Right
                      </button>
                      <button
                        type="button"
                        onClick={startCamera}
                        style={{ background: 'rgba(0,0,0,0.75)', color: '#FFF', border: 'none', padding: '0.4rem 0.75rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        🔄 Retake
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1rem' }}>
                    <video
                      ref={(el) => {
                        videoRef.current = el;
                        if (el && streamRef.current) {
                          el.srcObject = streamRef.current;
                        }
                      }}
                      autoPlay
                      playsInline
                      muted
                      style={{ width: '100%', minHeight: '180px', maxHeight: '240px', borderRadius: '12px', objectFit: 'cover' }}
                    />
                    {!isCameraActive && (
                      <div style={{ color: '#A1A1AA', fontSize: '0.82rem', textAlign: 'center', margin: '1rem 0' }}>
                        Click below to capture item from camera
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={capturePhoto}
                      style={{
                        marginTop: '0.5rem',
                        background: 'linear-gradient(135deg, #7C4DFF 0%, #6366F1 100%)',
                        color: '#FFFFFF',
                        border: 'none',
                        padding: '0.6rem 1.4rem',
                        borderRadius: '999px',
                        fontWeight: 800,
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                        boxShadow: '0 4px 14px rgba(124, 77, 255, 0.4)'
                      }}
                    >
                      📸 Snap Item Photo
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* FILE UPLOAD PREVIEW */}
            {imageInputMode === 'file' && (
              <div style={{ border: '2px dashed #ECE7FE', borderRadius: '16px', padding: '1.25rem', textAlign: 'center', background: '#FAF9FE' }}>
                {capturedImage ? (
                  <div style={{ position: 'relative', width: '100%', height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundImage: 'radial-gradient(#E2E8F0 1px, transparent 1px)', backgroundSize: '12px 12px', borderRadius: '12px' }}>
                    <img src={capturedImage} alt="Uploaded preview" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.15))' }} />
                    <div style={{ position: 'absolute', bottom: '10px', right: '10px', display: 'flex', gap: '0.4rem' }}>
                      <button
                        type="button"
                        onClick={() => rotateImageCanvas(-90)}
                        style={{ background: 'rgba(0,0,0,0.75)', color: '#FFF', border: 'none', padding: '0.4rem 0.75rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        ↺ Rotate Left
                      </button>
                      <button
                        type="button"
                        onClick={() => rotateImageCanvas(90)}
                        style={{ background: 'rgba(0,0,0,0.75)', color: '#FFF', border: 'none', padding: '0.4rem 0.75rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        ↻ Rotate Right
                      </button>
                    </div>
                  </div>
                ) : (
                  <label style={{ cursor: 'pointer', display: 'block' }}>
                    <ImageIcon size={32} color="#7C4DFF" style={{ marginBottom: '0.4rem' }} />
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1C1D21' }}>Click to select photo from device</div>
                    <div style={{ fontSize: '0.75rem', color: '#8E92A0' }}>Supports JPG, PNG, WEBP</div>
                    <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>
                )}
              </div>
            )}

            {/* URL INPUT */}
            {imageInputMode === 'url' && (
              <div style={{ position: 'relative' }}>
                <input
                  type="url"
                  placeholder="https://..."
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.85rem 1.1rem 0.85rem 2.6rem',
                    borderRadius: '14px',
                    border: '1.5px solid #ECEBF5',
                    backgroundColor: '#FAF9FE',
                    fontSize: '0.9rem',
                    outline: 'none',
                    color: '#1C1D21'
                  }}
                />
                <ImageIcon size={17} color="#8E92A0" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              </div>
            )}
          </div>

          {/* Action Buttons matching screenshot layout */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.85rem', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #ECEBF5' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '0.85rem 1.6rem',
                borderRadius: '16px',
                border: 'none',
                backgroundColor: '#FAF9FE',
                color: '#7C4DFF',
                fontSize: '0.95rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F0EBFF'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#FAF9FE'}
            >
              Cancel
            </button>

            <button
              type="submit"
              style={{
                padding: '0.85rem 1.75rem',
                borderRadius: '16px',
                border: 'none',
                background: 'linear-gradient(135deg, #7C4DFF 0%, #6366F1 100%)',
                color: '#FFFFFF',
                fontSize: '0.95rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 6px 20px rgba(124, 77, 255, 0.35)',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
            >
              <Plus size={18} /> Save to Inventory
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}

