#!/usr/bin/env node

const earthRadius = 6378137;

const circ = earthRadius * Math.PI * 2;

const zoom = process.argv[2];

const pixels = Math.pow(2, zoom) * 256;

const meterToPixel = circ / pixels;

const bboxPixels = process.argv
  .slice(3)
  .map(m => Number(m))
  .map(m => Math.round(m / meterToPixel));

const bbox = bboxPixels.map(m => m * meterToPixel);

console.log(`gdalwarp ... -te ${bbox.join(' ')} -ts ${bboxPixels[2] - bboxPixels[0]} ${bboxPixels[3] - bboxPixels[1]}`);
