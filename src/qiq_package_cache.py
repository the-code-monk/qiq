import argparse
import time
import os
import sqlite3
import json
from pathlib import Path
import threading
from typing import Optional

# Project Imports
import qiq_config as C
import qiq_utils as utils

CACHE_DB = "qiq_pypi_cache.sqlite3"

class QiQ_Package_Cache:
    """SQLite-backed key-value cache for PyPI metadata.

    Two tables, because the two kinds of data have different freshness rules:
      - `versions`: which releases exist for a package name. This CAN go
        stale -- a new release can appear at any time -- so it's subject to
        a TTL and to --refresh.
      - `requires_dist`: the dependency specifiers declared by one exact,
        already-published (name, version). This is immutable once published
        (short of a yank), so it's cached forever with no staleness check.

    Every read/write goes through `self._lock`, since sqlite3 connections
    aren't safe to share across threads without one. The lock only ever
    guards the DB call itself (a few ms), never a network request, so this
    doesn't undo the parallelism PyPIClient relies on.
    """

    DEFAULT_TTL = 24 * 3600.0  # seconds

    def __init__(self, ttl: float = DEFAULT_TTL, force_refresh: bool = False):
        python_path = utils.get_python_path()
        db_path = Path(os.path.join(python_path, C.QIQ_DIR, C.QIQ_CONFIG_DIR, CACHE_DB))
        self.ttl = ttl
        self.force_refresh = force_refresh
        self._run_start = time.time()
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        with self._lock, self._conn:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS versions (
                    name TEXT PRIMARY KEY,
                    versions_json TEXT NOT NULL,
                    fetched_at REAL NOT NULL
                )"""
            )
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS requires_dist (
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    requires_dist_json TEXT NOT NULL,
                    PRIMARY KEY (name, version)
                )"""
            )
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS projects (
                    name TEXT PRIMARY KEY
                )"""
            )
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS packages (
                    name TEXT PRIMARY KEY
                )"""
            )

    def is_stale(self, name: str) -> bool:
        """Whether `name`'s version list needs a network refresh.

        Anything already fetched during *this* run (fetched_at >= run start)
        is never re-considered stale for the rest of the run, regardless of
        --ttl or --refresh. Without that guard, a low --ttl (or --refresh
        without it) would refetch the same package every single time it's
        looked up within one resolution -- e.g. once per backtrack attempt --
        since "now minus fetched_at" keeps growing past the threshold even a
        few milliseconds later. TTL/--refresh are about staleness *across*
        runs (did a new release appear since last time), not within one.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT fetched_at FROM versions WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return True
        fetched_at = row[0]
        if fetched_at >= self._run_start:
            return False
        if self.force_refresh:
            return True
        return (time.time() - fetched_at) > self.ttl

    def get_versions(self, name: str) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute(
                "SELECT versions_json FROM versions WHERE name = ?", (name,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def set_versions(self, name: str, versions: dict) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO versions (name, versions_json, fetched_at) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET versions_json = excluded.versions_json, "
                "fetched_at = excluded.fetched_at",
                (name, json.dumps(versions), time.time()),
            )

    def get_requires_dist(self, name: str, version: str) -> Optional[list]:
        with self._lock:
            row = self._conn.execute(
                "SELECT requires_dist_json FROM requires_dist WHERE name = ? AND version = ?",
                (name, version),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def set_requires_dist(self, name: str, version: str, deps: list) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO requires_dist (name, version, requires_dist_json) VALUES (?, ?, ?) "
                "ON CONFLICT(name, version) DO UPDATE SET "
                "requires_dist_json = excluded.requires_dist_json",
                (name, version, json.dumps(deps)),
            )

    def set_projects(self, projects: list[str]) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM projects")
            self._conn.executemany(
                "INSERT INTO projects (name) VALUES (?)", [(p,) for p in projects]
            )

    def get_projects(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute("SELECT name FROM projects").fetchall()
        return [row[0] for row in rows]

    def set_packages(self, packages: list[str]) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM packages")
            self._conn.executemany(
                "INSERT INTO packages (name) VALUES (?)", [(p,) for p in packages]
            )

    def get_packages(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute("SELECT name FROM packages").fetchall()
        return [row[0] for row in rows]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
