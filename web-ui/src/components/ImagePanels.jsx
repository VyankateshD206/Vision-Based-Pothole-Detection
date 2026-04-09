import { useRef, useEffect } from 'react';

// Generates a simulated segmentation mask overlay on a canvas
export function MaskCanvas({ imageSrc, width = 400, height = 300 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imageSrc) return;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      // Simulate a pothole mask region (elliptical area in lower-center)
      const cx = img.width * 0.48;
      const cy = img.height * 0.62;
      const rx = img.width * 0.18;
      const ry = img.height * 0.14;

      // Semi-transparent red overlay
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(234, 88, 12, 0.45)';
      ctx.fill();
      ctx.restore();

      // Bounding box
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2.5;
      ctx.strokeRect(cx - rx - 8, cy - ry - 8, rx * 2 + 16, ry * 2 + 16);

      // Label
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(cx - rx - 8, cy - ry - 32, 90, 22);
      ctx.fillStyle = '#ffffff';
      ctx.font = '13px Inter, sans-serif';
      ctx.fillText('Pothole', cx - rx - 4, cy - ry - 15);

      // Mask area %
      ctx.fillStyle = 'rgba(0,0,0,0.55)';
      ctx.fillRect(8, img.height - 32, 120, 24);
      ctx.fillStyle = '#f59e0b';
      ctx.font = 'bold 12px Inter, sans-serif';
      ctx.fillText('Mask Area: 8.4%', 14, img.height - 14);
    };
    img.src = imageSrc;
  }, [imageSrc]);

  return <canvas ref={canvasRef} className="w-full h-auto rounded-xl" />;
}

// Generates a simulated depth heatmap overlay on a canvas
export function DepthCanvas({ imageSrc, width = 400, height = 300 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imageSrc) return;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      // Apply a pseudo depth-heatmap effect using gradients
      const imageData = ctx.getImageData(0, 0, img.width, img.height);
      const data = imageData.data;

      for (let i = 0; i < data.length; i += 4) {
        // Convert to grayscale as depth proxy
        const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        const t = gray / 255;

        // Inferno/plasma-like colormap
        let r, g, b;
        if (t < 0.25) {
          r = Math.floor(20 + t * 4 * 100);
          g = Math.floor(t * 4 * 20);
          b = Math.floor(80 + t * 4 * 120);
        } else if (t < 0.5) {
          const s = (t - 0.25) * 4;
          r = Math.floor(120 + s * 120);
          g = Math.floor(20 + s * 30);
          b = Math.floor(200 - s * 120);
        } else if (t < 0.75) {
          const s = (t - 0.5) * 4;
          r = Math.floor(240);
          g = Math.floor(50 + s * 140);
          b = Math.floor(80 - s * 60);
        } else {
          const s = (t - 0.75) * 4;
          r = Math.floor(240 + s * 15);
          g = Math.floor(190 + s * 65);
          b = Math.floor(20 + s * 40);
        }
        data[i] = Math.min(255, r);
        data[i + 1] = Math.min(255, g);
        data[i + 2] = Math.min(255, b);
      }
      ctx.putImageData(imageData, 0, 0);
    };
    img.src = imageSrc;
  }, [imageSrc]);

  return <canvas ref={canvasRef} className="w-full h-auto rounded-xl" />;
}

export function DepthLegend() {
  return (
    <div className="flex items-center gap-2 mt-2">
      <span className="text-[10px] text-slate-400">Shallow</span>
      <div
        className="flex-1 h-2.5 rounded-full"
        style={{
          background: 'linear-gradient(to right, #1e0540, #7b2d8e, #d4442d, #f0a030, #fcffa4)',
        }}
      />
      <span className="text-[10px] text-slate-400">Deep</span>
    </div>
  );
}
