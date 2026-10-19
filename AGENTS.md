# AGENTS.md

Panduan untuk agen koding yang bekerja di repo ini. Dibuat mengikuti
[agents.md](https://agents.md/) dan disusun dari isi repo, bukan dari tebakan.

## Project Overview

Fork pribadi [`j-hc/revanced-magisk-module`](https://github.com/j-hc/revanced-magisk-module)
(`aessaputra/rvmm-builds`) yang membangun APK ReVanced/Morphe untuk 10 aplikasi
Android dan mengunggah hasilnya ke GitHub Releases.

Inti alurnya:

```
config.toml (10 tabel app)
  -> build.sh             baca config, loop per tabel
  -> utils.sh             unduh stok APK, ambil patch bundle + CLI, patch, align, sign
  -> build/               <app>-<brand>-v<versi>-<arch>.apk + zip modul
  -> GitHub Actions       release + update json + notifikasi Telegram
```

Semua logika ada di shell. `build.sh` adalah orkestrator tipis (175 baris);
`utils.sh` (909 baris) memuat seluruh fungsi kerja. Tidak ada bahasa lain, tidak
ada test suite, tidak ada package manager.

Komponen:

- `build.sh` — entry point. Validasi tool (`jq`, `java`, `zip`), baca
  `config.toml` via `bin/toml/tq-*`, loop tabel, panggil `build_rv` per app.
  Mode khusus: `./build.sh clean` (hapus `temp/`, `build/`, `build.md`) dan
  `./build.sh <cfg> --config-update` (cetak daftar app yang punya versi baru).
- `utils.sh` — fungsi kunci: `build_rv` (inti build), `get_prebuilts`
  (unduh/cache patch bundle + CLI), `patches_list` /
  `get_patch_last_supported_ver` (cari versi yang didukung patch),
  `dl_archive` / `dl_apkmirror` / `dl_uptodown` / `dl_direct` (sumber stok APK),
  `merge_splits` (APKM/XAPK -> APK), `patch_apk`, `check_sig`, `module_prop`.
- `config.toml` — satu tabel per app: `pkg-name`, `patches-source`,
  `cli-source`, `rv-brand`, `archive-dlurl`, `apkmirror-dlurl`, dll.
- `CONFIG.md` — dokumentasi semua kunci config beserta default.
- `module/` — template modul Magisk/KernelSU (`customize.sh`, `service.sh`,
  `module.prop` dihasilkan oleh `module_prop`).
- `bin/` — binary pendukung yang ikut ter-commit: `aapt2`, `htmlq`, `toml/tq`,
  `apksigner.jar`, `dexlib2.jar`, `paccer.jar`. Jangan hapus; CI memakainya.
- `sig.txt` — daftar sha256 sertifikat per paket. `check_sig` memakainya untuk
  memastikan stok APK asli (hanya untuk paket yang terdaftar).
- `ks.keystore`, `ks-p12.keystore` — kunci penandatanganan hasil build.

## Setup Commands

Repo ini dirancang untuk GitHub Actions (Ubuntu + JDK 21). Di mesin lokal,
`build.sh` butuh:

```bash
jq --version   # wajib, dipanggil di awal build.sh
java --version # wajib, JDK 21 (dipakai apksigner + morphe-cli)
zip --version  # wajib, untuk modul
unzip --version
git, curl, gh  # unduh prebuilt + release
```

Linux:

```bash
git clone https://github.com/aessaputra/rvmm-builds
cd rvmm-builds
./build.sh
```

Termux: `bash build-termux.sh`.

Host tanpa root (mis. container aarch64): `bin/aapt2`, `bin/htmlq`, `bin/toml`
sudah tersedia untuk arm64/arm. Java dan zip harus disediakan sendiri.

## Development Workflow

1. Ubah `config.toml` (bukan `build.sh`) untuk menambah app, mengganti sumber
   patch, atau mengubah sumber stok APK.
2. Validasi sintaks shell setelah menyentuh `build.sh` / `utils.sh`:
   `bash -n build.sh && bash -n utils.sh`.
3. Cek apakah ada versi baru tanpa membangun:
   `./build.sh config.toml --config-update` (butuh `build.md`; cetak daftar
   app yang perlu build, atau kosong bila tidak ada).
4. Build penuh lokal: `./build.sh` (menulis `temp/`, `build/`, `build.md`).
5. Bersihkan artefak: `./build.sh clean`.

Catatan: `parallel-jobs` dipaksa `1` di `build.sh` (komentar: multi-job rusak
di versi CLI terbaru). Jangan "memperbaiki" itu tanpa menguji CLI-nya.

## Testing Instructions

Tidak ada unit test. Verifikasi yang tersedia:

- `bash -n build.sh && bash -n utils.sh` — gate sintaks, jalankan setiap kali
  mengubah shell.
- `./build.sh config.toml --config-update` — jalur baca config + cek versi,
  tanpa patching. Cara termurah memastikan `config.toml` masih valid.
- Build satu app: set `enabled = false` pada tabel lain, lalu `./build.sh`.
  Hasilnya di `build/`; periksa `build.md` untuk log per app.
- Kegagalan yang wajar terlihat di `build.md`: `Could not find <app> in
  archive` berarti stok versi itu belum ada di arsip, bukan bug kode.

## Code Style

- Bash dengan `set -euo pipefail`; indentasi tab; nama fungsi `snake_case`.
- Pesan keluar lewat helper: `pr` (info), `epr` (error, juga `::error::` di
  Actions), `wpr` (warning), `abort` (hentikan semua job), `log` (tulis ke
  `build.md` yang jadi isi release).
- Jangan `echo` langsung untuk pesan status; CI mem-parse `::error::` /
  `::warning::`.
- Nilai config dibaca dengan `toml_get "$t" <kunci> || default`, bukan parsing
  manual.
- Nama file hasil build ditentukan `build_rv`; jangan mengubah polanya karena
  `*-update.json` dan workflow mengandalkan nama tersebut.

## Build and Deployment

- CI utama: `.github/workflows/ci.yml` — cron harian `0 16 * * *` +
  `workflow_dispatch`. Job `check` menjalankan `--config-update`; hanya kalau
  ada versi baru job `build` (`.github/workflows/build.yml`) dijalankan.
- `build.yml` memakai JDK 21 (zulu), checkout `origin/update` untuk `build.md`,
  membangun, membuat/meng-edit release bernomor (`NEXT_VER_CODE`), menulis
  `*-update.json` ke branch `update`, lalu mengirim notifikasi Telegram bila
  `TG_TOKEN` ada.
- Build berjalan otomatis. Jangan memicu `workflow_dispatch` manual kecuali
  diminta; cukup pastikan sumber stok APK tersedia.
- Output: `build/<app>-<brand>-v<versi>-<arch>.apk` dan
  `build/<module>-<brand>-v<versi>.zip`. Keduanya di-`.gitignore`.
- Stok APK diambil berurutan dari `DL_SRCS=("direct" "archive" "apkmirror")`.
  Mayoritas app memakai `archive-dlurl` ke item archive.org `km-apks` dengan
  pola `apks/<pkg>/<pkg>-<versi>-all.apk`. Bila file tidak ada di arsip, build
  jatuh ke `apkmirror-dlurl`.

## Menambah app baru

1. Tambah tabel di `config.toml`:

   ```toml
   [NamaApp]
   app-name = "Nama App"
   patches-source = "org/repo-patches"
   cli-source = "MorpheApp/morphe-cli"
   rv-brand = "Brand"
   build-mode = "apk"
   pkg-name = "com.contoh.app"
   apkmirror-dlurl = "https://www.apkmirror.com/apk/vendor/app/"
   archive-dlurl = "https://archive.org/download/km-apks/apks/com.contoh.app"
   ```

2. Pastikan stok APK versi yang didukung patch tersedia di arsip. Bila belum,
   unggah ke `km-apks` dengan nama `apks/<pkg>/<pkg>-<versi>-all.apk`
   (APKM/XAPK boleh, asal ekstensinya `.apkm` agar `merge_splits` jalan).
3. Jangan mengubah `build.sh` untuk app baru. Semua perilaku per app diatur
   kunci config (`CONFIG.md`).

## Pull Request Guidelines

- Format judul: `tipe: ringkasan` (`feat:`, `fix:`, `chore:`, `refactor:`),
  mengikuti riwayat commit yang ada.
- Sertakan `bash -n` pada file shell yang berubah dan hasil
  `--config-update` bila menyentuh `config.toml`.
- Jangan commit `build/`, `temp/`, `build.md`, `*.apk`, `*.zip` (sudah
  di-`.gitignore`).
- Jangan commit kunci keystore baru atau mengubah `sig.txt` tanpa alasan jelas.

## Security Considerations

- `ks.keystore` dan `ks-p12.keystore` adalah kunci tanda tangan. Jangan
  mengganti, memindahkan, atau mencetak isinya.
- `sig.txt` mengikat paket ke sha256 sertifikat. `check_sig` memakai
  `apksigner verify --print-certs`; jangan melemahkan pemeriksaan ini.
- Stok APK dari sumber pihak ketiga (arsip pribadi, APKMirror, APKPure) harus
  dianggap tidak tepercaya. Patch dan penandatanganan ulang adalah lapisan
  pertahanannya; jangan melewati `check_sig` untuk paket yang terdaftar.
- Rahasia CI: `GITHUB_TOKEN` (bawaan), `TG_TOKEN` (opsional, notifikasi).
  Jangan menulis token ke file yang ter-commit.

## Troubleshooting

- `Could not find <app> in archive` — versi yang dibutuhkan patch belum ada di
  `km-apks`; unggah stoknya, jangan ubah kode.
- `All builds failed` — semua tabel gagal; baca `build.md` dan cek tool
  (`jq`, `java`, `zip`).
- Metadata archive.org telat beberapa menit setelah upload; URL unduhan bisa
  404 sesaat. Tunggu, jangan unggah ulang.
- `Patching integrations checks failed` pada app non-ReVanced (mis. TikTok
  Hushfeed) adalah warning yang bisa diabaikan.
- `enable-update-checks` hanya berlaku untuk skema j-hc; untuk app lain flag
  ini diabaikan.
