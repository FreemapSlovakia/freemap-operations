// remove blank pngs
// find . -type f -size 334c -exec md5sum {} + | grep cd37744a985b79ed29bb6269e45da27f | awk '{print $2}' | xargs rm

// import * as path from "https://deno.land/std/path/mod.ts";

// const encoder = new TextEncoder();

// const dot = encoder.encode('.');
// const dash = encoder.encode('-');

const { spawn } = require('child_process');
const { promises: fs } = require('fs');
const path = require('path');

async function generateZoom(sourceZoom) {
  const base = '/home/martin/fm/freemap-mapnik/tiles/' + sourceZoom;

  const coords = new Set();

  for (const file of await fs.readdir(base)) {
    const name = path.join(base, file);

    console.log(name);

    const x = Number(file);

    for (const file1 of await fs.readdir(name)) {
      // const name1 = path.join(name, file1);

      const y = Number(file1.slice(0, -4));

      // if (y > 300000) {
      //   // console.log("mv", name1, `${name}/${y}.jpg`);
      //   await Deno.rename(name1, `${name}/${524287 - y}.jpg`);
      // } else {
      //   console.log("???", y);
      // }

      coords.add(`${Math.floor(x / 2)}/${Math.floor(y / 2)}`);
    }
  }

  console.log("Let's go...");

  let promises = [];

  for (const coord of [...coords].sort()) {
    console.log(coord);

    const [x, y] = coord.split('/');

    const xx = x * 2;
    const yy = y * 2;

    const parts = [
      `${base}/${xx}/${yy}.png`,
      `${base}/${xx}/${yy + 1}.png`,
      `${base}/${xx + 1}/${yy}.png`,
      `${base}/${xx + 1}/${yy + 1}.png`,
    ];

    const fn = async () => {
      // try {
      //   await Deno.stat(`tiles/${toZoom}/${x}/${y}.jpg`);

      //   Deno.stdout.write(dash);

      //   return;
      // } catch {
      //   // ignore
      // }

      // Deno.stdout.write(dot);

      await fs.mkdir(`tiles/${sourceZoom - 1}/${x}`, { recursive: true });

      for (let i = 0; i < 4; i++) {
        try {
          await fs.stat(parts[i]);
        } catch (err) {
          parts[i] = 'blank256.png';
        }
      }

      // console.log('>>>');

      const proc = spawn('convert', [
        '(',
        parts[0],
        parts[2],
        '+append',
        ')',
        '(',
        parts[1],
        parts[3],
        '+append',
        ')',
        '-append',
        '-resize',
        '256x256',
        `tiles/${sourceZoom - 1}/${x}/${y}.png`,
      ]);

      proc.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
      });

      proc.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
      });

      await new Promise((resolve) => {
        proc.on('close', () => {
          // console.log('<<<');
          resolve();
        });
      });
    };

    const p = fn();

    p.then(() => {
      p.done = true;
    });

    promises.push(p);

    if (promises.length > 24) {
      await Promise.race(promises);

      promises = promises.filter((p) => !p.done);
    }
  }

  await Promise.all(promises);
}

async function run() {
  for (let z = 17; z > 0; z--) {
    console.log('Zoom:', z - 1);

    await generateZoom(z);
  }
}

run().then(() => {
  console.log('DONE');
});
