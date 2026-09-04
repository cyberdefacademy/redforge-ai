# REDFORGE AI — Tool Adapter Architecture

## Registry (tools/registry/*.yaml)
```yaml
tool:
  name: nmap
  executable: /usr/bin/nmap
  category: reconnaissance
  risk_level: low
  timeout: 300
  requires_approval: false
  input_schema:
    type: object
    properties:
      target: {type: string}
      ports: {type: string}
      mode: {enum: [fast, comprehensive]}
  output_parser: nmap_xml
```

## Execution Pipeline
```
AI Intent → Structured Action → Adapter → Argument Validator → Scope Guard → Risk Engine → Approval Engine → Sandbox → Parser → Evidence → Graph Update
```

Never: `shell = ai_output`

## Sandbox (tools/sandbox)
- Process isolation, resource limits, timeout, CPU/mem caps, fs/net restrictions, env filtering, output capture, provenance, cancellation, cleanup
- Every run records: engagement_id, operator, agent, tool, target, timestamp, args, auth_state, risk, approval, exit_code, stdout/stderr, artifacts

## Categories & Adapters
- Recon: nmap, masscan, amass, subfinder, dnsx, whois, whatweb
- Web: nuclei, gobuster, feroxbuster, nikto, zap
- Network: nmap, netcat, tshark
- Vuln: nuclei, searchsploit, openvas stub
- AD/Cloud/Wireless: adapter stubs, enabled via plugins
