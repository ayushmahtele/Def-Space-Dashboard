// Samples 2D points from rendered text so a particle system can assemble into a wordmark.
export function sampleTextPoints(text: string, count: number, opts?: { fontSize?: number; fontWeight?: string }): { x: number; y: number }[] {
  const fontSize = opts?.fontSize ?? 200;
  const fontWeight = opts?.fontWeight ?? "700";

  const canvas = document.createElement("canvas");
  const width = 1600;
  const height = 400;
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return [];

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.font = `${fontWeight} ${fontSize}px "Inter", sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, width / 2, height / 2);

  const { data } = ctx.getImageData(0, 0, width, height);
  const candidates: { x: number; y: number }[] = [];
  const stride = 2; // sample every Nth pixel for performance
  for (let y = 0; y < height; y += stride) {
    for (let x = 0; x < width; x += stride) {
      const alpha = data[(y * width + x) * 4 + 3];
      if (alpha > 128) {
        candidates.push({ x: (x - width / 2) / width, y: -(y - height / 2) / width });
      }
    }
  }

  if (candidates.length === 0) return [];

  const points: { x: number; y: number }[] = [];
  for (let i = 0; i < count; i++) {
    points.push(candidates[Math.floor(Math.random() * candidates.length)]);
  }
  return points;
}
