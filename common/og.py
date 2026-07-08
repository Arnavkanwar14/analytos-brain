"""Thin Omnigraph HTTP client (data + control read plane). Actor identity is the
bearer token; the server resolves the actor and enforces Cedar server-side."""
from __future__ import annotations
import json
from urllib.parse import quote
import requests

from . import config


class OGError(RuntimeError):
    def __init__(self, status, body):
        super().__init__(f"OG HTTP {status}: {body[:300]}")
        self.status = status
        self.body = body


class OG:
    def __init__(self, role: str = "admin", base_url: str | None = None):
        self.role = role
        resolved = base_url or config.resolve_omnigraph_base_url()
        if config.is_hf_space():
            resolved = config.assert_localhost_og_url(resolved)
        self.base = resolved.rstrip("/")
        self.token = config.token(role)
        self.s = requests.Session()
        self.s.headers.update({
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        })

    def _req(self, method, path, body=None, raw=False, timeout=60):
        r = self.s.request(method, self.base + path, data=json.dumps(body) if body is not None else None, timeout=timeout)
        if r.status_code >= 400:
            raise OGError(r.status_code, r.text)
        return r.text if raw else (r.json() if r.text else {})

    # ---- health / topology ----
    def healthz(self):
        return self._req("GET", "/healthz")

    def graphs(self):
        return self._req("GET", "/graphs").get("graphs", [])

    # ---- reads ----
    def query(self, graph, name, params=None, branch="main"):
        return self._req("POST", f"/graphs/{graph}/queries/{name}", {"params": params or {}, "branch": branch})

    def query_adhoc(self, graph, source, params=None, branch="main"):
        return self._req("POST", f"/graphs/{graph}/query",
                         {"query": source, "params": params or {}, "branch": branch})

    def snapshot(self, graph, branch="main"):
        return self._req("GET", f"/graphs/{graph}/snapshot?branch={quote(branch, safe='')}")

    def commits(self, graph, branch="main"):
        return self._req("GET", f"/graphs/{graph}/commits?branch={quote(branch, safe='')}").get("commits", [])

    def branches(self, graph):
        return self._req("GET", f"/graphs/{graph}/branches").get("branches", [])

    def export(self, graph, branch="main"):
        """Returns a list of {'type'|'edge', 'data': {...}} records."""
        txt = self._req("POST", f"/graphs/{graph}/export", {"branch": branch}, raw=True)
        out = []
        for line in txt.splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    # ---- writes (branch-scoped) ----
    def load(self, graph, ndjson: str, mode="merge", branch="main", from_branch=None):
        body = {"data": ndjson, "mode": mode, "branch": branch}
        if from_branch:
            body["from"] = from_branch
        return self._req("POST", f"/graphs/{graph}/load", body)

    def merge(self, graph, source, target="main"):
        return self._req("POST", f"/graphs/{graph}/branches/merge", {"source": source, "target": target})

    def delete_branch(self, graph, name):
        return self._req("DELETE", f"/graphs/{graph}/branches/{quote(name, safe='')}")
