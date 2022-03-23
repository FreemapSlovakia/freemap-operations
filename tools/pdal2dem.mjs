#!/usr/bin/env zx

// laz projection must be EPSG:3857: ls -1 *.laz | parallel -j 24 pdal translate {} 3857/{} reprojection --filters.reprojection.out_srs="EPSG:3857"
// then run: ls -1 tile*.laz | parallel -j 24 ./script.mjs {}

const zoom = 20; // XYZ tile zoom level

const bufferSize = 8; // buffer to strip; TODO use bbox from LAStiling metadata

console.log("Processing:", argv._[1]);

const tile = argv._[1]; //'tile_2212800_6153600.laz';

const { metadata } = JSON.parse(await quiet($`pdal info --metadata ${tile}`));

// TODO use bbox from LAStiling; example: LAStiling (idx 2553, lvl 7, sub 0, bbox 2189600 6116800 2292000 6219200, buffer) (size 800 x 800, buffer 10)
// see https://github.com/LAStools/LAStools/blob/master/src/lasinfo.cpp#L4084

// const buf = Buffer.from(metadata.vlr_3.data, "base64");

// U32  level                                          4 bytes
// U32  level_index                                    4 bytes
// U32  implicit_levels + buffer bit + reversible bit  4 bytes
// F32  min_x                                          4 bytes
// F32  max_x                                          4 bytes
// F32  min_y                                          4 bytes
// F32  max_y                                          4 bytes

// console.log(metadata.minx, buf.readFloatLE(12));
// console.log(metadata.maxx, buf.readFloatLE(16));
// console.log(metadata.miny, buf.readFloatLE(20));
// console.log(metadata.maxy, buf.readFloatLE(24));

const px = (6378137 * Math.PI * 2) / 256 / Math.pow(2, zoom);

function align(value) {
  return Math.floor(value / px) * px;
}

const minX = align(metadata.minx + bufferSize);
const maxX = align(metadata.maxx - bufferSize);
const minY = align(metadata.miny + bufferSize);
const maxY = align(metadata.maxy - bufferSize);

const p = $`pdal pipeline -s`;

p.stdin.write(
  JSON.stringify([
    tile,
    {
      type: "filters.delaunay",
    },
    {
      type: "filters.faceraster",
      resolution: px,
      origin_x: minX,
      origin_y: minY,
      width: (maxX - minX) / px,
      height: (maxY - minY) / px,
    },
    {
      type: "writers.raster",
      filename: tile.replace(".laz", ".tif"),
      gdalopts: "COMPRESS=DEFLATE,PREDICTOR=3",
      data_type: "float32",
    },
  ])
);

p.stdin.end();

await p;
