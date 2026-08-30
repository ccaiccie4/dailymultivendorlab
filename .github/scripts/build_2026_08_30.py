from pathlib import Path
import re, html

TS='2026-08-30-07-59'
BASE=Path('docs/Daily_Multivendor_Routing_Lab_2026-08-29-08-11.html')
OUT=Path(f'docs/Daily_Multivendor_Routing_Lab_{TS}.html')
s=BASE.read_text(encoding='utf-8')
s=s.replace('2026-08-29-08-11',TS)
s=s.replace('<b>20 detailed lessons</b>','<b>27 detailed lessons</b>')
s=s.replace('<b>21 detailed lessons</b>','<b>28 detailed lessons</b>')

fresh=[
('Cisco','Q-in-VNI: controlled Layer-2 extension across EVPN-VXLAN','Official Cisco IOS XE 26.x — updated 2026-04-10','https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9600/software/release/26-x/configuration_guide/vxlan/26x-bgp-evpn-vxlan-9600-cg/configuring_layer2_overlay_with_Q-in-VNI.html',
'Cisco Q-in-VNI carries multiple customer 802.1Q domains through one EVPN Layer-2 service while preserving the inner customer tag. The ingress edge classifies traffic into a provider S-VLAN, maps that S-VLAN to a Layer-2 VNI, retains the inner C-VLAN header, and sends the frame across the IP fabric in VXLAN. The remote edge maps the VNI back to the provider service and delivers the original customer tag. This is a constrained Layer-2 extension model rather than ordinary routed EVPN.',
'The control-plane and data-plane consequences must be separated. EVPN can correctly advertise MAC reachability while the service is invalid because of a local tunnel-port restriction. Cisco documents that Layer-3 IP routing is not supported on VLANs mapped to the 802.1Q tunnel port, Layer-2 Protocol Tunneling is not supported there, the provider S-VLAN must not collide with a trunk C-VLAN, and overlapping MAC entries across C-VLANs sharing the same mapped S-VLAN are unsupported. A healthy EVPN session therefore does not prove the requested service model is supportable.',
'Troubleshoot from classification outward: verify dot1q-tunnel mode and S-VLAN uniqueness, EVI/L2VNI mapping, RT2 MAC advertisements, recursive reachability to the remote VTEP, and finally a packet capture proving the inner customer tag survives VXLAN encapsulation. If only one customer VLAN fails, inspect classification and bridge-table state before changing BGP.',
'show bgp l2vpn evpn\nshow l2vpn evpn\nshow interface nve1\nshow mac address-table',
'Build two fabric edges carrying C-VLANs 10 and 20 through one S-VLAN/L2VNI. Verify both tags end-to-end, then intentionally reuse the S-VLAN as a trunk C-VLAN and record the first state that becomes inconsistent.'),
('Fortinet','FortiOS 7.6.6 MP-BGP EVPN: control-plane endpoint learning versus flood-and-learn','Official Fortinet FortiOS 7.6.6 Administration Guide','https://docs.fortinet.com/document/fortigate/7.6.6/administration-guide/52499/vxlan-with-mp-bgp-evpn',
'FortiOS EVPN replaces part of classic VXLAN flood-and-learn with a BGP endpoint-control plane. The 7.6.6 guide documents Route Type 2 MAC/IP advertisements, Route Type 3 inclusive multicast routes, ARP suppression, egress replication for BUM, VLAN-based service and single-homing behavior. The exact feature inventory matters because a remote vendor may support additional route types or VRF models that are not present on the FortiOS release in use.',
'EVPN does not remove underlay recursion. A FortiGate can know which remote VTEP owns a MAC/IP while still being unable to send the outer VXLAN packet because the VTEP address has no usable RIB/FIB resolution. Route-target import failure and underlay recursion failure can therefore produce similar user symptoms but different evidence. Verify release-specific capability before assuming Type-5 or symmetric-IRB behavior from another platform applies unchanged.',
'Check BGP EVPN peer state, RT2/RT3 presence, VNI mapping, remote-VTEP routing, ARP-suppression state and BUM replication in that order. If RT2 exists but the VTEP route is missing, stop at underlay recursion. If the VTEP is reachable but endpoint routes never appear, focus on origination/import policy.',
'get router info bgp summary\nget router info bgp network\nget router info routing-table details <remote-vtep>\nshow system vxlan',
'Build two FortiOS VTEPs with one L2VNI. Establish a known-good RT2/RT3 baseline, then withdraw only underlay reachability to the remote VTEP and compare EVPN state with packet forwarding.'),
('Palo Alto Networks','Advanced Routing Engine filters: attachment stage is part of policy meaning','Official PAN-OS / Strata NGFW documentation — verified 2026-08-30','https://docs.paloaltonetworks.com/ngfw/networking/advanced-routing/create-filters-for-the-advanced-routing-engine',
'PAN-OS Advanced Routing Engine supports access lists, prefix lists and redistribution route maps across BGP, OSPFv2/v3 and RIPv2, with BGP-specific AS-path, community and route-map controls. The same prefix logic can be referenced at several different transitions: inbound peer-to-local-BGP-RIB admission, outbound local-BGP-RIB-to-peer advertisement, and source-protocol-to-destination-protocol redistribution. The attachment point is therefore part of the policy semantics.',
'The documentation also calls out sequential rule evaluation and implicit behavior. Most filters end with implicit deny, while AS-path access lists have different implicit behavior; peer settings can override peer-group settings. A syntactically correct prefix list attached at the wrong stage can remove the entire route set. If a route is already in the local BGP RIB but missing from one peer, redistribution has already succeeded and outbound filtering is the narrower boundary.',
'Trace a test prefix through source RIB, redistribution decision, destination protocol RIB, peer export filter and advertised-routes state. Inspect only the policy attached to the first missing transition. This technique is portable to Cisco route-maps, Junos policy-statements, EOS route-maps and FortiOS policies.',
'Network > Routing > Routing Profiles > Filters\nInspect BGP Filtering Profile\nInspect Redistribution Profile / Route Map\nInspect runtime RIB and advertised routes',
'Use one prefix list in a redistribution map and another in BGP outbound filtering. Make one route fail before entering BGP and another fail only at peer export; compare the evidence.'),
('Arista','EVPN Type-5 multi-domain DCI: D-path as redistribution-style provenance','Official Arista EOS 4.36.1F User Manual — verified 2026-08-30','https://www.arista.com/en/um-eos/eos-configuring-evpn',
'EOS can terminate EVPN Type-5 IP-prefix routes from one domain and re-originate them into another while using independent local and remote route distinguishers and route targets. Operationally this behaves like a redistribution boundary, not a transparent route reflector: the DCI gateway creates a new representation of the route in the far domain.',
'Re-origination introduces a loop-prevention requirement. Arista documents domain identifiers, D-path and bgp bestpath d-path so a route can retain domain provenance. Without durable provenance, a tenant prefix can leave one domain and return through another DCI gateway. Local preference can choose among candidates but does not preserve origin, so it cannot substitute for loop avoidance.',
'Compare the route before and after the DCI gateway: RD, RT, next hop, domain identifiers/D-path, VRF import and recursive VTEP reachability. If duplicate candidates appear, determine whether they are legitimate alternate domains or re-entry of the same origin before tuning ordinary BGP best-path attributes.',
'show bgp evpn\nshow bgp evpn route-type ip-prefix\nshow ip route vrf <vrf>\nrouter bgp <asn>\n bgp bestpath d-path',
'Create two EVPN domains and two DCI gateways. Re-originate one tenant prefix in both directions, verify D-path loop avoidance, then remove that provenance policy and observe the duplicate-route signature.'),
('Aruba/HPE','VSX EVPN: two control-plane identities represented by one logical VTEP','Official HPE Aruba Networking AOS-CX 10.15 VSX Guide','https://www.arubanetworks.com/techdocs/AOS-CX/10.15/PDF/vsx.pdf',
'AOS-CX VSX makes control-plane versus forwarding identity explicit. The two peers act as independent BGP routing entities toward spines and remote VTEPs, but in the datapath they can represent one logical VTEP. Different addresses establish BGP sessions; a common IP is used as the VTEP next hop. Remote devices therefore see a stable forwarding identity while each chassis retains unique routing identity.',
'The VSX guide also explains selective BGP synchronization. Prefix lists, communities and route maps can synchronize, but router ID, cluster ID and update-source remain unique. Some next-hop-setting actions are intentionally not synchronized because each peer may require different local next-hop values. Thus VSX sync is not a byte-for-byte configuration clone and should not be validated as one.',
'Compare both peers side-by-side: VSX status, individual BGP sessions, EVPN advertisements, common logical-VTEP reachability, access LAG state and actual forwarding. Then compare synchronized policy objects and the identity-sensitive fields that are designed to differ.',
'show vsx status\nshow bgp l2vpn evpn\nshow evpn\nshow ip route <logical-vtep>\nshow running-config bgp',
'Fail one peer BGP uplink while preserving the common VTEP through the partner; then separately break VSX/access state while both BGP sessions remain healthy. Document the different state boundaries.'),
('Juniper','EVPN Type-2/Type-5 coexistence: route preference as a PFE scaling control','Official Junos EVPN documentation — verified 2026-08-30','https://www.juniper.net/documentation/us/en/software/junos/evpn/topics/concept/evpn-t2-t5-coexist-evpn-vxlan.html',
'Junos can learn both Type-2 MAC+IP and Type-5 IP-prefix routes for the same destination. Those are distinct EVPN routes and can consume distinct Packet Forwarding Engine next hops. Juniper therefore documents a coexistence preference algorithm that chooses the forwarding representation appropriate for the destination while conserving PFE resources.',
'Type-2 remains valuable for locally attached ESI hosts and proxy-ARP/ARP-suppression information, while Type-5 is generally the scalable routed-overlay representation for remote prefixes. A non-preferred EVPN route can remain visible in bgp.evpn.0 even though it is not installed in the tenant inet table. Treating that intentional non-installation as a routing failure leads to unnecessary policy changes.',
'Compare bgp.evpn.0, the VRF inet table and the actual forwarding next hop. Determine whether the route is intentionally non-preferred or absent because import/VNI policy failed. At scale, correlate route-type coexistence with PFE next-hop resources rather than examining BGP route count alone.',
'show route table bgp.evpn.0\nshow route table <vrf>.inet.0\nshow evpn database',
'Advertise the same destination as Type-2 and Type-5. Observe preference, remove Type-5 and confirm Type-2 fallback, then restore Type-5 and compare forwarding next-hop state.'),
('FRRouting','FRR EVPN: BGP correctness plus Linux bridge/FDB/neighbor correctness','Official FRRouting latest EVPN documentation — verified 2026-08-30','https://docs.frrouting.org/en/latest/evpn.html',
'FRR provides a transparent demonstration of control-plane versus dataplane boundaries. BGP EVPN exchanges MAC/IP and prefix reachability, zebra translates routing state into kernel objects, and Linux bridge/VXLAN/VRF devices provide actual forwarding. A correct EVPN route is therefore only one checkpoint in the service lifecycle.',
'A remote RT2 can appear in show bgp l2vpn evpn while the Linux bridge FDB lacks the MAC, the VXLAN device belongs to the wrong bridge/VNI, the neighbor entry is absent, or the VRF association is wrong. Those are not route-target problems; they are FRR/zebra/kernel integration failures. This is the software equivalent of a hardware NOS having a correct RIB but a broken ASIC/FIB entry.',
'Verify the BGP EVPN route, show evpn vni, zebra route/nexthop state, ip -d link, bridge FDB, neighbor state and a packet capture. Stop at the first mismatch instead of rewriting BGP policy after the EVPN control plane has already proven correct.',
'show bgp l2vpn evpn\nshow evpn vni\nip -d link show\nbridge fdb show\nip neigh show',
'Build two Linux VTEPs with FRR and a known-good RT2 baseline. Remove only the bridge-to-VXLAN/VLAN association while leaving BGP untouched, then compare control-plane and kernel evidence.')]

def e(x): return html.escape(x, quote=True)
articles=[]
for i,(vendor,title,classification,url,a,b,c,cmds,lab) in enumerate(fresh,1):
    articles.append(f'''<article class="lesson fresh"><div><span class="badge">Fresh 2026-08-30</span><span class="badge">{e(vendor)}</span><span class="badge">{e(classification)}</span></div><h3>Fresh {i}. {e(title)}</h3><p><b>Exact source:</b> <a href="{e(url)}">{e(url)}</a></p><h4>Problem, architecture and intent</h4><p>{e(a)}</p><h4>Control-plane/data-plane mechanics and caveats</h4><p>{e(b)}</p><h4>Evidence-first troubleshooting workflow</h4><p>{e(c)}</p><details open><summary>Verification commands / evidence</summary><div class="cmd"><pre>{e(cmds)}</pre></div></details><details><summary>Reproducible lab</summary><p>{e(lab)}</p></details><div class="figure"><div class="fallback" style="display:block"><b>Technical figure reference</b><p>The source contains technical figures or topology material, but its interface did not expose a stable direct raster URL suitable for durable hot-linking. The original source is linked rather than inventing an image URL.</p><p class="small"><b>Source article:</b> <a href="{e(url)}">{e(url)}</a><br><b>Original image URL:</b> No stable direct raster URL exposed; open the source article to view the original figure in context.</p></div></div><div class="remember"><b>Active recall:</b> Identify the first state boundary that can fail while the previous checkpoint still looks healthy.</div></article>''')
marker='<section id="lessons"><h2>Detailed Technical Lessons</h2>'
insert='<div class="card callout"><b>Fresh research for this run:</b> Seven newly researched lessons appear first; the prior source-derived lessons remain below for cumulative study and spaced repetition.</div>'+''.join(articles)
if marker not in s: raise SystemExit('lessons marker missing')
s=s.replace(marker,marker+insert,1)

# Replace first seven current questions; keep established answer-position balance 0,1,2,3,0,1,2.
newq=[
('Current/Cisco','1. A Q-in-VNI service must carry multiple customer C-VLANs through one EVPN L2VNI while preserving the customer tags. Which design action is central?',['Map a provider S-VLAN to the L2VNI and preserve the inner C-VLAN tag','Terminate each C-VLAN into a routed SVI before VXLAN','Advertise every C-VLAN as Type-5 only','Replace the customer tag with an MPLS label']),
('Current/Fortinet','2. FortiOS has a valid EVPN RT2 route, but the remote VTEP is absent from the underlay RIB. What is the first failure boundary?',['Route-target import','Recursive underlay reachability to the VTEP','ARP suppression','BGP router-ID selection']),
('Current/PAN-OS','3. A prefix is already in the local PAN-OS BGP RIB but missing only from one peer. Which stage is the narrowest first check?',['Source OSPF adjacency','Redistribution admission into BGP','Outbound BGP filtering or route-map for that peer/group','Security policy']),
('Current/Arista','4. Why does D-path matter when an Arista DCI gateway re-originates EVPN Type-5 routes between domains?',['It computes VXLAN UDP checksums','It replaces route targets','It elects the MLAG primary','It carries domain provenance for loop avoidance']),
('Current/Aruba','5. Why can two VSX peers use different BGP session addresses while remote VTEPs see one common next hop?',['Control-plane identity and data-plane VTEP identity are intentionally separate','The peers share one BGP process','VSX removes the underlay RIB','Both peers must use identical router IDs']),
('Current/Juniper','6. Why does Junos choose between coexisting EVPN Type-2 and Type-5 representations for the same destination?',['To force all traffic to Type-2','To conserve PFE next-hop resources and choose the appropriate representation','To disable ARP suppression','To make bgp.evpn.0 identical to inet.0']),
('Current/FRR','7. FRR shows the expected EVPN route, but bridge fdb show lacks the remote MAC. What does this most directly suggest?',['The route must be redistributed into OSPF','The AS_PATH is necessarily wrong','A control-plane-to-Linux-dataplane integration problem','The VNI must equal the VLAN ID'])]
correct=[0,1,2,3,0,1,2]
for n,(domain,stem,opts) in enumerate(newq,1):
    labels=''.join(f'<label><input type="radio" name="q{n}" value="{j}"> <b>{chr(65+j)}.</b> {e(o)}</label>' for j,o in enumerate(opts))
    block=f'<div class="q"><span class="badge">{e(domain)}</span><h3>{e(stem)}</h3>{labels}<button onclick="checkQ({n})">Check Answer</button><div id="fb{n}" class="feedback"></div><span id="why{n}" style="display:none">Correct answer: {e(opts[correct[n-1]])}. The distractors target another state boundary, unrelated mechanism, or later-stage remediation.</span></div>'
    pat=re.compile(r'<div class="q"><span class="badge">[^<]*</span><h3>'+str(n)+r'\..*?<span id="why'+str(n)+r'" style="display:none">.*?</span></div>',re.S)
    s,c=pat.subn(block,s,count=1)
    if c!=1: raise SystemExit(f'question {n} replacement failed')

# Update current-domain labels in META without changing answer keys.
domains={1:'Current/Cisco',2:'Current/Fortinet',3:'Current/PAN-OS',4:'Current/Arista',5:'Current/Aruba',6:'Current/Juniper',7:'Current/FRR'}
for n,d in domains.items():
    s=re.sub(rf'"{n}": \{{"domain": "[^"]+", "checked": false\}}',f'"{n}": {{"domain": "{d}", "checked": false}}',s,count=1)

OUT.write_text(s,encoding='utf-8')
# hard gates
if s.count('class="q"')!=50 or s.count('Check Answer')!=50: raise SystemExit('exam count validation failed')
if s.count('class="lesson')<27: raise SystemExit('lesson count validation failed')
for bad in ('DecompressionStream','const b=`','gzip.decompress','base64.b64decode'):
    if bad in s: raise SystemExit('compression wrapper detected: '+bad)
if TS not in s: raise SystemExit('timestamp validation failed')
print(f'Built {OUT} bytes={OUT.stat().st_size} lessons={s.count(chr(99)+chr(108)+chr(97)+chr(115)+chr(115)+"=\"lesson")} questions=50')
