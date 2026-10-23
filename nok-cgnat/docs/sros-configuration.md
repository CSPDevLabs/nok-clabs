# SROS CG-NAT configuration (this lab)

MD-CLI in `configs/ne/` follows the DS-Lite AFTR + stateful inter-chassis redundancy
(SICR) intent from the 26.7 MD-CLI note, with digital-twin addresses from the
CG-NAT lab design. Lab image, XPaths, and log IDs are SR OS 26.7.R1.

This lab uses the **Base-router** NAT variant (MD-CLI note §7) so the digital twin
comes up on SRSIM without a full BGP-VPN. The same NAT policy, pool, DS-Lite
endpoint, SICR, watermarks, and syslog split apply. gNMI still subscribes to the
VPRN form of B9 so a VPRN deployment matches the reference tree.

The CG-NAT tech note is a SoW / ATP checklist (LSN, DS-Lite, SICR, logging, FCAPS),
not a lab dump. This recipe implements the DS-Lite + stateful ICR + syslog slice.

## Building blocks

1. **ISA2-BB MDA** (`1/2`) on an SR-1e `iom-e` line card. Each NAT router has
   a CPM container and a slot-1 IOM container sharing its network namespace.
   MDA 1 is `me6-10gb-sfp+`; MDA 2 is `isa2-bb`; `active-mda-limit 1` matches
   the single NAT adapter. SR-SIM 26.7 supports ISA2-BB on this profile. The IOM
   container is required for the adapter to become equipped and operational;
   a Linux ESA cable peer does not provide ESA compute resources.
2. **ISA nat-group 1** with `redundancy inter-chassis` enabled: keepalive 30/3,
   replication-threshold 50, flow-timeout-on-switchover 50, ip-mtu 9000,
   `local-ip-range-start` / `remote-ip-range-start` swapped on the peer,
   `preferred true` on cgnat1.
3. **MCS** `redundancy multi-chassis peer` `sync nat nat-group 1` with
   matching `sync-tag "dslite-nat"` and `source-address`.
4. **Outside pool** `dslite-pool` `type large-scale`, `port-reservation ports 200`,
   watermarks **90/80** (event **2003**), `large-scale redundancy admin-state disable`
   (stateless dual-homing and SICR are mutually exclusive from 26.3.R1).
5. **NAT policy** `dslite-policy`: block-limit 4, TCP/UDP/ICMP timeouts from the
   MD-CLI note, `flow-log-policy syslog "dslite-syslog"`.
6. **Inside DS-Lite** AFTR endpoint `2001:db8:1::1` (VRRP on ACCESS),
   subscriber-prefix-length **128**, tunnel-mtu 1500, reassembly false,
   min-first-fragment-size-rx 1280. IPv6 VRRP uses explicit ACCESS link-local
   addresses (`fe80::2` / `fe80::3`), virtual link-local address `fe80::1`, and
   enabled router advertisements with the virtual MAC.
7. **Syslog split:** CPM NAT events on **local5** (`log-id 50`, filter application
   NAT); ISA per-flow records on **local6**. Event severities raised for 2025 /
   2037 / 2003; LSN subscriber watermarks 2026–2029 throttled.

cgnat1 and cgnat2 share the pool and AFTR address; SICR elects the active group.
Equal health uses `preferred true` on cgnat1. The core advertises INET into
IS-IS as passive; both ICL sync routes and NAT-pool return next hops are
explicitly enabled because SR OS otherwise leaves the next hops disabled.

## Addressing (digital twin)

| Role | Value |
|------|--------|
| AFTR / VRRP | `2001:db8:1::1/64` |
| CGNAT1 / CGNAT2 ACCESS | `2001:db8:1::2`, `::3` |
| ICL | `10.255.255.0/30` |
| ISA sync ranges | `10.192.3.1` / `10.192.4.1` |
| Outside P2P | `192.0.2.0/30`, `192.0.2.4/30` |
| NAT pool | `203.0.113.1–254` |
| Internet | `198.51.100.10/24` |
| B4 dummy (RFC 6333) | `192.0.0.2/29` |
| Customer LAN (all three homes) | `192.168.1.0/24`, host `.50` |

## Not in this lab image

- Hardware `imm-2pc-fp3` / `isa2-bb` MDA option (MD-CLI §1.A) — deployed as an equipped ISA2-BB MDA, not an ESA stub.
- Inside/outside VPRNs 550/500 with BGP-VPN (MD-CLI §4–5) — Base NAT instead.
- DHCPv6 option 64 AFTR-Name server (MD-CLI §6) — B4s use static WAN IPv6 plus
  `dhclient -6` if a server appears.
- IPFIX export (MD-CLI §9.1) — syslog flow-log only, as the recipe specifies.
- SR-MPLS between PEs — ISIS IPv4 on the outside/ICL only.

Show commands from the MD-CLI note still apply:

```
show isa nat-group 1
show isa nat-group 1 inter-chassis-redundancy
show redundancy multi-chassis sync
```
