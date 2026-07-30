import { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * Pure Three.js 3D scene — no React Three Fiber dependency.
 * Renders to a fixed full-screen div behind all page content.
 */
export function Scene3D() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    /* ── Renderer ──────────────────────────────────────── */
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    mount.appendChild(renderer.domElement);

    /* ── Scene + Camera ────────────────────────────────── */
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#010408');
    scene.fog = new THREE.Fog('#010408', 14, 32);

    const camera = new THREE.PerspectiveCamera(68, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.z = 10;

    /* ── Particle Cloud ─────────────────────────────────── */
    const COUNT = 2200;
    const pos = new Float32Array(COUNT * 3);
    const col = new Float32Array(COUNT * 3);

    for (let i = 0; i < COUNT; i++) {
      const r     = 2.5 + Math.random() * 9;
      const theta = Math.random() * Math.PI * 2;
      const phi   = Math.acos(2 * Math.random() - 1);
      pos[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
      const t        = Math.random();
      col[i * 3]     = t * 0.47;       // R  (0 → 0.47  cyan→violet)
      col[i * 3 + 1] = 1 - t * 0.63;  // G
      col[i * 3 + 2] = 1.0;            // B  always 1
    }

    const pgeo = new THREE.BufferGeometry();
    pgeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    pgeo.setAttribute('color',    new THREE.BufferAttribute(col, 3));

    const pmat = new THREE.PointsMaterial({
      size: 0.022,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const particles = new THREE.Points(pgeo, pmat);
    scene.add(particles);

    /* ── Floating Wireframe Shapes ──────────────────────── */
    const shapeDefs = [
      { geo: new THREE.IcosahedronGeometry(1.3, 1), color: '#00ffff', p: [-5.5,  2.5, -3], r: [0.18, 0.30, 0.06] },
      { geo: new THREE.TorusGeometry(1.1, 0.35, 8, 22),  color: '#bf5fff', p: [ 5.5, -2.0, -4], r: [0.25, 0.10, 0.20] },
      { geo: new THREE.OctahedronGeometry(1.0),           color: '#ff0080', p: [ 2.0,  4.0, -5], r: [0.30, 0.40, 0.12] },
      { geo: new THREE.IcosahedronGeometry(1.1, 1),       color: '#00ff41', p: [-3.5, -3.5, -6], r: [0.12, 0.22, 0.08] },
      { geo: new THREE.TorusGeometry(0.9, 0.3, 8, 20),   color: '#ffd700', p: [-1.0,  1.0, -8], r: [0.08, 0.15, 0.25] },
    ];

    const meshes: THREE.Mesh[] = [];
    const floatOffsets: number[] = [];

    shapeDefs.forEach(({ geo, color, p, r }) => {
      const mat  = new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: 0.22 });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(p[0], p[1], p[2]);
      scene.add(mesh);
      meshes.push(mesh);
      floatOffsets.push(Math.random() * Math.PI * 2);
    });

    /* ── Mouse tracking ─────────────────────────────────── */
    let mouseX = 0;
    let mouseY = 0;

    const onMouse = (e: MouseEvent) => {
      mouseX = (e.clientX / window.innerWidth  - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener('mousemove', onMouse);

    /* ── Resize ─────────────────────────────────────────── */
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', onResize);

    /* ── Render loop ────────────────────────────────────── */
    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      // Rotate particle cloud
      particles.rotation.y = t * 0.035;
      particles.rotation.x = t * 0.018;

      // Animate each shape
      meshes.forEach((mesh, i) => {
        const rs = shapeDefs[i].r;
        mesh.rotation.x += rs[0] * 0.01;
        mesh.rotation.y += rs[1] * 0.01;
        mesh.rotation.z += rs[2] * 0.01;
        // Sinusoidal float
        const baseY = shapeDefs[i].p[1];
        mesh.position.y = baseY + Math.sin(t * 0.5 + floatOffsets[i]) * 0.45;
      });

      // Smooth camera follow
      camera.position.x += (mouseX * 1.2 - camera.position.x) * 0.025;
      camera.position.y += (-mouseY * 0.7 - camera.position.y) * 0.025;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
    };
    animate();

    /* ── Cleanup ────────────────────────────────────────── */
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', onMouse);
      window.removeEventListener('resize', onResize);
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }}
    />
  );
}
