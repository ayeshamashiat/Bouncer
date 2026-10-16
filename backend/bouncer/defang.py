"""One canonical spelling for every indicator, so the same domain/IP from two
sources becomes ONE node (otherwise nothing connects).

Canonical form = lowercase, last dot written as [.]  e.g. socifiapp[.]com, 91.92.242[.]30
"""
import ipaddress
import re

# Shared infrastructure that connects everything and proves nothing (supernodes).
COMMON_INFRA_ALLOWLIST = {
    "github.com", "raw.githubusercontent.com", "gist.github.com", "api.github.com",
    "objects.githubusercontent.com", "pypi.org", "files.pythonhosted.org",
    "npmjs.com", "registry.npmjs.org", "googleapis.com", "storage.googleapis.com",
    "amazonaws.com", "s3.amazonaws.com", "cloudflare.com", "jsdelivr.net",
    "cdn.jsdelivr.net", "unpkg.com", "clawhub.ai", "openclaw.ai", "anthropic.com",
    "openai.com", "huggingface.co",
}

# Matches real (un-defanged) URLs and IPs: these must never sit in our data files.
LIVE_URL_RE = re.compile(r"\bhttps?://", re.I)
LIVE_IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


def refang(value: str) -> str:
    v = value.strip()
    v = v.replace("[.]", ".").replace("(.)", ".").replace("[dot]", ".")
    v = re.sub(r"^hxxp", "http", v, flags=re.I)
    v = v.replace("[:]", ":").replace("[://]", "://")
    return v


def _defang_last_dot(v: str) -> str:
    i = v.rfind(".")
    return v if i < 0 else v[:i] + "[.]" + v[i + 1:]


def canon_domain(value: str) -> str:
    v = refang(value).lower().rstrip(".")
    v = re.sub(r"^[a-z]+://", "", v).split("/")[0].split(":")[0]
    return _defang_last_dot(v)


def canon_ip(value: str) -> str:
    v = refang(value)
    ipaddress.ip_address(v)  # raises ValueError if not an IP
    return _defang_last_dot(v)


def canon_payload(value: str) -> str:
    return value.strip()


def plain_domain(canon: str) -> str:
    return refang(canon)


def is_common_infra_domain(canon: str) -> bool:
    d = plain_domain(canon)
    return any(d == a or d.endswith("." + a) for a in COMMON_INFRA_ALLOWLIST)
