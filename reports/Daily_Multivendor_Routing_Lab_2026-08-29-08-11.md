# Daily Multivendor Routing Lab — 2026-08-29-08-11

**Run timestamp:** `2026-08-29-08-11` (America/Los_Angeles)  
**Vendors:** Cisco Systems, Fortinet, Palo Alto Networks, Arista Networks, Aruba/HPE, Juniper, FRRouting  
**Focus:** Layer 2/Layer 3 routing and switching, redistribution, EVPN/VXLAN, MPLS/Segment Routing, underlay/overlay, RIB/FIB, multichassis, and cumulative active recall.

> **Core mental model:** adjacency, protocol database, RIB selection, recursive next-hop reachability, FIB/hardware programming, overlay import, multichassis state, and real service health are separate checkpoints. A healthy earlier checkpoint does not prove a later checkpoint.

## Vendor / Topic Matrix

| Vendor | Focus in this run |
|---|---|
| Cisco | Hierarchical eBGP EVPN, all-active multihoming consistency, routed overlay |
| Fortinet | BGP multipath + SD-WAN, NP7 VXLAN offload, OSPF/BGP route tags |
| Palo Alto Networks | Advanced Routing Engine filters, OSPF migration, redistribution vs export |
| Arista | EVPN Type-5 DCI, centralized-gateway BUM behavior, control/data plane |
| Aruba/HPE | VSX logical VTEP, OSPF redistribution, layered troubleshooting |
| Juniper | IPv6 EVPN underlay, routing on IRB, Type-5 scale design |
| FRRouting | Linux EVPN state, OSPF redistribution, IS-IS Segment Routing |

---

## Detailed Technical Lessons

### 1. Cisco — Hierarchical eBGP EVPN multihoming: preserve the VTEP next hop through the spine

**Source:** https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst_standalones/Multihoming/multihoming-in-bgp-evpn-vxlan-fabric/hierarchical-multihoming/configure-ebgp-based-evpn-multihoming-and-fabric-network.html

Cisco's hierarchical eBGP design separates leaf/distribution and spine/border routing domains. The spine functions as a control-plane transit point rather than an unintended VXLAN data-plane waypoint. Preserving the original VTEP next hop allows remote leaves to recursively resolve the actual VTEP and encapsulate traffic directly.

A route can therefore be present and valid in the EVPN RIB while still being unusable for forwarding. If the retained VTEP next hop is missing from the underlay RIB/FIB, the first failed boundary is underlay recursion—not route-target import.

Verification sequence:

```text
show bgp l2vpn evpn summary
show bgp l2vpn evpn
show ip route <remote-vtep>
```

**Lab:** Preserve the next hop through a spine, verify direct VTEP-to-VTEP VXLAN forwarding, then remove underlay reachability to the remote VTEP and compare control-plane state with the forwarding failure.

### 2. Cisco — All-active EVPN multihoming: pair consistency is forwarding correctness

**Source:** https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst_standalones/Multihoming/multihoming-in-bgp-evpn-vxlan-fabric/all-active-mode/restriction-for-aa-multihoming.html

Cisco requires provisioned and operational EVPN instance state to remain consistent across both dual-homed VTEPs. A mismatch can create partial service state and traffic blackholing even though BGP sessions are healthy.

Troubleshoot the pair side-by-side: Ethernet Segment identity, EVPN instance/VNI state, local port-channel state, EVPN advertisements, and underlay reachability.

### 3. Cisco — Routed overlay: keep Layer-2 redundancy and Layer-3 overlay reasoning separate

**Source:** https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst_standalones/Multihoming/multihoming-in-bgp-evpn-vxlan-fabric/routed-overlay-mh/routed-overlay-network-reference-configuration.html

A healthy host-facing Ethernet Segment proves access redundancy, not tenant route import or remote VTEP reachability. Debug VLAN↔VNI, SVI↔VRF, VRF↔RT, and EVPN-route↔next-hop mappings as explicit boundaries.

### 4. Fortinet — BGP-learned routes feeding SD-WAN: multipath must reach the RIB first

**Source:** https://community.fortinet.com/fortigate-3/technical-tip-configuring-sd-wan-traffic-steering-with-bgp-learned-routes-229549

Fortinet's August 24, 2026 example shows two Established eBGP sessions learning the same destination. Before eBGP multipath is enabled, both paths can exist in BGP while only one is installed in the routing table. SD-WAN cannot steer over a path that routing has not made usable.

```text
get router info bgp summary
get router info bgp network <prefix>
get router info routing-table details <prefix>
diagnose sys sdwan service
diagnose sys session list
```

The session output is particularly valuable because fields such as `sdwan_mbr_seq` and the selected gateway prove which member a real flow used.

### 5. Fortinet — VXLAN over EVPN on NP7: reachability can be correct while offload is wrong

**Source:** https://community.fortinet.com/fortigate-3/technical-tip-how-to-enable-np7-hardware-offloading-for-vxlan-over-evpn-traffic-225075

On affected NP7 platforms, Fortinet documents a relationship between the VXLAN `learn-from-traffic` setting and hardware acceleration. This creates an important diagnostic split: EVPN and VNI state may be correct while CPU utilization or throughput is wrong because the data path is not offloaded as expected.

### 6. Fortinet — OSPF route tags redistributed into BGP: verify provenance after conversion

**Source:** https://community.fortinet.com/fortigate-3/technical-tip-wrong-route-tag-added-to-bgp-routes-redistributed-from-ospf-214352

Affected FortiOS versions can mishandle very high route-tag values during OSPF→BGP redistribution. Because tags often implement deny-on-return loop prevention, a metadata defect can become a routing-loop or reachability problem.

Verify the tag in the source OSPF database and again after BGP redistribution rather than assuming it survived protocol conversion unchanged.

### 7. Palo Alto Networks — Advanced Routing Engine filters: syntax is incomplete without the attachment point

**Source:** https://docs.paloaltonetworks.com/ngfw/networking/advanced-routing/create-filters-for-the-advanced-routing-engine

PAN-OS can use prefix lists, access lists, redistribution route maps, BGP community lists, AS-path filters, and BGP route maps at different stages. A prefix match attached to redistribution is semantically different from the same prefix match attached to peer export.

Troubleshoot the route lifecycle in order: source RIB → redistribution admission → destination protocol RIB → peer advertisement.

### 8. Palo Alto Networks — OSPF migration to Advanced Routing Engine: policy semantics can change

**Source:** https://docs.paloaltonetworks.com/pan-os/u-v/routing-engine-migration-reference/routing-protocol-migration-exceptions/ospf

Legacy OSPF export rules can match path type and area in ways that do not map one-for-one to Advanced Routing Engine redistribution policy. A syntactically successful migration can therefore broaden or narrow route admission unless business intent is reconstructed with prefixes, tags, or other supported matches.

### 9. Palo Alto Networks — Redistribution candidate selection and BGP peer export are different boundaries

**Source:** https://docs.paloaltonetworks.com/ngfw/networking/configure-route-redistribution

If a route never enters the local BGP RIB, changing peer export policy cannot fix it. If it exists locally but is absent from one peer, changing global redistribution may be too broad. Always identify the first stage where the prefix disappears.

### 10. Arista — EVPN Type-5 DCI gateway: re-origination creates a loop-prevention boundary

**Source:** https://www.arista.com/en/um-eos/eos-configuring-evpn

A DCI gateway can terminate Type-5 routes from one EVPN domain and re-originate them into another using domain-specific RD/RT and next-hop behavior. This resembles redistribution: provenance must survive the boundary so a route cannot leave one domain and return through another gateway unchecked.

```text
show bgp evpn
show bgp evpn route-type ip-prefix
show ip route vrf <vrf>
```

### 11. Arista — Single-gateway centralized routing: unnecessary VTEP identities can duplicate BUM replication

**Source:** https://www.arista.com/ko/um-eos/eos-evpn-vxlan-single-gateway-centralized-routing

In a topology with only one centralized L3 gateway or MLAG pair, redundant VTEP identities in the floodset can cause unnecessary duplicate BUM replication. Control-plane correctness and flood-efficiency are different design questions.

### 12. Arista — Control plane vs data plane: a route table entry is not proof of forwarding

**Source:** https://www.arista.com/en/um-eos/eos-data-transfer

EOS explicitly separates routing/control-plane route calculation from hardware-optimized packet transfer. This reinforces the universal multivendor troubleshooting model: protocol route → selected RIB route → resolved next hop → FIB/hardware programming → packet evidence.

### 13. Aruba/HPE — VSX with EVPN: independent BGP speakers, one logical VTEP

**Source:** https://www.arubanetworks.com/techdocs/AOS-CX/10.15/PDF/vsx.pdf

AOS-CX documents VSX peers as independent BGP control-plane entities while the pair can present one common logical VTEP in the data path. A single BGP session failure therefore does not necessarily remove the shared forwarding identity, and healthy BGP sessions do not prove host-facing VSX forwarding.

```text
show bgp l2vpn evpn
show evpn
show vsx status
show ip route <logical-vtep>
```

### 14. Aruba/HPE — OSPF redistribution and `active-routes-only`

**Source:** https://www.arubanetworks.com/techdocs/AOS-CX/10.15/PDF/ip_route_6300-6400-8100-83xx-9300-10000.pdf

AOS-CX can restrict redistribution to routes actually selected for forwarding. A route can exist in another protocol's database yet remain ineligible for redistribution because it is not the active RIB winner.

### 15. Aruba/HPE — Multivendor VXLAN troubleshooting: prove underlay, EVPN, then VSX

**Source:** https://www.arubanetworks.com/techdocs/AOS-CX/10.15/PDF/vsx.pdf

Recommended order: physical/VSX links → underlay route to logical VTEP → BGP EVPN session → EVPN route import → VXLAN forwarding → endpoint learning. The first missing state is the failure boundary.

### 16. Juniper — EVPN-VXLAN over IPv6 underlay

**Source:** https://www.juniper.net/documentation/us/en/software/junos/evpn/topics/topic-map/vxlan-ipv6-underlay-overview.html

Junos supports qualified EVPN-VXLAN designs with IPv6 underlay using BGP and OSPFv3. EVPN remains the overlay control plane while recursive VTEP transport reachability uses IPv6. Troubleshooting therefore moves the underlay evidence into IPv6 routing tables without changing the core overlay mental model.

### 17. Juniper — Routing protocols directly on EVPN IRB interfaces

**Source:** https://www.juniper.net/documentation/us/en/software/junos/evpn/topics/concept/protocols-evpn-vxlan.html

Junos can run OSPF, IS-IS, and BGP on IRB interfaces in EVPN-VXLAN designs. This is useful when a firewall, load balancer, or CE router forms a real routing adjacency at the overlay edge. A healthy IRB adjacency still does not prove remote EVPN/VNI reachability.

### 18. Juniper — Type-5 subnet routes as a scaling boundary

**Source:** https://www.juniper.net/documentation/us/en/software/junos/release-notes/25.4/junos-release-notes-25.4r1/topics/new-features/feature-descriptions/evpn-9.html

For large stretched fabrics, Juniper documents policy approaches that allow core devices to retain host specificity while lower tiers consume subnet Type-5 reachability. Route granularity is an architectural scaling choice, not merely a BGP configuration detail.

### 19. FRRouting — EVPN correctness includes Linux kernel state

**Source:** https://docs.frrouting.org/en/latest/evpn.html

FRR maps L2VNIs to MAC-VRFs and L3VNIs to IP-VRFs while relying on Linux bridge, VXLAN, SVI, VRF, FDB, and neighbor state. A correct BGP EVPN table therefore does not prove the Linux forwarding objects are wired correctly.

```text
show bgp l2vpn evpn
ip link
bridge fdb show
ip neigh
ip route show vrf <vrf>
```

### 20. FRRouting — OSPF redistribution: route maps, E1/E2, Type-5 and Type-7

**Source:** https://docs.frrouting.org/en/latest/ospfd.html

FRR can redistribute BGP, connected, EIGRP, IS-IS, RIP, static and other sources into OSPF using route maps and explicit metric/metric-type policy. Normal external-capable areas receive Type-5 LSAs; NSSAs use Type-7; stub areas intentionally suppress external LSAs.

### 21. FRRouting — IS-IS Segment Routing: capability matrices matter

**Source:** https://docs.frrouting.org/en/stable-10.0/isisd.html

FRR supports IS-IS Segment Routing for the MPLS data plane with Prefix-SIDs, SRGB configuration and node MSD. Documentation also lists feature limitations in the referenced release. 'Standards-based' does not mean every optional SR feature has identical support on Cisco, Juniper and FRR.

---

## Original Source Figures / Visual References

### Cisco — EVPN VXLAN fabric topology

[Open source](https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst_standalones/Multihoming/multihoming-in-bgp-evpn-vxlan-fabric/routed-overlay-mh/routed-overlay-network-reference-configuration.html)

**What to notice:** separate access/multihoming state, underlay routing, and tenant overlay mappings.

### Fortinet — Dual eBGP paths feeding SD-WAN

![Fortinet dual eBGP SD-WAN topology](https://fortinet.grazitti.com/fortinet-kb-production/api/uploads/f463303c.png)

[Original article](https://community.fortinet.com/fortigate-3/technical-tip-configuring-sd-wan-traffic-steering-with-bgp-learned-routes-229549)

**What to notice:** two BGP peers are not equivalent to two installed forwarding paths; multipath eligibility is the missing middle step.

### Palo Alto Networks — Redistribution profile visual

![PAN-OS No-Redistribution profile](https://live.paloaltonetworks.com/t5/image/serverpage/image-id/57951i89F9808DD1BFC786/image-size/medium/is-moderation-mode/true?px=900&v=v2)

[Original discussion](https://live.paloaltonetworks.com/t5/general-topics/how-to-filter-routes-being-exported-to-bgp-neighbor/td-p/578873)

**What to notice:** global redistribution exclusion and peer-specific export policy are different stages.

### Arista — EVPN/VXLAN IRB topology

![Arista EVPN L3 topology](https://www.arista.com/assets/data/images/EVPN%20L3%20Basic%20Diagram.jpg)

[Original sample configurations](https://www.arista.com/en/um-eos/eos-sample-configurations)

### Aruba/HPE, Juniper and FRR

- Aruba/HPE VSX EVPN logical-VTEP section: https://www.arubanetworks.com/techdocs/AOS-CX/10.15/PDF/vsx.pdf
- Juniper EVPN-VXLAN IRB figures: https://www.juniper.net/documentation/us/en/software/junos/evpn/topics/concept/protocols-evpn-vxlan.html
- FRR EVPN Linux architecture: https://docs.frrouting.org/en/latest/evpn.html

---

## Multi-Vendor Translation Guide

| Engineering question | Portable design rule |
|---|---|
| Redistribution | Prove the source route is an eligible RIB candidate before debugging destination-protocol advertisement. |
| Loop prevention | Preserve route origin with tags, communities, domain metadata, or equivalent policy and deny re-entry. |
| BGP next hop | A best BGP/EVPN route is unusable until its next hop recursively resolves. |
| EVPN/VXLAN | Separate EVPN control plane from VTEP transport, VNI/VRF mapping, multichassis state, and data-plane programming. |
| RIB/FIB | Protocol-table visibility is not equivalent to forwarding installation. |
| Multichassis | Validate both local pair state and standards-visible EVPN state. |
| MTU/BUM | A correct control plane can still suffer encapsulation MTU or inefficient BUM replication. |

## Redistribution Loop-Prevention Pattern

1. Identify the route's native source domain.
2. Filter the exact prefixes that are permitted to cross the boundary.
3. Attach durable origin metadata—route tag, community, or domain attribute.
4. Assign a meaningful destination-protocol metric/preference.
5. At every return boundary, reject routes carrying the original-source marker.
6. Test both positive and negative cases.
7. Do not rely only on administrative distance/route preference; it selects among local candidates but does not preserve route origin.

## Evidence-First Troubleshooting Playbook

1. **Physical / L2:** link, counters, VLAN/trunk, LACP/MLAG/vPC/VSX, MTU.
2. **Adjacency:** OSPF/OSPFv3, EIGRP, IS-IS, BGP/EVPN, BFD.
3. **Candidate route:** confirm source-protocol presence and path type.
4. **Policy boundary:** route-map, prefix list, tag/community, RD/RT import/export.
5. **RIB selection:** identify the winning candidate and why.
6. **Recursion / FIB:** resolve next hop/VTEP and verify forwarding programming.
7. **Overlay / multichassis:** VNI/VRF, ESI, MAC/ARP/ND, Type-2/3/5, BUM, VSX/MLAG state.
8. **Platform data plane:** hardware offload or Linux bridge/FDB/neigh state.
9. **Service path:** prove actual packet forwarding and application/SLA health.

> **Rule:** the first missing or incorrect state is the failure boundary.

---

# 50-Question Cumulative Exam

The interactive HTML version contains per-question Check Answer controls and final grading. The GitHub Markdown version preserves the questions and review answers for repository study.

### 1. Two FortiGate eBGP sessions are Established, but only one next hop is installed for a destination. What must happen before SD-WAN can use both paths?

- A. Both paths must satisfy multipath criteria and be installed in the RIB
- B. Increase OSPF priority
- C. Change VXLAN VNI
- D. Enable STP root guard

<details><summary>Answer</summary>**A.** SD-WAN can steer only across forwarding paths routing has actually installed.</details>

### 2. Why does Cisco's hierarchical eBGP EVPN design preserve the original VTEP next hop through the spine?

- A. So remote leaves can resolve and encapsulate directly toward the actual VTEP
- B. So the spine decapsulates every VXLAN packet
- C. To disable recursion
- D. To replace EVPN with OSPF

<details><summary>Answer</summary>**A.** The spine remains primarily a control-plane transit point while the remote leaf resolves the real VTEP.</details>

### 3. A VSX pair uses separate BGP session addresses but one logical VTEP address. What does that prove?

- A. Control-plane identity and forwarding identity can be different abstractions
- B. Both BGP speakers must share one router ID
- C. VSX has one CPU
- D. The underlay is unnecessary

<details><summary>Answer</summary>**A.** AOS-CX separates the independent BGP speakers from the common data-plane VTEP identity.</details>

### 4. What changes when EVPN-VXLAN uses an IPv6 underlay?

- A. VTEP recursive reachability and outer IP transport use IPv6 while EVPN remains the overlay control plane
- B. EVPN route types disappear
- C. VXLAN uses TCP
- D. BGP is no longer supported

<details><summary>Answer</summary>**A.** The transport address family changes, not the core EVPN overlay model.</details>

### 5. Why can FRR show correct EVPN routes while forwarding still fails?

- A. Linux bridge/SVI/VRF/kernel state can be wrong even when BGP EVPN is correct
- B. FRR never programs Linux
- C. EVPN has no data plane
- D. BGP must use RIP

<details><summary>Answer</summary>**A.** FRR relies on Linux kernel forwarding objects in addition to the BGP control plane.</details>

### 6. Why can a single-gateway centralized EVPN design create unnecessary BUM traffic with redundant VTEP identities?

- A. Both physical and virtual VTEP identities can enter the floodset and receive duplicate replication
- B. BGP sends every packet twice
- C. VXLAN has no split horizon
- D. OSPF duplicates MAC routes

<details><summary>Answer</summary>**A.** Floodset membership can duplicate BUM replication even when route control is correct.</details>

### 7. A route is present in the local PAN-OS BGP RIB but absent only from one peer. Which policy boundary is most likely?

- A. Peer/group BGP export policy
- B. Redistribution admission into BGP
- C. OSPF DR election
- D. VXLAN MTU

<details><summary>Answer</summary>**A.** The route already passed redistribution and local BGP selection.</details>

### 8. How does an NSSA affect an FRR OSPF redistributed route?

- A. The external is represented as a Type-7 inside the NSSA
- B. The route becomes EVPN Type-5
- C. The route is dropped because NSSA supports no externals
- D. The route becomes iBGP

<details><summary>Answer</summary>**A.** NSSA uses Type-7 LSAs for locally introduced external routes.</details>

### 9. What does AOS-CX `route-redistribute active-routes-only` change?

- A. Only routes selected for forwarding are eligible for redistribution
- B. All protocol database entries are redistributed
- C. Only static routes are allowed
- D. It disables route maps

<details><summary>Answer</summary>**A.** It makes active RIB status part of redistribution eligibility.</details>

### 10. Why are high OSPF route-tag values risky on affected FortiOS versions?

- A. A documented conversion defect can alter the tag and break downstream policy
- B. OSPF supports only 8-bit tags
- C. BGP cannot carry route tags
- D. High tags change AS_PATH

<details><summary>Answer</summary>**A.** Broken provenance metadata can invalidate loop-prevention policy.</details>

### 11. Why must EVPN instance state match across all-active multihoming VTEPs?

- A. Inconsistency can produce partial service state and traffic blackholing
- B. BGP requires identical hostnames
- C. VTEPs must share the same management IP
- D. STP elects only one VTEP

<details><summary>Answer</summary>**A.** The fabric expects the redundant VTEPs to represent the same service consistently.</details>

### 12. Why would an engineer run BGP or OSPF directly on an EVPN IRB?

- A. To form routed adjacencies to appliances/CEs while the fabric provides overlay connectivity
- B. To replace VXLAN UDP encapsulation
- C. To advertise STP roots
- D. To create MPLS labels automatically

<details><summary>Answer</summary>**A.** The IRB can be a real routing-protocol boundary.</details>

### 13. What architectural problem does an EVPN multi-domain DCI gateway resemble?

- A. A redistribution boundary where route provenance must prevent re-entry
- B. A pure Layer-2 hub
- C. A DHCP relay
- D. A spanning-tree root

<details><summary>Answer</summary>**A.** Re-origination across domains creates the same provenance/loop problem as redistribution.</details>

### 14. Why can an OSPF policy migration to PAN-OS Advanced Routing Engine silently change behavior?

- A. Legacy path-type/area matches do not map one-for-one to the newer redistribution model
- B. OSPF is unsupported
- C. BGP becomes mandatory
- D. VLAN IDs change

<details><summary>Answer</summary>**A.** Policy semantics—not merely syntax—must be reconstructed.</details>

### 15. What is the main design caution with FRR IS-IS Segment Routing?

- A. Standards-based interop exists but optional capabilities/limitations must be verified
- B. FRR cannot run IS-IS
- C. SR requires VXLAN
- D. Only RIP can advertise Prefix-SIDs

<details><summary>Answer</summary>**A.** Feature-name parity is not feature-capability parity.</details>

### 16. Why advertise subnet Type-5 routes to access/distribution instead of every host route?

- A. To reduce route-table state and improve scale
- B. To disable routing
- C. To make VXLAN Layer 2 only
- D. To force all traffic through the core

<details><summary>Answer</summary>**A.** Route granularity is a scaling design choice.</details>

### 17. What does the EOS control-plane/data-plane model teach?

- A. A route in the routing table does not by itself prove hardware forwarding
- B. The control plane forwards all data packets
- C. Hardware never uses a FIB
- D. Static routes bypass routing

<details><summary>Answer</summary>**A.** Route selection and packet forwarding are separate states.</details>

### 18. A BGP EVPN route exists but its VTEP next hop is unresolved. Where is the first failure boundary?

- A. Underlay recursive next-hop reachability
- B. Route-target import
- C. STP
- D. BGP TCP session only

<details><summary>Answer</summary>**A.** An unresolved next hop prevents usable forwarding even when EVPN import succeeded.</details>

### 19. A FortiGate VXLAN/EVPN fabric has correct routes but unexpected CPU load. Which source-specific area should be checked?

- A. NP7 offload behavior and the VXLAN `learn-from-traffic` setting
- B. OSPF router priority
- C. BGP cluster ID
- D. VLAN native mode only

<details><summary>Answer</summary>**A.** Performance/offload is a separate platform data-plane boundary.</details>

### 20. What should be translated first when moving a Cisco route-map policy to PAN-OS?

- A. The business intent and policy attachment stage
- B. Exact command spelling
- C. Interface names
- D. Router ID

<details><summary>Answer</summary>**A.** Syntax without stage/intent can implement the wrong policy.</details>

### 21. A BGP best path has an unreachable NEXT_HOP. What is the correct design correction?

- A. Make the next hop reachable or apply next-hop-self at the proper boundary
- B. Raise MED
- C. Disable recursion
- D. Redistribute the route into RIP

<details><summary>Answer</summary>**A.** BGP path selection does not eliminate the requirement for recursive reachability.</details>

### 22. What is OSPF Area 0?

- A. The OSPF backbone used for inter-area connectivity
- B. An NSSA-only area
- C. A BGP route-reflector cluster
- D. A VXLAN VNI

<details><summary>Answer</summary>**A.** Area 0 is the OSPF backbone.</details>

### 23. What does an OSPF Type-5 LSA carry?

- A. AS-external reachability
- B. Router-LSA state only
- C. EVPN IP prefixes
- D. BGP communities

<details><summary>Answer</summary>**A.** Type-5 is the normal AS-external LSA.</details>

### 24. What is the E1 versus E2 distinction?

- A. E1 includes internal cost toward the ASBR while E2 generally uses the external metric as dominant
- B. E1 is IPv6 only
- C. E2 exists only in NSSA
- D. E1 cannot be redistributed

<details><summary>Answer</summary>**A.** E1 incorporates internal path cost to the ASBR; E2 generally does not.</details>

### 25. Why does EIGRP need a valid seed metric for redistributed routes?

- A. It needs metric components to create a usable composite metric
- B. BGP requires it
- C. STP uses the metric
- D. VXLAN uses it as a VNI

<details><summary>Answer</summary>**A.** Redistributed routes need an EIGRP metric to participate in DUAL/RIB selection.</details>

### 26. What identifies a loop-free EIGRP feasible successor?

- A. DUAL's feasibility condition
- B. STP root guard
- C. BGP MED
- D. EVPN RT import

<details><summary>Answer</summary>**A.** The feasibility condition provides loop-free alternate-path qualification.</details>

### 27. What is RIP's maximum usable hop count?

- A. 15
- B. 16
- C. 255
- D. 8

<details><summary>Answer</summary>**A.** 16 is unreachable; 15 is the maximum usable metric.</details>

### 28. What does IS-IS Level 2 provide?

- A. Inter-area/backbone routing
- B. ARP suppression
- C. VXLAN encapsulation
- D. BGP authentication

<details><summary>Answer</summary>**A.** Level 2 provides inter-area/backbone connectivity.</details>

### 29. What is MPLS forwarding primarily based on?

- A. Labels
- B. VLAN IDs only
- C. OSPF area numbers
- D. TCP ports

<details><summary>Answer</summary>**A.** MPLS forwards using label operations.</details>

### 30. What isolates customer routing tables in an MPLS L3VPN?

- A. VRFs
- B. STP instances
- C. BFD sessions
- D. Native VLANs

<details><summary>Answer</summary>**A.** VRFs isolate customer routing contexts.</details>

### 31. Which EVPN route type carries MAC/IP endpoint advertisements?

- A. Type 2
- B. Type 3
- C. Type 4 only
- D. Type 5

<details><summary>Answer</summary>**A.** Route Type 2 carries MAC/IP advertisements.</details>

### 32. Which EVPN route type carries IP prefixes?

- A. Type 5
- B. Type 2
- C. Type 3
- D. Type 1

<details><summary>Answer</summary>**A.** Route Type 5 is the IP Prefix route.</details>

### 33. Which EVPN route type commonly supports IMET/BUM membership?

- A. Type 3
- B. Type 5
- C. Type 2
- D. Type 4

<details><summary>Answer</summary>**A.** Type 3 IMET advertisements support BUM replication membership.</details>

### 34. What is the common VXLAN UDP destination port?

- A. 4789
- B. 179
- C. 89
- D. 520

<details><summary>Answer</summary>**A.** VXLAN uses UDP/4789.</details>

### 35. Why is MTU planning important for VXLAN?

- A. Encapsulation adds outer headers that the underlay must carry
- B. BGP updates always require jumbo frames
- C. OSPF hellos are 9 KB
- D. LACP uses VXLAN

<details><summary>Answer</summary>**A.** VXLAN adds encapsulation overhead.</details>

### 36. What is symmetric IRB?

- A. Distributed inter-subnet routing using tenant VRF/L3-VNI semantics at ingress and egress
- B. An STP mode
- C. A BGP route-reflector design
- D. RIP summarization

<details><summary>Answer</summary>**A.** Symmetric IRB uses tenant L3-VNI/VRF routing semantics across the fabric.</details>

### 37. What is an anycast gateway?

- A. The same first-hop gateway IP/MAC presented on multiple VTEPs
- B. A route reflector
- C. An OSPF ASBR
- D. A DHCP server

<details><summary>Answer</summary>**A.** It keeps the first-hop gateway local and consistent across leaf locations.</details>

### 38. Which BGP attribute is normally preferred when higher?

- A. Local Preference
- B. MED
- C. AS_PATH length
- D. Origin code

<details><summary>Answer</summary>**A.** Higher Local Preference is preferred inside the AS.</details>

### 39. Which BGP path is normally preferred when AS_PATH is shorter?

- A. The shorter AS_PATH
- B. The longer AS_PATH
- C. The path with more communities
- D. The highest VNI

<details><summary>Answer</summary>**A.** Shorter AS_PATH is normally preferred after earlier attributes tie.</details>

### 40. Why is a route reflector used?

- A. To reduce iBGP full-mesh requirements
- B. To replace the IGP
- C. To encapsulate VXLAN
- D. To translate OSPF LSAs

<details><summary>Answer</summary>**A.** Route reflection reduces iBGP scaling requirements.</details>

### 41. What is the safest reusable mutual-redistribution pattern?

- A. Tag/classify route origin and deny re-entry on the return boundary
- B. Redistribute everything both ways
- C. Rely only on administrative distance
- D. Set all metrics to zero

<details><summary>Answer</summary>**A.** Preserve provenance and explicitly reject the route when it attempts to return to its source domain.</details>

### 42. Why is administrative distance alone weak loop prevention?

- A. It chooses among local candidates but does not preserve origin or prevent re-entry
- B. It is carried in AS_PATH
- C. It changes TTL
- D. It applies only to static routes

<details><summary>Answer</summary>**A.** Administrative preference is local selection, not route-origin metadata.</details>

### 43. What is the primary risk of indiscriminate Layer-2 stretch?

- A. Expanded BUM, loop and failure domains
- B. BGP stops using TCP
- C. OSPF becomes classful
- D. MPLS labels disappear

<details><summary>Answer</summary>**A.** L2 stretch expands shared failure and flooding scope.</details>

### 44. What must be compatible across vendors for a healthy LACP bundle?

- A. Member characteristics, LACP behavior, VLAN/MTU and bundle intent
- B. Hostnames
- C. BGP ASNs
- D. OSPF router IDs

<details><summary>Answer</summary>**A.** Link/bundle semantics must match; vendor names do not.</details>

### 45. What is LISP's conceptual role in Cisco SD-Access?

- A. Endpoint identity-to-location control-plane mapping
- B. VXLAN encryption
- C. STP root election
- D. MPLS labeling

<details><summary>Answer</summary>**A.** LISP maps endpoint identity to fabric location.</details>

### 46. What is the SD-Access fabric data plane?

- A. VXLAN
- B. RIP
- C. LDP
- D. GRE only

<details><summary>Answer</summary>**A.** SD-Access uses VXLAN for the fabric data plane.</details>

### 47. What is the difference between RIB and FIB?

- A. RIB is routing selection/control state; FIB is programmed forwarding state
- B. They are identical
- C. RIB is Layer 2 only
- D. FIB is BGP-only

<details><summary>Answer</summary>**A.** A selected route must still be translated into forwarding state.</details>

### 48. What does BUM stand for?

- A. Broadcast, Unknown-unicast, Multicast
- B. BGP, Underlay, MPLS
- C. Bridge, Unicast, Metric
- D. Backup, Uplink, Multihop

<details><summary>Answer</summary>**A.** BUM is Broadcast, Unknown-unicast, Multicast traffic.</details>

### 49. What is the strongest evidence-first troubleshooting order?

- A. Adjacency/control plane → route/RIB → recursion/FIB → encapsulation/policy → packet test
- B. Packet test only
- C. GUI then reboot
- D. STP then DNS

<details><summary>Answer</summary>**A.** This sequence identifies the earliest missing state and avoids debugging downstream symptoms first.</details>

### 50. When translating routing policy between vendors, what should be mapped first?

- A. Business intent and policy attachment stage
- B. Exact command spelling
- C. Interface names
- D. Default hostname

<details><summary>Answer</summary>**A.** Equivalent syntax at the wrong stage implements a different policy.</details>

---

## Source Index

1. Cisco hierarchical EVPN multihoming — https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst_standalones/Multihoming/multihoming-in-bgp-evpn-vxlan-fabric/hierarchical-multihoming/configure-ebgp-based-evpn-multihoming-and-fabric-network.html
2. Cisco all-active EVPN restrictions — https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst_standalones/Multihoming/multihoming-in-bgp-evpn-vxlan-fabric/all-active-mode/restriction-for-aa-multihoming.html
3. Cisco routed overlay reference — https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst_standalones/Multihoming/multihoming-in-bgp-evpn-vxlan-fabric/routed-overlay-mh/routed-overlay-network-reference-configuration.html
4. Fortinet BGP + SD-WAN multipath — https://community.fortinet.com/fortigate-3/technical-tip-configuring-sd-wan-traffic-steering-with-bgp-learned-routes-229549
5. Fortinet NP7 VXLAN offload — https://community.fortinet.com/fortigate-3/technical-tip-how-to-enable-np7-hardware-offloading-for-vxlan-over-evpn-traffic-225075
6. Fortinet OSPF/BGP route tags — https://community.fortinet.com/fortigate-3/technical-tip-wrong-route-tag-added-to-bgp-routes-redistributed-from-ospf-214352
7. PAN-OS Advanced Routing Engine filters — https://docs.paloaltonetworks.com/ngfw/networking/advanced-routing/create-filters-for-the-advanced-routing-engine
8. PAN-OS OSPF migration exceptions — https://docs.paloaltonetworks.com/pan-os/u-v/routing-engine-migration-reference/routing-protocol-migration-exceptions/ospf
9. PAN-OS route redistribution — https://docs.paloaltonetworks.com/ngfw/networking/configure-route-redistribution
10. Arista EVPN configuration — https://www.arista.com/en/um-eos/eos-configuring-evpn
11. Arista EVPN VXLAN single-gateway centralized routing — https://www.arista.com/ko/um-eos/eos-evpn-vxlan-single-gateway-centralized-routing
12. Arista data transfer / control-data plane — https://www.arista.com/en/um-eos/eos-data-transfer
13. Aruba/HPE AOS-CX VSX 10.15 — https://www.arubanetworks.com/techdocs/AOS-CX/10.15/PDF/vsx.pdf
14. Aruba/HPE AOS-CX IP Routing 10.15 — https://www.arubanetworks.com/techdocs/AOS-CX/10.15/PDF/ip_route_6300-6400-8100-83xx-9300-10000.pdf
15. Juniper EVPN IPv6 underlay — https://www.juniper.net/documentation/us/en/software/junos/evpn/topics/topic-map/vxlan-ipv6-underlay-overview.html
16. Juniper routing protocols on EVPN IRB — https://www.juniper.net/documentation/us/en/software/junos/evpn/topics/concept/protocols-evpn-vxlan.html
17. Juniper Type-5 scale feature — https://www.juniper.net/documentation/us/en/software/junos/release-notes/25.4/junos-release-notes-25.4r1/topics/new-features/feature-descriptions/evpn-9.html
18. FRR EVPN — https://docs.frrouting.org/en/latest/evpn.html
19. FRR OSPF — https://docs.frrouting.org/en/latest/ospfd.html
20. FRR IS-IS Segment Routing — https://docs.frrouting.org/en/stable-10.0/isisd.html

---

*This Markdown file is the GitHub-readable companion. The emailed `.html` workbook remains the interactive version with per-question Check Answer controls, JavaScript grading, score breakdowns, and image-load fallbacks.*
