# Deployment GlowMatch

```
Browser (kamera) ──HTTPS──▶ caddy (opsional, TLS otomatis)
                              │
                              ▼
                     web: nginx  ── file statis React (Vite build)
                              │  /api/*
                              ▼
                     api: FastAPI + PyTorch CPU  ◀── volume: models/undertone, models/season, models/hf_cache
```

| Image | Isi | Ukuran perkiraan |
|---|---|---|
| `glowmatch-api` | Python 3.12, PyTorch CPU, OpenCV, kode `app/` + `ml/`, detektor YuNet | ± 2 GB |
| `glowmatch-web` | nginx + hasil `npm run build` | ± 50 MB |

Artefak model **tidak** dimasukkan ke image (besar, sebagian berlisensi gated). Artefak di-mount dari `backend/models/`.

## Prasyarat

- Docker 24+ dengan Compose v2.
- Server: minimal 2 vCPU dan **4 GB RAM** untuk container API (direkomendasikan 4 vCPU / 6 GB). Ruang disk ± 6 GB.
- Publik: domain dan HTTPS. **Browser hanya mengizinkan kamera di HTTPS atau `localhost`.**
- Satu kali di mesin build: Python 3.12 untuk menyiapkan artefak model.

## 1. Siapkan artefak model (sekali)

```bash
cd backend
pip install -r requirements-dev.txt
```

**a. Unduh output notebook dari Kaggle.** Isi slug kernel Anda.

```bash
kaggle kernels output <user>/<kernel-undertone> -p ~/kaggle_out/undertone
kaggle kernels output <user>/<kernel-season> -p ~/kaggle_out/season
```

File yang dibutuhkan: `undertone_ensemble.joblib`, `convnext_ft_fold0-4.pth`, `E12_artifacts.joblib`, `ft_s42_f0-4.pt`.

**b. Samakan versi scikit-learn** dengan versi di Kaggle (`import sklearn; print(sklearn.__version__)` di notebook). Pin versinya di `backend/requirements.txt`. Pickle sklearn tidak dijamin kompatibel lintas versi.

**c. Kumpulkan, rapikan, dan verifikasi artefak.**

```bash
python scripts/extract_models.py all --src ~/kaggle_out/undertone ~/kaggle_out/season
```

Output harus diakhiri `[verify] SEMUA OK`. Perintah ini juga memeriksa bahwa bobot ensemble dan nama kelas cocok dengan angka di notebook, sehingga artefak dari run yang salah akan tertangkap.

**d. Unduh bobot pretrained** (DINOv2, DINOv3, SegFormer). Repo `facebook/dinov3-vits16-pretrain-lvd1689m` bersifat gated: setujui lisensinya di halaman Hugging Face dulu, lalu buat token baca.

```bash
HF_TOKEN=hf_xxx python scripts/extract_models.py fetch
```

Hasil akhirnya:

```
backend/models/
├── manifest.json                 (di-commit)
├── undertone/  undertone_bundle.joblib, convnext_ft_fold0-4.pth, ...
├── season/     season_bundle.joblib, ft_s42_f0-4.pt, ...
└── hf_cache/   hub/models--facebook--dinov3-..., models--jonathandinu--face-parsing, models--timm--...
```

## 2. Jalankan

```bash
cp .env.example .env          # opsional, lalu sesuaikan
docker compose up -d --build
docker compose logs -f api    # tunggu "model undertone dimuat" & "model season dimuat"
curl http://localhost:8080/api/health
```

Bila `"status": "ok"`, buka **http://localhost:8080**.

Bila `"status": "degraded"`, field `load_errors` menunjukkan file mana yang belum ada. Aplikasi tetap berjalan: pengecekan frame kamera bekerja, sedangkan `/api/analyze` mengembalikan 503.

## 3. Produksi dengan HTTPS

1. Arahkan DNS (record A/AAAA) domain ke server. Buka port 80 dan 443.
2. Di `.env`, isi `DOMAIN=glowmatch.example.com` dan `WEB_PORT=127.0.0.1:8080` (port web hanya untuk lokal; publik lewat Caddy).
3. Jalankan:

```bash
docker compose --profile tls up -d --build
```

Caddy mengambil sertifikat Let's Encrypt secara otomatis. Bila memakai load balancer atau CDN sendiri (Nginx, Cloudflare, ALB), lewati profil `tls` dan arahkan proxy ke `web:80` / port `WEB_PORT`. Timeout proxy minimal **180 detik** dan body maksimal **10 MB**.

## 4. Konfigurasi (`.env`)

| Variabel | Default | Keterangan |
|---|---|---|
| `WEB_PORT` | `8080` | Port host untuk web. `127.0.0.1:8080` = hanya lokal |
| `DOMAIN` | `localhost` | Domain untuk profil `tls` |
| `TORCH_THREADS` | `0` (otomatis) | Set ke jumlah core CPU |
| `MAX_FOLDS` | `0` (semua) | `1`–`2` = analisis lebih cepat, sedikit menyimpang dari hasil notebook |
| `WHITE_BALANCE` | `1` | Gray-World white balance (`0` untuk A/B test) |
| `WB_STRENGTH` | `1.0` | Kekuatan koreksi 0..1 |
| `MAX_UPLOAD_MB` | `8` | Batas ukuran foto |
| `API_MEMORY` | `4g` | Batas RAM container API |

CORS tidak perlu diatur karena web dan API satu origin lewat nginx. Bila frontend di-host terpisah, build web dengan `--build-arg VITE_API_URL=https://api.domain` dan set `GLOWMATCH_CORS_ORIGINS` di service `api`.

## 5. Operasional

- **Log:** `docker compose logs -f api`. Setiap analisis tercatat sebagai satu baris berisi `request_id`, musim, undertone, dan durasi.
- **Ganti model:** jalankan ulang langkah 1c, lalu `docker compose restart api`. Image tidak perlu di-build ulang.
- **Skala:**
  - Tiap container memuat seluruh model, sekitar 2–3 GB RAM.
  - Inferensi diserialisasi per container, jadi untuk lebih banyak pengguna, tambah replika `api` di belakang load balancer.
  - Pengecekan frame kamera (`/api/frame/check`) ringan dan tidak ikut antre.
- **GPU (opsional):**
  - Build dengan `docker compose build --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cu124 api`.
  - Set `GLOWMATCH_DEVICE=cuda`.
  - Tambahkan `deploy.resources.reservations.devices` (NVIDIA Container Toolkit).

## 6. Pengembangan lokal tanpa Docker

```bash
cd backend && python scripts/mock_server.py
```

Perintah di atas menjalankan API di :8000 dengan model berbobot acak (pipeline asli, hasil tidak bermakna). Untuk memakai model asli, ganti dengan `uvicorn app.main:app --reload`.

```bash
cd model-lab-Front-end && npm run dev
```

Frontend berjalan di http://localhost:5173, dan `/api` diteruskan ke :8000.

```bash
cd backend && python -m pytest
```

Perintah terakhir menjalankan test backend.

## 7. Troubleshooting

| Gejala | Penyebab / solusi |
|---|---|
| Kamera tidak terbuka, pesan "hanya bisa diakses lewat HTTPS" | Akses lewat IP/HTTP biasa. Pakai profil `tls`, atau buka lewat `localhost`. |
| "Akses kamera ditolak" | Izin kamera diblokir di browser. Izinkan di ikon gembok address bar, lalu muat ulang. |
| `/api/health` → `degraded`, `FileNotFoundError` | Artefak belum ada di `backend/models/<modul>/`. Ulangi langkah 1c. |
| `degraded`, error `huggingface` / `offline` | Bobot pretrained belum di-cache. Ulangi langkah 1d (`fetch`). |
| `InconsistentVersionWarning` / gagal unpickle | Versi scikit-learn berbeda dari Kaggle. Pin versi, lalu build ulang image. |
| `/api/analyze` 504 dari proxy | Timeout proxy di depan nginx terlalu pendek. Naikkan ke ≥ 180 detik, atau set `MAX_FOLDS=2`. |
| Container API di-restart (OOM) | Naikkan `API_MEMORY` (≥ 4g), atau set `MAX_FOLDS` lebih kecil. |
| Wajah sering tidak terdeteksi | Pastikan log/health menunjukkan `"detector": "yunet"`. Pencahayaan harus cukup dan wajah menghadap kamera. |
