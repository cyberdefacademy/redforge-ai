FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap curl whatweb hydra sqlmap \
    perl libwhisker2-perl libnet-ssleay-perl libio-socket-ssl-perl openssl ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && curl -sSL https://github.com/sullo/nikto/archive/refs/tags/2.5.0.tar.gz | tar -xz -C /opt \
  && mv /opt/nikto-2.5.0 /opt/nikto \
  && printf '#!/bin/sh\nexec perl /opt/nikto/program/nikto.pl "$@"\n' > /usr/bin/nikto && chmod +x /usr/bin/nikto \
  && useradd -r -u 999 -m appuser && mkdir -p /var/lib/redforge/evidence && chown appuser:appuser /var/lib/redforge/evidence
# WhatWeb fix: disable resolv-replace (pure-Ruby DNS returns AAAA first with no
# connect fallback, breaking scans in dual-stack Docker networks). System
# getaddrinfo (gai.conf IPv4-first + full fallback) is used instead.
RUN sed -i "s|^require 'resolv-replace'|# require 'resolv-replace'  # disabled by REDFORGE: AAAA-first, no fallback|" \
      /usr/lib/ruby/vendor_ruby/whatweb.rb \
  && grep -q "disabled by REDFORGE" /usr/lib/ruby/vendor_ruby/whatweb.rb
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini pytest.ini ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh \
  && printf 'precedence ::ffff:0:0/96 100\n' >> /etc/gai.conf
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD curl -sf http://127.0.0.1:8000/healthz || exit 1
USER appuser
ENTRYPOINT ["./entrypoint.sh"]
