#!/usr/bin/env bash
# 検証用の Neo4j をローカルに立てる。1,050ノードなのでヒープは小さくてよい。
set -euo pipefail
PASS="${NEO4J_PASSWORD:?NEO4J_PASSWORD を設定してください}"
docker rm -f kg-neo4j >/dev/null 2>&1 || true
docker run -d --name kg-neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH="neo4j/${PASS}" \
  -e NEO4J_server_memory_heap_initial__size=512m \
  -e NEO4J_server_memory_heap_max__size=512m \
  -e NEO4J_server_memory_pagecache_size=256m \
  neo4j:5-community >/dev/null
echo -n "起動待ち"
until (exec 3<>/dev/tcp/localhost/7687) 2>/dev/null; do echo -n .; sleep 3; done
echo " OK  (ブラウザ: http://localhost:7474)"
