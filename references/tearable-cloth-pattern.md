# Teable Cloth — Three.js Verlet Simulation

Interaktywna siatka z fizyką sprężynową — użytkownik rozrywa materiał by odsłonić warstwę pod spodem.

## Koncepcja
- Dwie warstwy PlaneGeometry — dolna statyczna, górna z fizyką
- Wierzchołki górnej warstwy połączone sprężynami (verlet integration)
- Myszka chwyta najbliższy wierzchołek i ciągnie
- Sprężyna pęka gdy dystans > TEAR_DIST
- Grawitacja ściąga rozdarte fragmenty

## Kluczowe parametry

```js
const W = 60, H = 80;           // gęstość siatki (W+1 × H+1 wierzchołków)
const REST_X = 0.07;            // spoczynkowa odległość X
const REST_Y = 0.07;            // spoczynkowa odległość Y
const TEAR_DIST = 0.18;         // próg zerwania sprężyny
const GRAVITY = -0.0008;        // grawitacja
const DAMPING = 0.985;          // tłumienie
const MOUSE_FORCE = 2.5;        // siła przyciągania do myszki
const MOUSE_RADIUS = 0.5;       // promień chwytania
```

## Technologie
- Three.js 0.160 przez CDN + import map
- ES modules, pojedynczy plik HTML
- Tekstury: dwie warstwy (top/bottom), górna na MeshStandardMaterial, dolna na MeshBasicMaterial
- Verlet integration: pozycje + prędkości, constraints iterowane 4× na klatkę
- Raycaster do wykrywania kliknięć

## Zastosowanie
- Efekt "zedrzyj by odkryć" — idealne do galerii, revealów, interaktywnych banerów
- Można użyć dla nerudek.com jako element galerii lub hero
- Działa na mobile (touch events)
