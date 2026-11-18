#!/bin/sh -e
# Build packages/*.zip and catalog.json for the public app-store seed repo.
# Usage: ./tools/app-store-seed/pack.sh
# Optional: STORE_BASE=https://raw.githubusercontent.com/OWNER/REPO/main ./pack.sh

HERE="$(cd "$(dirname "$0")" && pwd)"
# Default: GitHub Contents API (works when raw.githubusercontent.com is blocked).
REPO="${STORE_REPO:-fary99/app_test}"
REF="${STORE_REF:-main}"
BASE="${STORE_BASE:-https://api.github.com/repos/$REPO/contents}"
PKG="$HERE/packages"
mkdir -p "$PKG"
rm -f "$PKG"/*.zip

apps_json=""
first=1
for app in "$HERE"/apps/*/; do
	[ -d "$app" ] || continue
	[ -f "$app/manifest.json" ] || continue
	id=$(node -p 'JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).id' "$app/manifest.json")
	ver=$(node -p 'JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).version' "$app/manifest.json")
	name_zh=$(node -p 'const n=JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).name; n["zh-CN"]||Object.values(n)[0]' "$app/manifest.json")
	name_en=$(node -p 'const n=JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).name; n["en-US"]||Object.values(n)[0]' "$app/manifest.json")
	zipname="${id}-${ver}.zip"
	(
		cd "$app"
		# zip contents are the project root (manifest.json at top level)
		zip -qr "$PKG/$zipname" . -x '*.pyc' -x '*__pycache__*' -x '*.git*'
	)
	icon_url="$BASE/apps/$id/icon.svg?ref=$REF"
	dl="$BASE/packages/$zipname?ref=$REF"
	entry=$(printf '{"id":"%s","name":{"zh-CN":"%s","en-US":"%s"},"summary":{"zh-CN":"示例应用 %s","en-US":"Sample app %s"},"version":"%s","min_sdk":"0.3.0","icon":"%s","download":"%s"}' \
		"$id" "$name_zh" "$name_en" "$id" "$id" "$ver" "$icon_url" "$dl")
	if [ "$first" = 1 ]; then
		apps_json="$entry"
		first=0
	else
		apps_json="$apps_json,$entry"
	fi
	echo "packed $zipname"
done

cat > "$HERE/catalog.json" <<EOF
{
  "schemaVersion": 1,
  "apps": [$apps_json]
}
EOF
node -e 'const fs=require("fs");const p=process.argv[1];fs.writeFileSync(p,JSON.stringify(JSON.parse(fs.readFileSync(p,"utf8")),null,2)+"\n")' "$HERE/catalog.json"
echo "wrote $HERE/catalog.json"
ls -la "$PKG"
