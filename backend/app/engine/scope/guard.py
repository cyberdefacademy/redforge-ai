import ipaddress, re
from urllib.parse import urlparse

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

    @classmethod
    def evaluate(cls, target: str, target_type: str, scope_targets: list[dict], exclusions: list[dict], port: int | None = None, technique: str | None = None) -> dict:
        """Returns {allowed: bool, reason: str}"""
        # Determine if target matches any scope target
        matched = False
        for t in scope_targets:
            if t["target_type"] == target_type and t["value"] == target:
                matched = True
            elif t["target_type"] == "cidr" and target_type == "ip":
                if cls.ip_in_scope(target, [t["value"]]):
                    matched = True
            elif t["target_type"] == "domain" and target_type in ("domain","hostname"):
                if cls.hostname_allowed(target, [t["value"]]):
                    matched = True

        if not matched and scope_targets:
            # If targets defined and none match, deny
            return {"allowed": False, "reason": f"Target {target} not in authorized scope"}

        # Check exclusions
        for e in exclusions:
            if e["value"] == target or (e["exclusion_type"] == "port" and str(port) == e["value"]):
                return {"allowed": False, "reason": f"Target excluded: {e['value']}"}
            if e["exclusion_type"] == "technique" and technique == e["value"]:
                return {"allowed": False, "reason": f"Technique excluded: {technique}"}
            if e["exclusion_type"] == "port" and port and str(port) == e["value"]:
                return {"allowed": False, "reason": f"Port excluded: {port}"}

        return {"allowed": True, "reason": "Scope validated"}
