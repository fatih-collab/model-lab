import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { FiRotateCw } from 'react-icons/fi';
import logoTileUrl from '../assets/logo-tile.webp';

/**
 * Logo GlowMatch dalam 3D: ubin berbevel yang mengilap dengan empat bola kecil
 * (warna diambil dari empat lingkaran di logo) yang mengorbit. Seluruh geometri
 * dibuat lewat kode; satu-satunya aset adalah tekstur logo-tile.webp.
 *
 * Kerangka render (renderer transparan, RoomEnvironment, loop rAF, jeda saat tab
 * tersembunyi, prefers-reduced-motion, tombol putar native, tidak ada drag di
 * layar sentuh) mengikuti spesifikasi BloomSculpture.
 *
 * Props:
 *  - menuOpen       : logo bergeser memberi ruang untuk menu.
 *  - onHoverChange  : dipanggil true/false saat kursor masuk/keluar bentuk logo.
 *  - onTap          : ketukan jari pada logo (layar sentuh tidak punya hover).
 *  - controls       : node tambahan (mis. petunjuk atau tombol) di bawah logo.
 *  - showSpinButton : tampilkan tombol "Putar logo" (bawaan true). Logo tetap bisa diputar dengan diseret.
 */

const TAU = Math.PI * 2;
// Kecepatan awal putaran. Dengan peluruhan exp(-2.1 t), total putaran = v / 2.1 = tepat satu putaran penuh.
const DECAY = 2.1;
const SPIN_VELOCITY = TAU * DECAY;
const TILE_RADIUS = 0.2;
const TILE_SIZE = 3.1;

// Empat bola = empat lingkaran di logo. 'z' memilih fungsi untuk sumbu kedalaman.
const ORBS = [
  { color: 0xf69179, size: 0.21, speed: 0.45, phase: 0.7, rx: 2.15, ry: 1.7, rz: 0.9, z: 'sin' },
  { color: 0x96a8e0, size: 0.15, speed: 0.36, phase: 3.6, rx: 2.25, ry: 1.78, rz: 0.6, z: 'cos' },
  { color: 0xaa2870, size: 0.18, speed: 0.52, phase: 2.2, rx: 2.05, ry: 1.62, rz: 0.8, z: 'cos' },
  { color: 0x8a9460, size: 0.12, speed: 0.31, phase: 5.2, rx: 2.3, ry: 1.84, rz: 0.55, z: 'sin' },
];

function tileShape(radius) {
  const r = radius;
  const s = new THREE.Shape();
  s.moveTo(r, 0);
  s.lineTo(1 - r, 0);
  s.absarc(1 - r, r, r, -Math.PI / 2, 0, false);
  s.lineTo(1, 1 - r);
  s.absarc(1 - r, 1 - r, r, 0, Math.PI / 2, false);
  s.lineTo(r, 1);
  s.absarc(r, 1 - r, r, Math.PI / 2, Math.PI, false);
  s.lineTo(0, r);
  s.absarc(r, r, r, Math.PI, Math.PI * 1.5, false);
  return s;
}

export default function LogoSculpture({ menuOpen = false, onHoverChange, onTap, controls = null, showSpinButton = true }) {
  const hostRef = useRef(null);
  const spinRef = useRef(() => {});
  const syncOpenRef = useRef(() => {});
  const openTargetRef = useRef(0);
  const hoverCbRef = useRef(onHoverChange);
  const tapCbRef = useRef(onTap);
  const [available, setAvailable] = useState(true);
  const [spins, setSpins] = useState(0);

  // Callback terbaru disimpan di ref agar scene tidak dibuat ulang tiap render.
  useEffect(() => {
    hoverCbRef.current = onHoverChange;
    tapCbRef.current = onTap;
  }, [onHoverChange, onTap]);

  useEffect(() => {
    openTargetRef.current = menuOpen ? 1 : 0;
    syncOpenRef.current();
  }, [menuOpen]);

  useEffect(() => {
    const host = hostRef.current;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let motionReduced = reducedMotion.matches;

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
    } catch {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- fallback statis bila WebGL tidak bisa dibuat
      setAvailable(false);
      return undefined;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.7));
    renderer.setClearColor(0x000000, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1;
    renderer.domElement.setAttribute('aria-hidden', 'true');
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(33, 1, 0.1, 50);
    camera.position.set(0, 0.03, 8.2);

    const environment = new RoomEnvironment();
    const generator = new THREE.PMREMGenerator(renderer);
    const envTarget = generator.fromScene(environment, 0.04);
    scene.environment = envTarget.texture;
    environment.dispose();
    generator.dispose();

    const key = new THREE.DirectionalLight(0xfff2e0, 2.2);
    key.position.set(-3, 5, 6);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xffc8e0, 1.3);
    rim.position.set(4, 2, -2);
    scene.add(rim);
    scene.add(new THREE.AmbientLight(0xffffff, 0.45));

    // --- Ubin logo: badan berbevel + pelat depan bertekstur ---
    const shape = tileShape(TILE_RADIUS);
    const DEPTH = 0.12;
    const BEVEL_T = 0.05;
    const bodyGeometry = new THREE.ExtrudeGeometry(shape, {
      depth: DEPTH,
      bevelEnabled: true,
      bevelThickness: BEVEL_T,
      bevelSize: 0.045,
      bevelSegments: 8,
      curveSegments: 40,
    });
    bodyGeometry.translate(-0.5, -0.5, -DEPTH / 2);
    const bodyMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xfff3e0, roughness: 0.36, metalness: 0, envMapIntensity: 0.9,
      clearcoat: 0.8, clearcoatRoughness: 0.28, sheen: 0.3, sheenColor: new THREE.Color(0xffd6e8), sheenRoughness: 0.55,
    });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);

    const plateGeometry = new THREE.ShapeGeometry(shape, 40);
    plateGeometry.translate(-0.5, -0.5, DEPTH / 2 + BEVEL_T + 0.0015);
    let plate = null;
    let plateMaterial = null;
    let texture = null;

    // Kotak pemicu hover: sedikit lebih besar dari ubin, tidak dirender.
    const hitGeometry = new THREE.BoxGeometry(1.06, 1.06, 0.45);
    const hitProxy = new THREE.Mesh(hitGeometry, new THREE.MeshBasicMaterial({ visible: false }));

    const tile = new THREE.Group();
    tile.scale.setScalar(TILE_SIZE);
    tile.add(body, hitProxy);

    const sculpture = new THREE.Group();
    sculpture.add(tile);
    sculpture.rotation.set(-0.1, -0.2, 0.03);

    const stage = new THREE.Group();
    stage.add(sculpture);
    scene.add(stage);

    // --- Empat bola yang mengorbit ---
    const orbGeometry = new THREE.SphereGeometry(1, 40, 32);
    const orbs = ORBS.map((def) => {
      const material = new THREE.MeshPhysicalMaterial({
        color: def.color, roughness: 0.22, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.12, envMapIntensity: 0.9,
      });
      const mesh = new THREE.Mesh(orbGeometry, material);
      mesh.scale.setScalar(def.size);
      stage.add(mesh);
      return { def, mesh, material };
    });

    // --- State animasi ---
    let frame = 0;
    let elapsed = 0;
    let previous = 0;
    let drag = false;
    let lastX = 0;
    let lastY = 0;
    let movement = 0;
    let rot = 0; // yaw tambahan (putaran + drag); idle kembali ke kelipatan 2π agar logo menghadap depan
    let yawVel = 0;
    let pitchDrag = 0;
    let bounce = 0;
    let openAmt = openTargetRef.current;
    let visible = !document.hidden;
    let disposed = false;
    let hovering = false;
    const pointer = { x: 0, y: 0, inside: false };
    const raycaster = new THREE.Raycaster();
    const ndc = new THREE.Vector2();

    const setHover = (hit) => {
      if (hit === hovering) return;
      hovering = hit;
      host.classList.toggle('is-over', hit);
      if (hoverCbRef.current) hoverCbRef.current(hit);
    };
    const probe = () => {
      if (!pointer.inside || drag) return;
      ndc.set(pointer.x * 2 - 1, -(pointer.y * 2 - 1));
      raycaster.setFromCamera(ndc, camera);
      setHover(raycaster.intersectObject(hitProxy, false).length > 0);
    };

    const draw = (time) => {
      const narrow = camera.aspect < 1;
      orbs.forEach(({ def, mesh }) => {
        const a = time * def.speed + def.phase;
        mesh.position.set(Math.cos(a) * def.rx, Math.sin(a) * def.ry, (def.z === 'sin' ? Math.sin(a) : Math.cos(a)) * def.rz);
      });
      const sway = Math.sin(time * 0.5) * 0.3;
      sculpture.rotation.set(-0.1 + Math.sin(time * 0.4) * 0.07 + pitchDrag, -0.2 + sway + rot, 0.03 + Math.sin(time * 0.3) * 0.02);
      sculpture.position.y = Math.sin(time * 0.9) * 0.11;
      const pulse = 1 + Math.sin(bounce) * Math.min(bounce * 0.018, 0.07);
      sculpture.scale.setScalar(pulse);
      // Menu terbuka: di layar lebar logo bergeser ke kiri, di layar sempit naik dan sedikit mengecil.
      stage.position.set(narrow ? 0 : -1.45 * openAmt, narrow ? 1.05 * openAmt : 0, 0);
      stage.scale.setScalar(narrow ? 1 - 0.2 * openAmt : 1 - 0.14 * openAmt);
      renderer.render(scene, camera);
    };
    const renderStill = () => draw(elapsed);

    const resize = () => {
      const rect = host.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      renderer.setSize(rect.width, rect.height);
      camera.aspect = rect.width / rect.height;
      camera.position.z = camera.aspect < 1 ? 9.5 : 8.2;
      camera.updateProjectionMatrix();
      renderStill();
    };

    const tick = (now) => {
      frame = 0;
      if (disposed || !visible || motionReduced) return;
      const dt = Math.min((now - (previous || now)) / 1000, 0.045);
      previous = now;
      elapsed += dt;
      if (!drag) {
        rot += yawVel * dt;
        yawVel *= Math.exp(-dt * DECAY);
        if (Math.abs(yawVel) < 0.35) {
          const nearest = Math.round(rot / TAU) * TAU;
          rot += (nearest - rot) * Math.min(1, dt * 3);
        }
        pitchDrag *= Math.exp(-dt * 3);
      }
      bounce = Math.max(0, bounce - dt * 7);
      openAmt += (openTargetRef.current - openAmt) * Math.min(1, dt * 7);
      probe();
      draw(elapsed);
      host.dataset.rotation = rot.toFixed(3);
      frame = requestAnimationFrame(tick);
    };

    const syncPlayback = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      previous = 0;
      host.dataset.motion = motionReduced ? 'reduced' : 'animated';
      if (motionReduced || !visible) {
        openAmt = openTargetRef.current;
        renderStill();
      } else {
        frame = requestAnimationFrame(tick);
      }
    };
    syncOpenRef.current = () => {
      if (motionReduced || !visible) {
        openAmt = openTargetRef.current;
        renderStill();
      }
    };
    const onMotionChange = (event) => {
      motionReduced = event.matches;
      syncPlayback();
    };
    const onVisibility = () => {
      visible = !document.hidden;
      syncPlayback();
    };

    const spin = () => {
      if (motionReduced) {
        rot += Math.PI / 3;
        renderStill();
        host.dataset.rotation = rot.toFixed(3);
      } else {
        yawVel = SPIN_VELOCITY;
        bounce = 8;
      }
      setSpins((value) => value + 1);
    };
    spinRef.current = spin;

    const updatePointer = (event) => {
      const rect = host.getBoundingClientRect();
      pointer.x = (event.clientX - rect.left) / rect.width;
      pointer.y = (event.clientY - rect.top) / rect.height;
    };
    const down = (event) => {
      if (event.pointerType === 'touch') return; // layar sentuh: biarkan halaman scroll
      updatePointer(event);
      pointer.inside = true;
      probe();
      if (!hovering) return; // klik di luar bentuk logo diabaikan
      drag = true;
      movement = 0;
      lastX = event.clientX;
      lastY = event.clientY;
      host.setPointerCapture(event.pointerId);
      host.classList.add('is-dragging');
    };
    const move = (event) => {
      if (event.pointerType === 'touch') return;
      updatePointer(event);
      pointer.inside = true;
      if (!drag) {
        probe();
        return;
      }
      const dx = event.clientX - lastX;
      const dy = event.clientY - lastY;
      movement += Math.abs(dx) + Math.abs(dy);
      rot += dx * 0.012;
      pitchDrag = Math.max(-0.5, Math.min(0.5, pitchDrag + dy * 0.006));
      yawVel = Math.max(-14, Math.min(14, dx * 0.75));
      lastX = event.clientX;
      lastY = event.clientY;
      if (motionReduced || !visible) renderStill();
    };
    const up = () => {
      if (!drag) return;
      drag = false;
      host.classList.remove('is-dragging');
      if (movement < 6) spin();
      else if (motionReduced) renderStill();
    };
    const leave = (event) => {
      if (event.pointerType === 'touch') return;
      pointer.inside = false;
      if (!drag) setHover(false);
    };
    const tap = (event) => {
      // Ketukan jari: hover tidak ada di layar sentuh, jadi ketukan pada logo membuka/menutup menu dan memutarnya.
      if (event.pointerType !== 'touch') return;
      updatePointer(event);
      ndc.set(pointer.x * 2 - 1, -(pointer.y * 2 - 1));
      raycaster.setFromCamera(ndc, camera);
      if (raycaster.intersectObject(hitProxy, false).length === 0) return;
      if (tapCbRef.current) tapCbRef.current();
      spin();
    };

    // Tekstur logo dimuat async; pelat depan dibuat setelah siap.
    new THREE.TextureLoader().load(logoTileUrl, (loaded) => {
      if (disposed) {
        loaded.dispose();
        return;
      }
      texture = loaded;
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      // Warna logo dipertahankan: tekstur masuk lewat emissive dan tidak melewati tone mapping,
      // sementara clearcoat/env tetap memberi kilap di atasnya.
      plateMaterial = new THREE.MeshPhysicalMaterial({
        color: 0x000000, emissive: 0xffffff, emissiveMap: texture, roughness: 0.3, metalness: 0,
        clearcoat: 1, clearcoatRoughness: 0.12, envMapIntensity: 0.75, toneMapped: false,
      });
      plate = new THREE.Mesh(plateGeometry, plateMaterial);
      tile.add(plate);
      renderStill();
    });

    const observer = new ResizeObserver(resize);
    observer.observe(host);
    host.addEventListener('pointerdown', down);
    host.addEventListener('pointermove', move);
    host.addEventListener('pointerup', up);
    host.addEventListener('pointercancel', up);
    host.addEventListener('pointerleave', leave);
    host.addEventListener('click', tap);
    reducedMotion.addEventListener('change', onMotionChange);
    document.addEventListener('visibilitychange', onVisibility);
    syncPlayback();

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      host.removeEventListener('pointerdown', down);
      host.removeEventListener('pointermove', move);
      host.removeEventListener('pointerup', up);
      host.removeEventListener('pointercancel', up);
      host.removeEventListener('pointerleave', leave);
      host.removeEventListener('click', tap);
      reducedMotion.removeEventListener('change', onMotionChange);
      document.removeEventListener('visibilitychange', onVisibility);
      bodyGeometry.dispose();
      plateGeometry.dispose();
      hitGeometry.dispose();
      orbGeometry.dispose();
      bodyMaterial.dispose();
      hitProxy.material.dispose();
      if (plateMaterial) plateMaterial.dispose();
      if (texture) texture.dispose();
      orbs.forEach(({ material }) => material.dispose());
      envTarget.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
      host.classList.remove('is-over', 'is-dragging');
      spinRef.current = () => {};
      syncOpenRef.current = () => {};
      if (hovering && hoverCbRef.current) hoverCbRef.current(false);
    };
  }, []);

  return (
    <div className="sculpture-wrap">
      <div className="sculpture-shadow" aria-hidden="true" />
      <div
        ref={hostRef}
        className="sculpture-canvas"
        role="img"
        aria-label="Logo GlowMatch tiga dimensi dengan empat bola warna yang mengorbit"
      >
        {!available && (
          <img
            className="fallback-logo"
            src={logoTileUrl}
            alt=""
            width="330"
            height="330"
            onPointerEnter={(e) => e.pointerType !== 'touch' && hoverCbRef.current && hoverCbRef.current(true)}
            onPointerLeave={(e) => e.pointerType !== 'touch' && hoverCbRef.current && hoverCbRef.current(false)}
            onClick={() => tapCbRef.current && tapCbRef.current()}
          />
        )}
      </div>
      <div className="play-controls">
        <div className="play-row">
          {available && showSpinButton && (
            <button type="button" className="spin-button" onClick={() => spinRef.current()} aria-label="Putar logo GlowMatch">
              <FiRotateCw aria-hidden="true" size={14} />
              Putar logo
            </button>
          )}
          {controls}
        </div>
      </div>
      <span className="sr-only" aria-live="polite">{spins > 0 ? `Logo diputar ${spins} kali.` : ''}</span>
    </div>
  );
}
