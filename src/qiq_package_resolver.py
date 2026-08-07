"""
This class finds the the correct package versions by solving the 
inter dependencies in between packages like pip using resolvelib.

Example:
resolver = QiQ_Package_Resolver()
packages = [Requirement('numpy>2.0.0'), Requirement('pillow==2.1.1'), ...]
resolver.get(packages)

Output:
=======
{pkg:[dependencies], pkg:[dependencies], ...}
"""

__version__ = "0.0.1"

# python imports
import json
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import NamedTuple

# pip imports
from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from resolvelib import AbstractProvider, BaseReporter, Resolver, ResolutionImpossible

# Project imports 
from qiq_package_cache import QiQ_Package_Cache
import qiq_utils as utils
import qiq_config as C

USER_AGENT = "steno-pypi-resolver-prototype"
ENVIRONMENT = default_environment()

class Candidate(NamedTuple):
    name: str
    version: str


class PyPIClient:
    """Fetches PyPI project/version metadata, backed by a PyPICache.

    Thread-safe: many threads can request different (or even the same)
    packages concurrently. `self._inflight` deduplicates concurrent fetches
    for the exact same key, so speculative prefetching racing a synchronous
    call for the same package never doubles the network traffic.
    """

    def __init__(self, cache: QiQ_Package_Cache, max_workers: int = 8):
        self.cache = cache
        self._lock = threading.Lock()
        self._inflight: dict[tuple, threading.Event] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _get_json(self, url: str):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return 200, json.load(resp)
        except urllib.error.HTTPError as e:
            return e.code, None

    def _run_once(self, dedup_key: tuple, fetch_and_store) -> None:
        """Run fetch_and_store() exactly once per dedup_key across all threads."""
        with self._lock:
            event = self._inflight.get(dedup_key)
            if event is not None:
                is_owner = False
            else:
                event = threading.Event()
                self._inflight[dedup_key] = event
                is_owner = True
        if not is_owner:
            event.wait()
            return
        try:
            fetch_and_store()
        finally:
            with self._lock:
                del self._inflight[dedup_key]
            event.set()

    def versions(self, name: str) -> list[str]:
        """All non-yanked versions, sorted ascending by real version order."""
        key = canonicalize_name(name)

        if self.cache.is_stale(key):
            def do_fetch():
                print(f"{C.YELLOW}Refreshing package cache : {C.RESET} {key}")
                status, data = self._get_json(f"https://pypi.org/pypi/{key}/json")
                versions = {}
                if status == 200:
                    for version, files in data["releases"].items():
                        yanked = bool(files) and all(f.get("yanked", False) for f in files)
                        versions[version] = {"yanked": yanked}
                self.cache.set_versions(key, versions)

            self._run_once(("project", key), do_fetch)

        cached = self.cache.get_versions(key) or {}
        parsed = []
        for version, meta in cached.items():
            if meta.get("yanked"):
                continue
            try:
                parsed.append((Version(version), version))
            except InvalidVersion:
                continue
        parsed.sort()
        return [v for _, v in parsed]

    def requires_dist(self, name: str, version: str) -> list[str]:
        key = canonicalize_name(name)

        cached = self.cache.get_requires_dist(key, version)
        if cached is not None:
            return cached

        def do_fetch():
            status, data = self._get_json(f"https://pypi.org/pypi/{key}/{version}/json")
            deps = (data["info"].get("requires_dist") or []) if status == 200 else []
            self.cache.set_requires_dist(key, version, deps)

        self._run_once(("dist", key, version), do_fetch)
        return self.cache.get_requires_dist(key, version) or []

    def prefetch_versions(self, names) -> None:
        """Blocking: warm the version list for every name, in parallel."""
        keys = {canonicalize_name(n) for n in names}
        futures = [self._executor.submit(self.versions, k) for k in keys]
        for f in as_completed(futures):
            f.result()

    def prefetch_versions_async(self, names) -> None:
        """Fire-and-forget: warm version lists for newly discovered names."""
        for n in {canonicalize_name(n) for n in names}:
            self._executor.submit(self.versions, n)

    def prefetch_requires_dist_async(self, name_version_pairs) -> None:
        """Fire-and-forget: warm requires_dist for likely-to-be-chosen candidates."""
        for name, version in name_version_pairs:
            self._executor.submit(self.requires_dist, name, version)


class PyPIProvider(AbstractProvider):

    def __init__(self, client: PyPIClient, extras: frozenset[str] = frozenset(), prefetch_depth: int = 3):
        self.client = client
        self.extras = extras
        self.prefetch_depth = prefetch_depth

    def identify(self, requirement_or_candidate):
        return canonicalize_name(requirement_or_candidate.name)

    def get_preference(self, identifier, resolutions, candidates, information, backtrack_causes):
        return sum(1 for _ in candidates[identifier])

    def marker_ok(self, requirement) -> bool:
        if requirement.marker is None:
            return True
        if requirement.marker.evaluate({**ENVIRONMENT, "extra": ""}):
            return True
        return any(requirement.marker.evaluate({**ENVIRONMENT, "extra": e}) for e in self.extras)

    def find_matches(self, identifier, requirements, incompatibilities):
        reqs = [r for r in requirements[identifier] if self.marker_ok(r)]
        if not reqs and list(requirements[identifier]):
            return []  # every requirement for this id was marker-excluded

        bad_versions = {c.version for c in incompatibilities[identifier]}
        combined_spec = SpecifierSet()
        for r in reqs:
            combined_spec &= r.specifier

        def matching(allow_prereleases: bool) -> list[Candidate]:
            found = []
            for version in reversed(self.client.versions(identifier)):
                if version in bad_versions:
                    continue
                if not combined_spec.contains(version, prereleases=allow_prereleases):
                    continue
                found.append(Candidate(identifier, version))
            return found

        # Match pip's real default: only ever consider a prerelease if no
        # stable release satisfies the constraint, or a requirement names one
        # explicitly (combined_spec.contains already honors that per-clause).
        # Without this, a bare "librosa" with no version at all would happily
        # resolve to the newest matching string regardless of stability --
        # which, as observed, picked an rc over the real latest release.
        candidates = matching(allow_prereleases=False)
        if not candidates:
            candidates = matching(allow_prereleases=True)

        # Speculatively warm requires_dist for the most-preferred candidates in
        # the background -- resolvelib will likely call get_dependencies on one
        # of these soon (or on backtrack), so overlap that fetch with whatever
        # else the resolver is doing right now instead of paying for it later.
        top = candidates[: self.prefetch_depth]
        self.client.prefetch_requires_dist_async((c.name, c.version) for c in top)

        return candidates

    def is_satisfied_by(self, requirement, candidate):
        if not self.marker_ok(requirement):
            return True
        return requirement.specifier.contains(candidate.version, prereleases=True)

    def get_dependencies(self, candidate):
        deps = []
        for raw in self.client.requires_dist(candidate.name, candidate.version):
            req = Requirement(raw)
            if self.marker_ok(req):
                deps.append(req)

        # As soon as we see a new package name, start warming its version
        # list in the background -- resolvelib will need it in a later round.
        self.client.prefetch_versions_async(self.identify(d) for d in deps)

        return deps


class QiQ_Package_Resolver:

    def __init__ (self, ttl: float = QiQ_Package_Cache.DEFAULT_TTL, force_refresh: bool = False):

        self.cache = QiQ_Package_Cache(ttl, force_refresh)
        self.client = PyPIClient(self.cache)
        self.provider = PyPIProvider(self.client)
        self.resolver = Resolver(self.provider, BaseReporter())

    def _build_dependency_tree(self, result) -> dict:
        """Map each resolved package to the list of its *direct* dependencies.

        Both keys and values are "name==version" -- pulled from resolvelib's own
        result graph (result.graph.iter_children), not re-derived by hand, so
        this reflects what the resolver actually decided, edges and all.
        """
        def label(identifier: str) -> str:
            candidate = result.mapping[identifier]
            return f"{candidate.name}=={candidate.version}"

        tree = {}
        for identifier in result.mapping:
            children = sorted(result.graph.iter_children(identifier))
            tree[label(identifier)] = [label(c) for c in children]
        return dict(sorted(tree.items()))

    def _render_dependency_tree(self, result) -> str:
        """Render the resolved graph as an indented parent/child tree, starting
        from the roots (result.graph.iter_children(None) -- what requirements.txt
        actually asked for), with each dependency nested under whichever package
        pulled it in.

        A package required by more than one parent is shown again under each of
        them (real trees fan back in -- e.g. numpy under both scipy and librosa),
        matching how the resolved graph actually looks rather than collapsing it
        to one line. If a genuine cycle exists (A -> B -> A), the repeat is
        marked "(cycle)" and not expanded again, so this can't recurse forever.
        """
        def label(identifier: str) -> str:
            candidate = result.mapping[identifier]
            return utils.print_specifier(f"{candidate.name}=={candidate.version}", False)

        lines = []

        def walk(identifier: str, depth: int, ancestors: frozenset):
            if depth == 0:
                lines.append(label(identifier))
            else:
                indent = "|    " * (depth - 1)
                lines.append(f"{indent}└── {label(identifier)}")

            if identifier in ancestors:
                lines[-1] += "  (cycle)"
                return

            for child in sorted(result.graph.iter_children(identifier)):
                walk(child, depth + 1, ancestors | {identifier})

        for root in sorted(result.graph.iter_children(None)):
            walk(root, 0, frozenset())

        return "\n".join(lines)

    def _explain_conflict(self, exc: ResolutionImpossible) -> str:
        lines = ["Resolution impossible -- conflicting requirements:"]
        for cause in exc.causes:
            req = cause.requirement
            parent = cause.parent
            origin = f"{parent.name}=={parent.version}" if parent is not None else "(root requirement)"
            lines.append(f"  {origin} requires {req}")
        return "\n".join(lines)

    def _filter_roots(self, roots: list[Requirement]):
        # A root whose own marker doesn't match this environment (e.g.
        # `pywin32==311; sys_platform == "win32"` while running on Linux) must be
        # dropped *before* it ever reaches resolvelib. Transitive dependencies
        # already get this filtering in get_dependencies(), which simply never
        # hands resolvelib an inapplicable requirement in the first place -- but
        # roots go straight from requirements.txt into resolver.resolve(), so
        # without this, resolvelib would still see pywin32 as something that
        # MUST be pinned, find zero applicable candidates for it, and treat that
        # as an unresolvable conflict instead of "not needed here."
        applicable_roots, skipped_roots = [], []
        for r in roots:
            (applicable_roots if self.provider.marker_ok(r) else skipped_roots).append(r)
        if skipped_roots:
            print(f"Skipping {len(skipped_roots)} requirement(s) not applicable to this environment:")
            for r in skipped_roots:
                print(f"  {r}")
        return applicable_roots

    def _get(self, roots: list[Requirement]):
        start = time.monotonic()
        try:
            # All root package names are already known from requirements.txt
            # no need to wait for resolvelib to discover them one at a time.
            # Warm them all in parallel before the (single-threaded) solve starts.
            self.client.prefetch_versions(r.name for r in roots)
            result = self.resolver.resolve(roots)
        except ResolutionImpossible as exc:
            print(self._explain_conflict(exc))
            exit()
        finally:
            self.client.shutdown()
            self.cache.close()

        elapsed = time.monotonic() - start
        return result

    def get(self, roots: list[Requirement]):
        """"""
        roots = self._filter_roots(roots)
        results = self._get(roots)
        tree = self._build_dependency_tree(results)
        return tree

    def show_tree(self, root: Requirement):
        """"""
        roots = self._filter_roots([root])
        results = self._get([root])
        tree = self._render_dependency_tree(results)
        return tree
