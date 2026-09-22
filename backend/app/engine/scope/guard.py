import ipaddress, re
from urllib.parse import urlparse

_PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

class ScopeGuard:
    """Enforces authorized scope for every operation."""

    @staticmethod
    def validate_cidr(cidr: str) -> bool:
        try:
            ipaddress.ip_network(cidr, strict=False)
            return True
        except ValueError:
            return False

    @staticmethod
    def ip_in_scope(ip: str, cidrs: list[str]) -> bool:
        try:
            addr = ipaddress.ip_address(ip)
            for c in cidrs:
                if addr in ipaddress.ip_network(c, strict=False):
                    return True
        except ValueError:
            return False
        return False

    @staticmethod
    def is_valid_url(url: str) -> bool:
        try:
            p = urlparse(url)
            return p.scheme in ("http","https") and bool(p.netloc)
        except Exception:
            return False

    @staticmethod
    def hostname_allowed(hostname: str, allowed_domains: list[str]) -> bool:
        h = hostname.lower()
        for d in allowed_domains:
            d = d.lower().lstrip("*.")
            if h == d or h.endswith("." + d):
                return True
        return False

    @staticmethod
    def port_allowed(port: int, excluded_ports: list[int]) -> bool:
        return port not in excluded_ports

    @staticmethod
    def technique_allowed(technique: str, excluded_techniques: list[str]) -> bool:
        return technique not in excluded_techniques

    @staticmethod
    def time_window_valid(now_hour: int, start: int | None, end: int | None) -> bool:
        if start is None or end is None:
            return True
        if start <= end:
            return start <= now_hour <= end
        return now_hour >= start or now_hour <= end

    @staticmethod
    def is_private_ip(ip: str) -> bool:
        try:
            addr = ipaddress.ip_address(ip.strip().strip("[]"))
            return any(addr in n for n in _PRIVATE_NETS)
        except ValueError:
            return False

    @staticmethod
    def extract_host(target: str) -> str:
        """Extract hostname/IP from a URL or bare host:port value."""
        t = target.strip()
        if "://" in t:
            try:
                return urlparse(t).hostname or t
            except Exception:
                return t
        # strip port for bare host:port (but not IPv6 with brackets handled above)
        if t.count(":") == 1 and not t.startswith("["):
            return t.split(":")[0]
        return t.strip("[]")

    @classmethod
    def evaluate(cls, target: str, target_type: str, scope_targets: list[dict], exclusions: list[dict], port: int | None = None, technique: str | None = None) -> dict:
        """Returns {allowed: bool, reason: str} — deny-by-default."""
        target = (target or "").strip()
        if not target:
            return {"allowed": False, "reason": "Empty target"}
        # Deny-by-default: no scope defined means no authorization.
        if not scope_targets:
            return {"allowed": False, "reason": "No authorized scope defined for engagement"}
        host = cls.extract_host(target)
        # Determine if target matches any scope target
        matched = False
        for t in scope_targets:
            if t["target_type"] == target_type and t["value"] == target:
                matched = True
            elif t["target_type"] == "cidr" and target_type in ("ip", "hostname"):
                # hostname may be an IP literal
                try:
                    if cls.ip_in_scope(host, [t["value"]]):
                        matched = True
                except Exception:
                    pass
            elif t["target_type"] == "domain" and target_type in ("domain", "hostname", "url"):
                if cls.hostname_allowed(host, [t["value"]]):
                    matched = True
            elif t["target_type"] == "url" and target_type == "url":
                if cls.hostname_allowed(host, [cls.extract_host(t["value"])]):
                    matched = True
            elif t["target_type"] == "ip" and target_type in ("ip", "hostname"):
                if host == t["value"]:
                    matched = True

        if not matched:
            # Targets defined and none match -> deny. Private/link-local gets SSRF-specific reason.
            if target_type in ("url", "ip", "hostname") and cls.is_private_ip(host):
                return {"allowed": False, "reason": f"Target {target} not in scope and resolves to private address (SSRF blocked)"}
            return {"allowed": False, "reason": f"Target {target} not in authorized scope"}

        # Check exclusions
        for e in exclusions:
            et = e.get("exclusion_type", "system")
            val = e.get("value", "")
            if et in ("system", "host", "domain", "ip", "url"):
                # Exact match, CIDR containment, or subdomain match.
                if val == target or val == host:
                    return {"allowed": False, "reason": f"Target excluded: {val}"}
                try:
                    if "/" in val and cls.ip_in_scope(host, [val]):
                        return {"allowed": False, "reason": f"Target excluded by CIDR: {val}"}
                except Exception:
                    pass
                if host.endswith("." + val.lstrip("*.")):
                    return {"allowed": False, "reason": f"Target excluded by domain: {val}"}
            if et == "technique" and technique == val:
                return {"allowed": False, "reason": f"Technique excluded: {technique}"}
            if et == "port" and port is not None and str(port) == str(val):
                return {"allowed": False, "reason": f"Port excluded: {port}"}

        return {"allowed": True, "reason": "Scope validated"}
