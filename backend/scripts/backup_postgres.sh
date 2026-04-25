#!/usr/bin/env bash
# 将当前 .env 指向的 PostgreSQL 整库备份为自定义格式（.dump），用于本机持久化与发布前基线。
# 用法：在仓库根目录有 .env 时，于 backend 目录执行：  bash scripts/backup_postgres.sh
set -euo pipefail

BACKEND="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$BACKEND/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ROOT/.env"
  set +a
elif [[ -f "$BACKEND/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$BACKEND/.env"
  set +a
fi

: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=duoduo}"
: "${POSTGRES_DB:=jiazheng}"
export PGPASSWORD="${POSTGRES_PASSWORD:-}"

OUT="$BACKEND/backups"
mkdir -p "$OUT"
STAMP=$(date +%Y%m%d_%H%M%S)
FILE="$OUT/jiazheng_${STAMP}.dump"

pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c -f "$FILE"

echo "已写入: $FILE"
echo "恢复示例（目标库须已存在且为空或你可接受覆盖策略）:"
echo "  pg_restore -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists -v \"$FILE\""
