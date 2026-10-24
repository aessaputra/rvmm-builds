#!/usr/bin/env bash
# Cek parse listing archive.org + pemilihan berkas di dl_archive (tanpa java).
set -u
cd /opt/data/profiles/coder/workspace/rvmm-builds || exit 1
source utils.sh

work=$(mktemp -d)
req() {
	printf 'REQ %s\n' "$1" >>"$work/log.req"
	if [ "$2" = - ]; then curl -sL -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0' "$1"; else : >"$2"; fi
}
merge_splits() { printf 'MERGE %s\n' "$1" >>"$work/log.merge"; }

check() { # pkg vers expected_file expect_merge
	local pkg=$1 vers=$2 expect=$3 expmerge=$4 url out rc got
	url="https://archive.org/download/km-apks/apks/$pkg"
	version_f=$vers
	out="$work/$pkg"
	: >"$work/log.req"; : >"$work/log.merge"
	if ! get_archive_resp "$url"; then echo "FAIL $pkg: listing kosong"; return 1; fi
	dl_archive "$url" "$vers" "$out" all; rc=$?
	got=$(sed 's;.*/;;' "$work/log.req" | tail -1)
	printf '%-28s rc=%s berkas=%s merge=%s\n' "$pkg" "$rc" "${got:-<tidak ada>}" \
		"$(grep -c MERGE "$work/log.merge")"
	[ "$rc" = 0 ] && [ "$got" = "$expect" ] || { echo "FAIL $pkg: harap '$expect'"; return 1; }
	[ "$(grep -c MERGE "$work/log.merge")" = "$expmerge" ] || { echo "FAIL $pkg: merge salah"; return 1; }
}

fail=0
check com.zhiliaoapp.musically 47.4.3 com.zhiliaoapp.musically-47.4.3-all.apk 0 || fail=1

rm -rf "$work"
[ "$fail" = 0 ] && echo "SEMUA CEK LULUS" || echo "ADA YANG GAGAL"
exit "$fail"
