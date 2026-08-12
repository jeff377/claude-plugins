#!/usr/bin/env bash
# 發版步驟 3：把各套件的 PublicAPI.Unshipped.txt 併入 Shipped.txt 並清空 Unshipped。
# 規範見本 skill 的 SKILL.md § 步驟 3。
#
# 用法：merge-public-api-shipped.sh <last_tag>
#
# 為什麼不能單純 append —— Unshipped 有兩種語意相反的條目：
#   Foo.Bar() -> void            新增的 API      → 加進 Shipped
#   *REMOVED*Foo.Bar() -> void   已移除的 API    → 從 Shipped 刪掉該行，標記本身不進 Shipped
# 把 *REMOVED* 直接 append 會讓 build 失敗於
#   RS0024: The shipped API file can't have removed members
#
# 兩個容易寫錯的細節：
#   1. 排序必須 LC_ALL=C，`~override` 這類項目才會排在正確位置。
#   2. `grep -Fxv -f` 對空的移除清單會濾掉全部，故以 `|| tail -n +2 "$s"` 兜底
#      （多數版本沒有 *REMOVED* 條目，走的是這條原路徑）。
#
# 開發期若已直接從 Shipped 刪掉該行、同時又在 Unshipped 標了 *REMOVED*，
# 剔除步驟會是 no-op，結果一樣正確 —— 兩種作法都吃得下。
set -uo pipefail

last_tag="${1:?用法: $0 <last_tag>}"

for u in $(git diff --name-only "$last_tag"..HEAD -- "**/PublicAPI.Unshipped.txt"); do
  s="${u%Unshipped.txt}Shipped.txt"
  body=$(tail -n +2 "$u" | grep -v '^[[:space:]]*$')
  [ -z "$body" ] && continue

  add=$(mktemp); del=$(mktemp); merged=$(mktemp)
  echo "$body" | grep -v '^\*REMOVED\*'     > "$add" || true
  echo "$body" | sed -n 's/^\*REMOVED\*//p' > "$del" || true

  { tail -n +2 "$s" | grep -Fxv -f "$del" 2>/dev/null || tail -n +2 "$s"; cat "$add"; } \
    | grep -v '^[[:space:]]*$' | LC_ALL=C sort -u > "$merged"

  { echo "#nullable enable"; cat "$merged"; } > "$s"
  echo "#nullable enable" > "$u"
  rm -f "$add" "$del" "$merged"
  echo "merged: $s"
done

echo
echo "完成後跑一次 clean Release build —— analyzer 通過即證明申報一致："
echo "  dotnet build <方案>.slnx -c Release --no-incremental"
