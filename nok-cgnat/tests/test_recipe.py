import json
import unittest
from pathlib import Path

import yaml


RECIPE = Path(__file__).resolve().parents[1]


class CgnatRecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.topology = yaml.safe_load((RECIPE / "topo.yaml").read_text())
        cls.nodes = cls.topology["topology"]["nodes"]
        cls.links = cls.topology["topology"]["links"]

    def test_srsim_version_and_isa_iom_profile(self):
        srsim_nodes = [node for node in self.nodes.values() if node.get("kind") == "nokia_srsim"]
        self.assertTrue(srsim_nodes)
        self.assertTrue(all(node["image"].endswith(":26.7.R1") for node in srsim_nodes))
        self.assertNotIn("esa-stub", self.nodes)

        for router in ("cgnat1", "cgnat2"):
            cpm = self.nodes[router]
            iom = self.nodes[f"{router}-iom"]
            self.assertEqual(cpm["env"]["NOKIA_SROS_CHASSIS"], "sr-1e")
            self.assertEqual(iom["network-mode"], f"container:{router}")
            self.assertEqual(iom["env"]["NOKIA_SROS_CARD"], "iom-e")
            self.assertEqual(iom["env"]["NOKIA_SROS_MDA_2"], "isa2-bb")
            self.assertEqual(iom["license"], "srsim-lic-26.7.txt")
            endpoints = [endpoint for link in self.links for endpoint in link["endpoints"]]
            for port in ("1/1/1", "1/1/2", "1/1/3"):
                self.assertIn(f"{router}-iom:{port}", endpoints)

    def test_nat_routers_have_operational_vrrp_and_sync_config(self):
        for router, link_local, peer in (
            ("cgnat1", "fe80::2", "10.255.255.2"),
            ("cgnat2", "fe80::3", "10.255.255.1"),
        ):
            config = (RECIPE / self.nodes[router]["startup-config"]).read_text()
            self.assertEqual(config.count("{"), config.count("}"))
            self.assertIn("card-type iom-e", config)
            self.assertIn("mda-type isa2-bb", config)
            self.assertIn("mda 1/2 { }", config)
            self.assertNotIn("esa 1", config)
            self.assertIn(f"address {link_local}", config)
            self.assertIn("backup [fe80::1 2001:db8:1::1]", config)
            self.assertIn("use-virtual-mac true", config)
            self.assertIn(f"next-hop {peer} {{ admin-state enable }}", config)

    def test_core_advertises_inet_and_enables_nat_return_routes(self):
        config = (RECIPE / "configs/ne/core.txt").read_text()
        self.assertIn('interface "INET" { passive true }', config)
        self.assertIn("next-hop 192.0.2.1 { admin-state enable preference 10 }", config)
        self.assertIn("next-hop 192.0.2.5 { admin-state enable preference 20 }", config)

    def test_dashboards_query_the_mda_metrics(self):
        dashboards = RECIPE / "grafana-dashboards"
        for name in ("cgnat-isa-and-icr.json", "cgnat-pools-and-dslite.json"):
            dashboard = json.loads((dashboards / name).read_text())
            expressions = [
                target["expr"]
                for panel in dashboard["panels"]
                for target in panel.get("targets", [])
                if "expr" in target
            ]
            hardware_queries = [
                expr for expr in expressions
                if "state_isa_nat_group_mda_" in expr or "state_isa_nat_group_esa_" in expr
            ]
            self.assertTrue(any("state_isa_nat_group_mda_" in expr for expr in hardware_queries), name)
            self.assertFalse(any("state_isa_nat_group_esa_" in expr for expr in expressions), name)

    def test_dashboard_resources_refresh_cached_content(self):
        resources = RECIPE / "nok-manifests/grafana/dashboards"
        for name in ("cgnat-isa-and-icr.yaml", "cgnat-pools-and-dslite.yaml"):
            resource = yaml.safe_load((resources / name).read_text())
            self.assertEqual(resource["spec"]["contentCacheDuration"], "1m", name)
            self.assertEqual(resource["spec"]["resyncPeriod"], "1m", name)

    def test_subscriber_traffic_uses_separate_forward_and_reverse_udp(self):
        lan = (RECIPE / "configs/hosts/lan.sh").read_text()
        internet = (RECIPE / "configs/hosts/inet.sh").read_text()
        self.assertIn("REVERSE_PORT=$((IPERF_PORT + 3))", lan)
        self.assertIn('"$REVERSE_PORT" -b 4k -l 100 -t 86400 -R', lan)
        self.assertNotIn("--bidir", lan)
        self.assertIn("for port in 5204 5205 5206", internet)


if __name__ == "__main__":
    unittest.main()
