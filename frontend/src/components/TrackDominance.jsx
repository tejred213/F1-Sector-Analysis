import { useRef, useEffect, useState, useCallback } from 'react';

export default function TrackDominance({ data }) {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);

    // Zoom & pan state
    const [zoom, setZoom] = useState(1);
    const [offset, setOffset] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const panStart = useRef({ x: 0, y: 0 });
    const panOffset = useRef({ x: 0, y: 0 });

    const resetView = () => { setZoom(1); setOffset({ x: 0, y: 0 }); };

    // Wheel zoom handler
    const handleWheel = useCallback((e) => {
        e.preventDefault();
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
        const newZoom = Math.min(8, Math.max(0.5, zoom * zoomFactor));

        // Zoom toward mouse position
        const scale = newZoom / zoom;
        const newOffsetX = mouseX - scale * (mouseX - offset.x);
        const newOffsetY = mouseY - scale * (mouseY - offset.y);

        setZoom(newZoom);
        setOffset({ x: newOffsetX, y: newOffsetY });
    }, [zoom, offset]);

    // Pan handlers
    const handleMouseDown = (e) => {
        if (e.button !== 0) return;
        setIsPanning(true);
        panStart.current = { x: e.clientX, y: e.clientY };
        panOffset.current = { ...offset };
    };

    const handleMouseMove = useCallback((e) => {
        if (!isPanning) return;
        const dx = e.clientX - panStart.current.x;
        const dy = e.clientY - panStart.current.y;
        setOffset({ x: panOffset.current.x + dx, y: panOffset.current.y + dy });
    }, [isPanning]);

    const handleMouseUp = () => setIsPanning(false);

    useEffect(() => {
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [handleMouseMove]);

    // Attach wheel handler with passive: false
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        canvas.addEventListener('wheel', handleWheel, { passive: false });
        return () => canvas.removeEventListener('wheel', handleWheel);
    }, [handleWheel]);

    // Draw the track
    useEffect(() => {
        if (!data || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        const W = rect.width;
        const H = rect.height;

        ctx.clearRect(0, 0, W, H);

        const { x, y, dominance, color1, color2, corners } = data;

        // Base transform (fit track into canvas)
        const pad = 50;
        const minX = Math.min(...x);
        const maxX = Math.max(...x);
        const minY = Math.min(...y);
        const maxY = Math.max(...y);
        const rangeX = maxX - minX || 1;
        const rangeY = maxY - minY || 1;

        const scaleX = (W - pad * 2) / rangeX;
        const scaleY = (H - pad * 2) / rangeY;
        const baseScale = Math.min(scaleX, scaleY);

        const baseOffsetX = pad + ((W - pad * 2) - rangeX * baseScale) / 2;
        const baseOffsetY = pad + ((H - pad * 2) - rangeY * baseScale) / 2;

        // Apply zoom + pan transform
        const tx = (v) => offset.x + zoom * (baseOffsetX + (v - minX) * baseScale);
        const ty = (v) => offset.y + zoom * (H - (baseOffsetY + (v - minY) * baseScale));

        // Background track (shadow)
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.lineWidth = 14 * zoom;
        ctx.strokeStyle = '#1A1A1A';
        ctx.beginPath();
        ctx.moveTo(tx(x[0]), ty(y[0]));
        for (let i = 1; i < x.length; i++) {
            ctx.lineTo(tx(x[i]), ty(y[i]));
        }
        ctx.stroke();

        // Outer glow
        ctx.lineWidth = 10 * zoom;
        ctx.strokeStyle = 'rgba(255,255,255,0.03)';
        ctx.beginPath();
        ctx.moveTo(tx(x[0]), ty(y[0]));
        for (let i = 1; i < x.length; i++) {
            ctx.lineTo(tx(x[i]), ty(y[i]));
        }
        ctx.stroke();

        // Coloured dominance segments
        ctx.lineWidth = Math.max(3, 5 * zoom);
        ctx.lineCap = 'round';
        for (let i = 0; i < x.length - 1; i++) {
            const segColor = dominance[i] === 1 ? color1 : color2;
            ctx.strokeStyle = segColor;
            ctx.shadowColor = segColor;
            ctx.shadowBlur = 4 * zoom;
            ctx.beginPath();
            ctx.moveTo(tx(x[i]), ty(y[i]));
            ctx.lineTo(tx(x[i + 1]), ty(y[i + 1]));
            ctx.stroke();
        }
        ctx.shadowBlur = 0;

        // Start/Finish marker
        const sfSize = Math.max(4, 7 * zoom);
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(tx(x[0]), ty(y[0]), sfSize, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(tx(x[0]), ty(y[0]), sfSize + 4, 0, Math.PI * 2);
        ctx.stroke();

        const fontSize = Math.max(9, 11 * zoom);
        ctx.font = `700 ${fontSize}px 'Kanit', sans-serif`;
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText('START / FINISH', tx(x[0]) + sfSize + 8, ty(y[0]) - sfSize - 2);

        // Sector boundary markers
        const n = x.length;
        const sectorLabels = ['S1 | S2', 'S2 | S3'];
        [Math.floor(n / 3), Math.floor(2 * n / 3)].forEach((idx, si) => {
            ctx.save();
            ctx.translate(tx(x[idx]), ty(y[idx]));
            ctx.rotate(Math.PI / 4);
            ctx.fillStyle = '#E10600';
            const diamondSize = Math.max(3, 5 * zoom);
            ctx.fillRect(-diamondSize, -diamondSize, diamondSize * 2, diamondSize * 2);
            ctx.restore();

            ctx.fillStyle = '#888';
            ctx.font = `600 ${Math.max(8, 10 * zoom)}px 'Kanit', sans-serif`;
            ctx.fillText(sectorLabels[si], tx(x[idx]) + diamondSize + 8, ty(y[idx]) + 4);
        });

        // Official turn numbers from circuit data
        if (corners && corners.length > 0) {
            const turnFontSize = Math.max(8, 10 * zoom);
            const radius = Math.max(9, 12 * zoom);

            corners.forEach((corner) => {
                const cx = tx(corner.x);
                const cy = ty(corner.y);

                // Dark circle background
                ctx.beginPath();
                ctx.arc(cx, cy, radius, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(0,0,0,0.85)';
                ctx.fill();
                ctx.strokeStyle = 'rgba(255,255,255,0.35)';
                ctx.lineWidth = 1.5;
                ctx.stroke();

                // Turn number text
                ctx.fillStyle = '#FFFFFF';
                ctx.font = `700 ${turnFontSize}px 'Kanit', sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`${corner.number}`, cx, cy + 1);
            });

            // Reset text alignment
            ctx.textAlign = 'start';
            ctx.textBaseline = 'alphabetic';
        }

    }, [data, zoom, offset]);

    if (!data) return null;

    return (
        <div className="track-section fade-in stagger-3">
            <div className="track-container" ref={containerRef}>
                <div className="track-toolbar">
                    <button className="track-toolbar__btn" onClick={() => setZoom(z => Math.min(8, z * 1.3))} title="Zoom In">+</button>
                    <button className="track-toolbar__btn" onClick={() => setZoom(z => Math.max(0.5, z / 1.3))} title="Zoom Out">−</button>
                    <button className="track-toolbar__btn" onClick={resetView} title="Reset View">⟲</button>
                    <span className="track-toolbar__zoom">{Math.round(zoom * 100)}%</span>
                </div>
                <canvas
                    ref={canvasRef}
                    className="track-canvas"
                    onMouseDown={handleMouseDown}
                    style={{ cursor: isPanning ? 'grabbing' : 'grab' }}
                />
                <div className="track-legend">
                    <div className="track-legend__item">
                        <div className="track-legend__swatch" style={{ background: data.color1, boxShadow: `0 0 8px ${data.color1}` }} />
                        <span>{data.driver1}</span>
                        <span style={{ color: '#888', fontWeight: 400 }}>({data.d1_pct}%)</span>
                    </div>
                    <div className="track-legend__item">
                        <div className="track-legend__swatch" style={{ background: data.color2, boxShadow: `0 0 8px ${data.color2}` }} />
                        <span>{data.driver2}</span>
                        <span style={{ color: '#888', fontWeight: 400 }}>({data.d2_pct}%)</span>
                    </div>
                </div>
                <div className="track-hint">Scroll to zoom • Drag to pan</div>
            </div>
        </div>
    );
}
