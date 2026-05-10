# Tearable 3D Cloth — Działający wzorzec Canvas 2D

## Problem

Próbowano implementacji "rozdzieranej" siatki 3D na Three.js z fizyką Verlet. Trzy próby zakończyły się porażką (corrupted geometria, tęczowe paski, NaN w pozycjach wierzchołków). Kodowanie bez planu w ciemno = fuszerka.

## Rozwiązanie

Canvas 2D + `globalCompositeOperation = 'destination-out'`. Najprostsze podejście zawsze wygrywa.

### Flow

1. `drawImage(bottomImage)` → dolna warstwa na canvasie
2. `drawImage(topImage)` → górna warstwa na wierzchu
3. Na `pointermove`: rysuj ścieżkę z `destination-out` → wycina dziury w górnej warstwie, odsłaniając dół
4. Postrzępione krawędzie: losowe przesunięcia ścieżki (`Math.random() * jitter`)

### Kod (esencja)

```javascript
function tear(x1, y1, x2, y2){
  ctx.save();
  ctx.globalCompositeOperation = 'destination-out';
  ctx.lineWidth = 16 + Math.random() * 4;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  const dx = x2 - x1, dy = y2 - y1;
  const dist = Math.hypot(dx, dy);
  const steps = Math.max(2, Math.floor(dist / 2));
  const nx = -dy / dist, ny = dx / dist;

  ctx.beginPath();
  ctx.moveTo(x1, y1);
  for(let i = 1; i <= steps; i++){
    const t = i / steps;
    const jx = (Math.random()-0.5) * Math.min(10, dist * 0.15);
    const jy = (Math.random()-0.5) * Math.min(10, dist * 0.15);
    ctx.lineTo(x1 + dx*t + nx*jx, y1 + dy*t + ny*jy);
  }
  ctx.stroke();
  ctx.restore();
}
```

## Dlaczego Three.js + Verlet zawiodło

1. Fizyka Verlet przy dużych prędkościach generuje NaN
2. PlaneGeometry z displacencją Z łatwo się korumpuje
3. Trzy iteracje kodowania w ciemno — każda gorsza od poprzedniej
4. Brak planu = brak zrozumienia co może pójść nie tak

## Dlaczego Canvas 2D działa

1. Zero fizyki — tylko rysowanie ścieżek
2. `destination-out` to natywna operacja kompozycji canvasu
3. Nie ma czego zepsuć — canvas nie korumpuje się
4. 3KB kodu vs 200KB Three.js + fizyka
