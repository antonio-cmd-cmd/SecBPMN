"""
Web App Evaluation Script - BPMN Threat Analysis & Mitigation
=============================================================

This script tests the full web app pipeline:
1. Load a test BPMN
2. Analyse threats
3. Generate the mitigated BPMN
4. Download the mitigated BPMN
5. Compare original vs mitigated BPMN
"""

import requests
import json
import os
import time
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import tempfile

# Imports for advanced BPMN metrics
try:
    import pm4py
    from pm4py.objects.bpmn.obj import BPMN
    from pm4py.objects.bpmn.importer import importer as bpmn_importer
    from pm4py.objects.conversion.bpmn import converter as bpmn_converter
    from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
    from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness
    from pm4py.algo.simulation.playout.petri_net import algorithm as simulator
    import networkx as nx
    PM4PY_AVAILABLE = True
except ImportError:
    print("WARNING: pm4py or networkx not available. Advanced metrics will not be computed.")
    print("Install with: pip install pm4py networkx")
    PM4PY_AVAILABLE = False

# Import per plotting
try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("WARNING: matplotlib or numpy not available. Charts will not be generated.")
    print("Install with: pip install matplotlib numpy")
    MATPLOTLIB_AVAILABLE = False


class BPMNEvaluator:
    """Evaluator for the BPMN threat-analysis and mitigation web app."""
    
    def __init__(self, backend_url="http://localhost:8000", output_dir="evaluation_results"):
        """
        Initialise the evaluator.

        Args:
            backend_url: Backend base URL.
            output_dir: Directory for saving results.
        """
        self.backend_url = backend_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Timestamp for this run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(exist_ok=True)

        # Evaluation results
        self.results = {
            "timestamp": self.timestamp,
            "backend_url": backend_url,
            "steps": {},
            "timings": {},
            "analysis": {}
        }
        
    def log(self, message, level="INFO"):
        """Print a timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def save_file(self, content, filename, subdir=None):
        """Save content to a file inside the session output directory."""
        if subdir:
            target_dir = self.session_dir / subdir
            target_dir.mkdir(exist_ok=True)
        else:
            target_dir = self.session_dir
            
        filepath = target_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
        
    def check_backend_health(self):
        """Check that the backend server is reachable."""
        self.log("Checking backend connection...")
        try:
            response = requests.get(f"{self.backend_url}/docs")
            if response.status_code == 200:
                self.log("✓ Backend reachable", "SUCCESS")
                return True
            else:
                self.log(f"✗ Backend returned status {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"✗ Cannot reach backend: {e}", "ERROR")
            return False
            
    def load_test_bpmn(self, bpmn_path):
        """
        Load the test BPMN file.

        Args:
            bpmn_path: Path to the test BPMN file.

        Returns:
            BPMN file content as a string.
        """
        self.log(f"Loading test BPMN from: {bpmn_path}")

        if not os.path.exists(bpmn_path):
            self.log(f"✗ BPMN file not found: {bpmn_path}", "ERROR")
            return None

        with open(bpmn_path, 'r', encoding='utf-8') as f:
            bpmn_content = f.read()

        # Save a copy of the original BPMN
        self.save_file(bpmn_content, "original_bpmn.xml", "bpmn_files")

        self.log(f"✓ BPMN loaded ({len(bpmn_content)} characters)", "SUCCESS")
        self.results["steps"]["load_bpmn"] = {
            "success": True,
            "file_path": bpmn_path,
            "file_size": len(bpmn_content)
        }
        
        return bpmn_content
        
    def validate_bpmn(self, bpmn_path):
        """
        Validate a BPMN file via the /validate-bpmn/ endpoint.

        Args:
            bpmn_path: Path to the BPMN file.

        Returns:
            Validation result dict, or None on failure.
        """
        self.log("Step 1: BPMN validation...")
        start_time = time.time()
        
        try:
            with open(bpmn_path, 'rb') as f:
                files = {'file': (os.path.basename(bpmn_path), f, 'application/xml')}
                response = requests.post(
                    f"{self.backend_url}/validate-bpmn/",
                    files=files
                )
                
            elapsed_time = time.time() - start_time
            self.results["timings"]["validate_bpmn"] = elapsed_time
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✓ Validation completed in {elapsed_time:.2f}s", "SUCCESS")

                self.save_file(
                    json.dumps(result, indent=2),
                    "validation_result.json",
                    "validation"
                )

                self.results["steps"]["validate_bpmn"] = {
                    "success": True,
                    "valid": result.get("valid", False),
                    "message": result.get("message", ""),
                    "elapsed_time": elapsed_time
                }

                return result
            else:
                self.log(f"✗ Validation error: {response.status_code}", "ERROR")
                self.results["steps"]["validate_bpmn"] = {
                    "success": False,
                    "error": response.text
                }
                return None

        except Exception as e:
            self.log(f"✗ Error during validation: {e}", "ERROR")
            self.results["steps"]["validate_bpmn"] = {
                "success": False,
                "error": str(e)
            }
            return None

    def analyze_threats(self, bpmn_path, context, principles):
        """
        Analyse threats in the BPMN via the /analyze-xml/ endpoint.

        Args:
            bpmn_path: Path to the BPMN file.
            context: Process context dict.
            principles: Security principles list.

        Returns:
            Threat analysis result dict, or None on failure.
        """
        self.log("Step 2: Threat analysis...")
        start_time = time.time()
        
        try:
            with open(bpmn_path, 'rb') as f:
                files = {'file': (os.path.basename(bpmn_path), f, 'application/xml')}
                data = {
                    'context': json.dumps(context),
                    'principles': json.dumps(principles)
                }
                
                response = requests.post(
                    f"{self.backend_url}/analyze-xml/",
                    files=files,
                    data=data
                )
                
            elapsed_time = time.time() - start_time
            self.results["timings"]["analyze_threats"] = elapsed_time
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✓ Analysis completed in {elapsed_time:.2f}s", "SUCCESS")

                self.save_file(
                    json.dumps(result, indent=2),
                    "threat_analysis_raw.json",
                    "threat_analysis"
                )

                if 'doc' in result:
                    self.save_file(
                        result['doc'],
                        "threat_analysis.md",
                        "threat_analysis"
                    )

                if 'element_ids' in result:
                    self.save_file(
                        json.dumps(result['element_ids'], indent=2),
                        "threat_element_ids.json",
                        "threat_analysis"
                    )

                self.results["steps"]["analyze_threats"] = {
                    "success": True,
                    "element_ids_count": len(result.get('element_ids', [])),
                    "elapsed_time": elapsed_time
                }

                return result
            else:
                self.log(f"✗ Analysis error: {response.status_code}", "ERROR")
                self.results["steps"]["analyze_threats"] = {
                    "success": False,
                    "error": response.text
                }
                return None

        except Exception as e:
            self.log(f"✗ Error during analysis: {e}", "ERROR")
            self.results["steps"]["analyze_threats"] = {
                "success": False,
                "error": str(e)
            }
            return None
            
    def generate_mitigated_bpmn(self, bpmn_path, context, principles, threat_analysis):
        """
        Generate the mitigated BPMN via the /generate-mitigated-bpmn/ endpoint.

        Args:
            bpmn_path: Path to the original BPMN file.
            context: Process context dict.
            principles: Security principles list.
            threat_analysis: Threat analysis markdown string.

        Returns:
            Mitigated BPMN as an XML string, or None on failure.
        """
        self.log("Step 3: Generating mitigated BPMN...")
        start_time = time.time()
        
        try:
            with open(bpmn_path, 'rb') as f:
                files = {'file': (os.path.basename(bpmn_path), f, 'application/xml')}
                data = {
                    'context': json.dumps(context),
                    'principles': json.dumps(principles),
                    'threat_analysis': threat_analysis
                }
                
                response = requests.post(
                    f"{self.backend_url}/generate-mitigated-bpmn/",
                    files=files,
                    data=data
                )
                
            elapsed_time = time.time() - start_time
            self.results["timings"]["generate_mitigated_bpmn"] = elapsed_time
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success', False):
                    mitigated_bpmn = result.get('mitigated_bpmn', '')

                    self.log(f"✓ Mitigated BPMN generated in {elapsed_time:.2f}s", "SUCCESS")

                    self.save_file(
                        mitigated_bpmn,
                        "mitigated_bpmn.xml",
                        "bpmn_files"
                    )

                    self.save_file(
                        json.dumps(result, indent=2),
                        "mitigation_result.json",
                        "mitigation"
                    )

                    self.results["steps"]["generate_mitigated_bpmn"] = {
                        "success": True,
                        "element_count": result.get('element_count', 0),
                        "elapsed_time": elapsed_time,
                        "message": result.get('message', ''),
                        "dual_llm_info": result.get('dual_llm_info')
                    }

                    return mitigated_bpmn
                else:
                    self.log(f"✗ Generation failed: {result.get('message', 'Unknown error')}", "ERROR")
                    self.results["steps"]["generate_mitigated_bpmn"] = {
                        "success": False,
                        "error": result.get('message', 'Unknown error')
                    }
                    return None
            else:
                self.log(f"✗ Generation error: {response.status_code}", "ERROR")
                self.results["steps"]["generate_mitigated_bpmn"] = {
                    "success": False,
                    "error": response.text
                }
                return None

        except Exception as e:
            self.log(f"✗ Error during generation: {e}", "ERROR")
            self.results["steps"]["generate_mitigated_bpmn"] = {
                "success": False,
                "error": str(e)
            }
            return None
            
    def download_bpmn(self, bpmn_xml, filename="downloaded_mitigated_bpmn.xml"):
        """
        Test the BPMN download via the /download-bpmn/ endpoint.

        Args:
            bpmn_xml: BPMN XML content.
            filename: Filename for the download.

        Returns:
            True if the download succeeded, False otherwise.
        """
        self.log("Step 4: Test BPMN download...")
        start_time = time.time()
        
        try:
            data = {'bpmn_xml': bpmn_xml}
            
            response = requests.post(
                f"{self.backend_url}/download-bpmn/",
                data=data
            )
            
            elapsed_time = time.time() - start_time
            self.results["timings"]["download_bpmn"] = elapsed_time
            
            if response.status_code == 200:
                self.log(f"✓ Download completed in {elapsed_time:.2f}s", "SUCCESS")

                self.results["steps"]["download_bpmn"] = {
                    "success": True,
                    "file_size": len(response.content),
                    "elapsed_time": elapsed_time
                }

                return True
            else:
                self.log(f"✗ Download error: {response.status_code}", "ERROR")
                self.results["steps"]["download_bpmn"] = {
                    "success": False,
                    "error": response.text
                }
                return False

        except Exception as e:
            self.log(f"✗ Error during download: {e}", "ERROR")
            self.results["steps"]["download_bpmn"] = {
                "success": False,
                "error": str(e)
            }
            return False
            
    def parse_bpmn_xml(self, bpmn_content):
        """
        Extract structural information from a BPMN XML string.

        Args:
            bpmn_content: BPMN XML content.

        Returns:
            Dict with element counts, or None on parse error.
        """
        try:
            root = ET.fromstring(bpmn_content)

            # BPMN namespace
            ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
            
            info = {
                'tasks': len(root.findall('.//bpmn:task', ns)),
                'user_tasks': len(root.findall('.//bpmn:userTask', ns)),
                'service_tasks': len(root.findall('.//bpmn:serviceTask', ns)),
                'gateways': len(root.findall('.//bpmn:*Gateway', ns)),
                'exclusive_gateways': len(root.findall('.//bpmn:exclusiveGateway', ns)),
                'parallel_gateways': len(root.findall('.//bpmn:parallelGateway', ns)),
                'events': len(root.findall('.//bpmn:*Event', ns)),
                'start_events': len(root.findall('.//bpmn:startEvent', ns)),
                'end_events': len(root.findall('.//bpmn:endEvent', ns)),
                'sequence_flows': len(root.findall('.//bpmn:sequenceFlow', ns)),
                'data_objects': len(root.findall('.//bpmn:dataObject', ns)),
                'data_stores': len(root.findall('.//bpmn:dataStoreReference', ns)),
            }
            
            return info
            
        except Exception as e:
            self.log(f"XML parse error: {e}", "ERROR")
            return None

    def compare_bpmn_structures(self, original_bpmn, mitigated_bpmn):
        """
        Compare the structural elements of two BPMN documents.

        Args:
            original_bpmn: Original BPMN XML string.
            mitigated_bpmn: Mitigated BPMN XML string.

        Returns:
            Dict with comparison results.
        """
        self.log("Comparing BPMN structures...")

        original_info = self.parse_bpmn_xml(original_bpmn)
        mitigated_info = self.parse_bpmn_xml(mitigated_bpmn)

        if not original_info or not mitigated_info:
            return None

        comparison = {
            'original': original_info,
            'mitigated': mitigated_info,
            'differences': {}
        }

        for key in original_info:
            original_count = original_info[key]
            mitigated_count = mitigated_info[key]
            diff = mitigated_count - original_count
            
            comparison['differences'][key] = {
                'original': original_count,
                'mitigated': mitigated_count,
                'delta': diff,
                'delta_percent': (diff / original_count * 100) if original_count > 0 else 0
            }
        
        self.save_file(
            json.dumps(comparison, indent=2),
            "bpmn_structure_comparison.json",
            "analysis"
        )

        self.log("✓ Structure comparison completed", "SUCCESS")

        return comparison

    def analyze_bpmn_complexity(self, bpmn_content):
        """
        Compute complexity metrics for a BPMN.

        Args:
            bpmn_content: BPMN XML content.

        Returns:
            Dict with complexity metrics.
        """
        info = self.parse_bpmn_xml(bpmn_content)

        if not info:
            return None

        complexity = {
            'total_elements': sum(info.values()),
            'control_flow_complexity': info['gateways'] + info['events'],
            'task_complexity': info['tasks'] + info['user_tasks'] + info['service_tasks'],
            'data_complexity': info['data_objects'] + info['data_stores'],
            'cyclomatic_complexity_estimate': info['gateways'] + 1,
            'structure_metrics': info
        }
        
        return complexity
        
    # ========================================================================
    # ADVANCED ANALYSIS - GED, FITNESS, BEHAVIORAL SIMILARITY
    # ========================================================================

    def bpmn_string_to_object(self, bpmn_content):
        """
        Convert a BPMN XML string to a pm4py BPMN object.

        Args:
            bpmn_content: BPMN XML string.

        Returns:
            pm4py BPMN object, or None if pm4py is unavailable.
        """
        if not PM4PY_AVAILABLE:
            return None

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False, encoding='utf-8') as tmp:
                tmp.write(bpmn_content)
                tmp_path = tmp.name

            bpmn_graph = bpmn_importer.apply(tmp_path)
            os.unlink(tmp_path)
            return bpmn_graph
        except Exception as e:
            self.log(f"BPMN conversion error: {e}", "ERROR")
            return None

    def bpmn_to_petri_net(self, bpmn_graph):
        """
        Convert a BPMN object to a Petri net.

        Args:
            bpmn_graph: pm4py BPMN object.

        Returns:
            Tuple (petri_net, initial_marking, final_marking), or None.
        """
        if not PM4PY_AVAILABLE or bpmn_graph is None:
            return None

        try:
            net, initial_marking, final_marking = bpmn_converter.apply(bpmn_graph)
            return net, initial_marking, final_marking
        except Exception as e:
            self.log(f"Petri net conversion error: {e}", "ERROR")
            return None

    def generate_event_log_from_bpmn(self, bpmn_graph, num_traces=100):
        """
        Generate a simulated event log from a BPMN object.

        Args:
            bpmn_graph: pm4py BPMN object.
            num_traces: Number of traces to simulate.

        Returns:
            Simulated event log, or None.
        """
        if not PM4PY_AVAILABLE or bpmn_graph is None:
            return None

        try:
            conversion_result = self.bpmn_to_petri_net(bpmn_graph)
            if conversion_result is None:
                return None

            net, im, fm = conversion_result

            simulated_log = simulator.apply(net, im, final_marking=fm, parameters={
                'no_traces': num_traces
            })

            return simulated_log
        except Exception as e:
            self.log(f"Event log generation error: {e}", "ERROR")
            return None

    def calculate_fitness(self, bpmn_graph, event_log):
        """
        Calculate token-replay fitness of a BPMN against an event log.

        Args:
            bpmn_graph: pm4py BPMN object.
            event_log: Event log to replay.

        Returns:
            Fitness metrics dict, or None.
        """
        if not PM4PY_AVAILABLE or bpmn_graph is None or event_log is None:
            return None

        try:
            conversion_result = self.bpmn_to_petri_net(bpmn_graph)
            if conversion_result is None:
                return None

            net, im, fm = conversion_result

            fitness = replay_fitness.apply(
                event_log, net, im, fm,
                variant=replay_fitness.Variants.TOKEN_BASED
            )

            return fitness
        except Exception as e:
            self.log(f"Fitness calculation error: {e}", "ERROR")
            return None

    def bpmn_to_networkx(self, bpmn_graph):
        """
        Convert a BPMN object to a directed NetworkX graph for GED computation.

        Args:
            bpmn_graph: pm4py BPMN object.

        Returns:
            Directed NetworkX graph, or None.
        """
        if not PM4PY_AVAILABLE or bpmn_graph is None:
            return None

        try:
            G = nx.DiGraph()

            for node in bpmn_graph.get_nodes():
                node_name = node.get_name() if node.get_name() else str(id(node))
                node_type = type(node).__name__
                G.add_node(node_name, node_type=node_type)

            for flow in bpmn_graph.get_flows():
                source_name = flow.get_source().get_name() if flow.get_source().get_name() else str(id(flow.get_source()))
                target_name = flow.get_target().get_name() if flow.get_target().get_name() else str(id(flow.get_target()))
                G.add_edge(source_name, target_name)

            return G
        except Exception as e:
            self.log(f"NetworkX conversion error: {e}", "ERROR")
            return None

    def calculate_ged(self, bpmn1_graph, bpmn2_graph):
        """
        Calculate the Graph Edit Distance (GED) between two BPMN objects.

        Args:
            bpmn1_graph: First pm4py BPMN object.
            bpmn2_graph: Second pm4py BPMN object.

        Returns:
            Dict with GED and related metrics, or None.
        """
        if not PM4PY_AVAILABLE or bpmn1_graph is None or bpmn2_graph is None:
            return None
            
        try:
            self.log("Computing Graph Edit Distance (GED)...")

            G1 = self.bpmn_to_networkx(bpmn1_graph)
            G2 = self.bpmn_to_networkx(bpmn2_graph)
            
            if G1 is None or G2 is None:
                return None
            
            # Compute optimised GED with timeout
            ged_value = nx.graph_edit_distance(G1, G2, timeout=30)

            # Normalise GED by the maximum graph size
            max_size = max(G1.number_of_nodes() + G1.number_of_edges(),
                          G2.number_of_nodes() + G2.number_of_edges())

            # Compute similarity (1 - normalised GED)
            if max_size > 0:
                normalized_ged = ged_value / max_size
                similarity = max(0, 1 - normalized_ged)
            else:
                normalized_ged = 0
                similarity = 1.0
            
            result = {
                'ged': ged_value,
                'normalized_ged': normalized_ged,
                'similarity': similarity,
                'graph1_size': G1.number_of_nodes() + G1.number_of_edges(),
                'graph2_size': G2.number_of_nodes() + G2.number_of_edges(),
                'graph1_nodes': G1.number_of_nodes(),
                'graph1_edges': G1.number_of_edges(),
                'graph2_nodes': G2.number_of_nodes(),
                'graph2_edges': G2.number_of_edges()
            }
            
            self.log(f"  GED: {ged_value:.2f}")
            self.log(f"  Normalised GED: {normalized_ged:.4f}")
            self.log(f"  Similarity: {similarity:.4f}")

            return result
        except Exception as e:
            self.log(f"GED calculation error: {e}", "ERROR")
            return None

    def calculate_behavioral_similarity(self, bpmn1_graph, bpmn2_graph, num_traces=100):
        """
        Calculate behavioural similarity between two BPMNs via cross-fitness.

        Args:
            bpmn1_graph: First pm4py BPMN object.
            bpmn2_graph: Second pm4py BPMN object.
            num_traces: Number of traces to simulate.

        Returns:
            Dict with behavioural metrics, or None.
        """
        if not PM4PY_AVAILABLE or bpmn1_graph is None or bpmn2_graph is None:
            return None

        try:
            self.log(f"Computing behavioural similarity ({num_traces} traces)...")
            
            # Generate event logs from each BPMN
            log1 = self.generate_event_log_from_bpmn(bpmn1_graph, num_traces)
            log2 = self.generate_event_log_from_bpmn(bpmn2_graph, num_traces)

            if log1 is None or log2 is None:
                return None

            # Compute cross-fitness
            fitness_2_on_1 = self.calculate_fitness(bpmn2_graph, log1)
            fitness_1_on_2 = self.calculate_fitness(bpmn1_graph, log2)

            # Compute self-fitness
            fitness_1_on_1 = self.calculate_fitness(bpmn1_graph, log1)
            fitness_2_on_2 = self.calculate_fitness(bpmn2_graph, log2)

            if any(f is None for f in [fitness_2_on_1, fitness_1_on_2, fitness_1_on_1, fitness_2_on_2]):
                return None

            # Behavioural similarity = average of cross-fitness scores
            behavioral_similarity = (
                fitness_2_on_1['average_trace_fitness'] +
                fitness_1_on_2['average_trace_fitness']
            ) / 2

            result = {
                'behavioral_similarity': behavioral_similarity,
                'fitness_bpmn2_on_log1': fitness_2_on_1,
                'fitness_bpmn1_on_log2': fitness_1_on_2,
                'fitness_bpmn1_self': fitness_1_on_1,
                'fitness_bpmn2_self': fitness_2_on_2,
                'num_traces': num_traces
            }

            self.log(f"  Behavioural similarity: {behavioral_similarity:.4f}")
            self.log(f"  Fitness BPMN1 (self): {fitness_1_on_1['average_trace_fitness']:.4f}")
            self.log(f"  Fitness BPMN2 (self): {fitness_2_on_2['average_trace_fitness']:.4f}")

            return result
        except Exception as e:
            self.log(f"Behavioural similarity error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_fitness_with_variable_tokens(self, bpmn_graph, num_tokens_range=None, traces_per_token=50):
        """
        Compute fitness by varying the number of simulated traces in the Petri net.

        Note: the parameter name "tokens" is kept for backward compatibility, but
        what actually varies is the number of simulated traces (not the initial marking).

        Args:
            bpmn_graph: pm4py BPMN object.
            num_tokens_range: List of trace counts to test. Defaults to [10, 20, ..., 200].
            traces_per_token: Deprecated - kept for backward compatibility.

        Returns:
            Dict with fitness results for each trace count.
        """
        if not PM4PY_AVAILABLE or bpmn_graph is None:
            self.log("pm4py not available or invalid BPMN for variable fitness computation", "ERROR")
            return None

        if num_tokens_range is None:
            num_tokens_range = list(range(10, 210, 10))

        try:
            self.log(f"Computing fitness with variable token count: {num_tokens_range}...")
            
            # Convert BPMN to Petri net
            conversion_result = self.bpmn_to_petri_net(bpmn_graph)
            if conversion_result is None:
                return None

            net, initial_marking, final_marking = conversion_result

            results = {
                'token_numbers': [],
                'fitness_scores': [],
                'percentage_fit_traces': [],
                'average_trace_fitness': [],
                'details': []
            }

            for num_tokens in num_tokens_range:
                self.log(f"  Simulating with {num_tokens} tokens...", "INFO")

                try:
                    # Do NOT modify the initial marking (causes deadlocks!).
                    # Instead, vary the number of simulated traces.
                    event_log = simulator.apply(
                        net,
                        initial_marking=initial_marking,
                        final_marking=final_marking,
                        parameters={'no_traces': num_tokens}
                    )

                    if event_log is None or len(event_log) == 0:
                        self.log(f"    No traces generated with {num_tokens} tokens", "WARNING")
                        continue

                    fitness_result = replay_fitness.apply(event_log, net, initial_marking, final_marking)

                    if fitness_result is None:
                        self.log(f"    Fitness error with {num_tokens} tokens", "WARNING")
                        continue

                    avg_fitness = fitness_result['average_trace_fitness']
                    pct_fit = fitness_result['percentage_of_fitting_traces']

                    results['token_numbers'].append(num_tokens)
                    results['fitness_scores'].append(avg_fitness)
                    results['percentage_fit_traces'].append(pct_fit)
                    results['average_trace_fitness'].append(avg_fitness)

                    detail = {
                        'num_tokens': num_tokens,
                        'average_trace_fitness': avg_fitness,
                        'percentage_of_fitting_traces': pct_fit,
                        'num_traces': len(event_log),
                        'full_result': fitness_result
                    }
                    results['details'].append(detail)

                    self.log(
                        f"    Fitness: {avg_fitness:.4f} | "
                        f"Fitting traces: {pct_fit:.4f} ({pct_fit*100:.2f}%) | "
                        f"Generated traces: {len(event_log)}",
                        "SUCCESS"
                    )

                except Exception as e:
                    self.log(f"    Simulation error with {num_tokens} tokens: {e}", "WARNING")
                    import traceback
                    traceback.print_exc()
                    continue

            if not results['token_numbers']:
                self.log("No results computed for the token range", "ERROR")
                return None

            self.log(f"✓ Variable fitness computed for {len(results['token_numbers'])} configurations", "SUCCESS")

            return results

        except Exception as e:
            self.log(f"Variable fitness error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None
    
    def plot_fitness_over_tokens(self, fitness_results, output_filename="fitness_over_tokens.png"):
        """
        Generate a fitness-vs-token-count plot.

        Args:
            fitness_results: Dict returned by calculate_fitness_with_variable_tokens.
            output_filename: Filename for the saved chart.

        Returns:
            Path to the saved chart file, or None.
        """
        if not MATPLOTLIB_AVAILABLE or fitness_results is None:
            self.log("matplotlib not available or invalid results for plotting", "ERROR")
            return None

        try:
            token_numbers = fitness_results.get('token_numbers', [])
            fitness_scores = fitness_results.get('fitness_scores', [])
            percentage_fit = fitness_results.get('percentage_fit_traces', [])

            if not token_numbers or not fitness_scores:
                self.log("Insufficient data for plotting", "ERROR")
                return None

            self.log("Generating fitness vs token chart...")
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

            ax1.plot(token_numbers, fitness_scores, 'o-', linewidth=2, markersize=8, color='#2E86AB')
            ax1.fill_between(token_numbers, fitness_scores, alpha=0.3, color='#2E86AB')
            ax1.set_xlabel('Number of Tokens', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Average Trace Fitness', fontsize=12, fontweight='bold')
            ax1.set_title('Petri Net Fitness as a Function of Token Count', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.set_ylim([0, 1.05])

            for x, y in zip(token_numbers, fitness_scores):
                ax1.annotate(f'{y:.3f}', xy=(x, y), xytext=(0, 10),
                           textcoords='offset points', ha='center', fontsize=9)

            ax2.plot(token_numbers, [p*100 for p in percentage_fit], 's-', linewidth=2, markersize=8, color='#A23B72')
            ax2.fill_between(token_numbers, [p*100 for p in percentage_fit], alpha=0.3, color='#A23B72')
            ax2.set_xlabel('Number of Tokens', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Percentage of Fitting Traces (%)', fontsize=12, fontweight='bold')
            ax2.set_title('Percentage of Fitting Traces as a Function of Token Count', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, linestyle='--')
            ax2.set_ylim([0, 105])

            for x, y in zip(token_numbers, percentage_fit):
                ax2.annotate(f'{y*100:.1f}%', xy=(x, y*100), xytext=(0, 10),
                           textcoords='offset points', ha='center', fontsize=9)

            plt.tight_layout()

            graph_path = self.save_file(None, output_filename, None)
            graph_path.parent.mkdir(parents=True, exist_ok=True)

            plt.savefig(str(graph_path), dpi=300, bbox_inches='tight')
            self.log(f"✓ Chart saved: {graph_path}", "SUCCESS")

            plt.close()

            return graph_path

        except Exception as e:
            self.log(f"Chart generation error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None
    
    def plot_fitness_comparison(self, fitness_original, fitness_mitigated,
                               output_filename="fitness_comparison_original_vs_mitigated.png"):
        """
        Generate a comparative fitness chart: original BPMN vs mitigated BPMN.

        Args:
            fitness_original: Dict with results for the original BPMN.
            fitness_mitigated: Dict with results for the mitigated BPMN.
            output_filename: Filename for the saved chart.

        Returns:
            Path to the saved chart file, or None.
        """
        if not MATPLOTLIB_AVAILABLE or fitness_original is None or fitness_mitigated is None:
            self.log("matplotlib not available or invalid results for comparative plotting", "ERROR")
            return None

        try:
            token_numbers_orig = fitness_original.get('token_numbers', [])
            fitness_scores_orig = fitness_original.get('fitness_scores', [])
            percentage_fit_orig = fitness_original.get('percentage_fit_traces', [])

            token_numbers_mit = fitness_mitigated.get('token_numbers', [])
            fitness_scores_mit = fitness_mitigated.get('fitness_scores', [])
            percentage_fit_mit = fitness_mitigated.get('percentage_fit_traces', [])

            if not token_numbers_orig or not fitness_scores_orig or not token_numbers_mit or not fitness_scores_mit:
                self.log("Insufficient data for comparative plotting", "ERROR")
                return None

            self.log("Generating comparative chart...")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

            ax1.plot(token_numbers_orig, fitness_scores_orig, 'o-', linewidth=2.5, markersize=8,
                    label='Original BPMN', color='#2E86AB', alpha=0.8)
            ax1.plot(token_numbers_mit, fitness_scores_mit, 's-', linewidth=2.5, markersize=8,
                    label='Mitigated BPMN', color='#A23B72', alpha=0.8)
            ax1.fill_between(token_numbers_orig, fitness_scores_orig, alpha=0.2, color='#2E86AB')
            ax1.fill_between(token_numbers_mit, fitness_scores_mit, alpha=0.2, color='#A23B72')

            ax1.set_xlabel('Number of Tokens', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Average Trace Fitness', fontsize=12, fontweight='bold')
            ax1.set_title('Average Trace Fitness: Original vs Mitigated', fontsize=13, fontweight='bold')
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.set_ylim([0, 1.05])
            ax1.legend(fontsize=11, loc='best')

            ax2.plot(token_numbers_orig, [p*100 for p in percentage_fit_orig], 'o-', linewidth=2.5, markersize=8,
                    label='Original BPMN', color='#2E86AB', alpha=0.8)
            ax2.plot(token_numbers_mit, [p*100 for p in percentage_fit_mit], 's-', linewidth=2.5, markersize=8,
                    label='Mitigated BPMN', color='#A23B72', alpha=0.8)
            ax2.fill_between(token_numbers_orig, [p*100 for p in percentage_fit_orig], alpha=0.2, color='#2E86AB')
            ax2.fill_between(token_numbers_mit, [p*100 for p in percentage_fit_mit], alpha=0.2, color='#A23B72')

            ax2.set_xlabel('Number of Tokens', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Percentage of Fitting Traces (%)', fontsize=12, fontweight='bold')
            ax2.set_title('Percentage of Fitting Traces: Original vs Mitigated', fontsize=13, fontweight='bold')
            ax2.grid(True, alpha=0.3, linestyle='--')
            ax2.set_ylim([0, 105])
            ax2.legend(fontsize=11, loc='best')

            plt.tight_layout()

            graph_path = self.session_dir / output_filename
            graph_path.parent.mkdir(parents=True, exist_ok=True)

            plt.savefig(str(graph_path), dpi=300, bbox_inches='tight')
            self.log(f"✓ Comparative chart saved: {graph_path}", "SUCCESS")

            plt.close()

            return graph_path

        except Exception as e:
            self.log(f"Comparative chart generation error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None
    


    def calculate_structural_similarity_advanced(self, bpmn1_graph, bpmn2_graph):
        """
        Calculate advanced structural similarity using pm4py (Jaccard on nodes and flows).

        Args:
            bpmn1_graph: First pm4py BPMN object.
            bpmn2_graph: Second pm4py BPMN object.

        Returns:
            Dict with structural similarity metrics, or None.
        """
        if not PM4PY_AVAILABLE or bpmn1_graph is None or bpmn2_graph is None:
            return None

        try:
            self.log("Computing advanced structural similarity...")
            
            nodes1 = set([node.get_name() for node in bpmn1_graph.get_nodes() if node.get_name()])
            nodes2 = set([node.get_name() for node in bpmn2_graph.get_nodes() if node.get_name()])

            flows1 = set([
                (flow.get_source().get_name(), flow.get_target().get_name())
                for flow in bpmn1_graph.get_flows()
                if flow.get_source().get_name() and flow.get_target().get_name()
            ])
            flows2 = set([
                (flow.get_source().get_name(), flow.get_target().get_name())
                for flow in bpmn2_graph.get_flows()
                if flow.get_source().get_name() and flow.get_target().get_name()
            ])

            # Jaccard similarity for nodes
            node_intersection = len(nodes1.intersection(nodes2))
            node_union = len(nodes1.union(nodes2))
            node_similarity = node_intersection / node_union if node_union > 0 else 0

            # Jaccard similarity for flows
            flow_intersection = len(flows1.intersection(flows2))
            flow_union = len(flows1.union(flows2))
            flow_similarity = flow_intersection / flow_union if flow_union > 0 else 0

            # Weighted average
            structural_similarity = 0.5 * node_similarity + 0.5 * flow_similarity

            result = {
                'structural_similarity': structural_similarity,
                'node_similarity': node_similarity,
                'flow_similarity': flow_similarity,
                'nodes_bpmn1': len(nodes1),
                'nodes_bpmn2': len(nodes2),
                'nodes_common': node_intersection,
                'flows_bpmn1': len(flows1),
                'flows_bpmn2': len(flows2),
                'flows_common': flow_intersection
            }

            self.log(f"  Structural similarity: {structural_similarity:.4f}")
            self.log(f"  Node similarity: {node_similarity:.4f}")
            self.log(f"  Flow similarity: {flow_similarity:.4f}")

            return result
        except Exception as e:
            self.log(f"Structural similarity error: {e}", "ERROR")
            return None

    # ========================================================================
    # ANALYSIS SECTION
    # ========================================================================

    def perform_custom_analysis(self, original_bpmn, mitigated_bpmn, threat_analysis):
        """
        Run all analysis metrics on the original and mitigated BPMN pair.

        Includes:
        - Basic structural comparison
        - Complexity analysis
        - Graph Edit Distance (GED)
        - Cross-fitness and behavioural similarity
        - Advanced structural similarity
        - Variable-token fitness analysis

        Args:
            original_bpmn: Original BPMN string.
            mitigated_bpmn: Mitigated BPMN string.
            threat_analysis: Result of threat analysis (dict).

        Returns:
            Dict with all analysis results.
        """
        self.log("=" * 80)
        self.log("RUNNING CUSTOM ANALYSIS")
        self.log("=" * 80)
        
        analysis_results = {
            'structure_comparison': self.compare_bpmn_structures(original_bpmn, mitigated_bpmn),
            'original_complexity': self.analyze_bpmn_complexity(original_bpmn),
            'mitigated_complexity': self.analyze_bpmn_complexity(mitigated_bpmn),
        }
        
        if PM4PY_AVAILABLE:
            self.log("\n--- Advanced Metrics (pm4py) ---")

            self.log("Converting BPMN strings to pm4py objects...")
            bpmn1_obj = self.bpmn_string_to_object(original_bpmn)
            bpmn2_obj = self.bpmn_string_to_object(mitigated_bpmn)
            
            if bpmn1_obj and bpmn2_obj:
                # 1. Graph Edit Distance (GED)
                ged_results = self.calculate_ged(bpmn1_obj, bpmn2_obj)
                if ged_results:
                    analysis_results['ged_metrics'] = ged_results
                    
                    # Save GED results separately
                    self.save_file(
                        json.dumps(ged_results, indent=2),
                        "ged_analysis.json",
                        "analysis"
                    )
                
                # 2. Advanced structural similarity
                structural_sim = self.calculate_structural_similarity_advanced(bpmn1_obj, bpmn2_obj)
                if structural_sim:
                    analysis_results['structural_similarity_advanced'] = structural_sim
                    self.save_file(
                        json.dumps(structural_sim, indent=2),
                        "structural_similarity_advanced.json",
                        "analysis"
                    )

                # 3. Behavioural similarity and fitness
                self.log("\n--- Behavioural Analysis ---")
                behavioral_sim = self.calculate_behavioral_similarity(
                    bpmn1_obj, 
                    bpmn2_obj, 
                    num_traces=100
                )
                if behavioral_sim:
                    analysis_results['behavioral_similarity'] = behavioral_sim
                    self.save_file(
                        json.dumps(behavioral_sim, indent=2, default=str),
                        "behavioral_similarity_fitness.json",
                        "analysis"
                    )

                # 4. Variable-token fitness (mitigated BPMN)
                self.log("\n--- Variable-Token Fitness Analysis (Mitigated BPMN) ---")
                fitness_var_results = self.calculate_fitness_with_variable_tokens(
                    bpmn2_obj,
                    num_tokens_range=list(range(10, 210, 10)),
                    traces_per_token=100
                )
                if fitness_var_results:
                    analysis_results['fitness_variable_tokens'] = fitness_var_results
                    self.save_file(
                        json.dumps(fitness_var_results, indent=2, default=str),
                        "fitness_variable_tokens.json",
                        "analysis"
                    )
                    graph_path = self.plot_fitness_over_tokens(
                        fitness_var_results,
                        output_filename="fitness_over_tokens.png"
                    )
                    if graph_path:
                        analysis_results['fitness_graph_path'] = str(graph_path)
                        self.log(f"✓ Fitness chart saved: {graph_path}", "SUCCESS")

                # 5. Variable-token fitness (original BPMN) - for comparison
                self.log("\n--- Variable-Token Fitness Analysis (Original BPMN) ---")
                fitness_var_results_original = self.calculate_fitness_with_variable_tokens(
                    bpmn1_obj,
                    num_tokens_range=list(range(10, 210, 10)),
                    traces_per_token=100
                )
                if fitness_var_results_original:
                    analysis_results['fitness_variable_tokens_original'] = fitness_var_results_original
                    self.save_file(
                        json.dumps(fitness_var_results_original, indent=2, default=str),
                        "fitness_variable_tokens_original.json",
                        "analysis"
                    )
                    self.log("Generating comparative chart...")
                    self.plot_fitness_comparison(
                        fitness_var_results_original,
                        fitness_var_results,
                        output_filename="fitness_comparison_original_vs_mitigated.png"
                    )

                self.log("\n✓ Advanced metrics completed", "SUCCESS")
            else:
                self.log("Unable to convert BPMN to pm4py objects", "WARNING")
                analysis_results['advanced_metrics_error'] = "BPMN conversion failed"
        else:
            self.log("\npm4py not available - advanced metrics skipped", "WARNING")
            analysis_results['advanced_metrics_available'] = False
        
        # Save complete analysis results
        self.save_file(
            json.dumps(analysis_results, indent=2, default=str),
            "custom_analysis_results.json",
            "analysis"
        )
        
        self.results["analysis"] = analysis_results
        
        self.log("\n" + "=" * 80)
        self.log("✓ CUSTOM ANALYSIS COMPLETED", "SUCCESS")
        self.log("=" * 80)
        
        return analysis_results
        
    def generate_report(self):
        """Generate a text evaluation report."""
        self.log("Generating final report...")

        report_lines = [
            "=" * 80,
            "EVALUATION REPORT - BPMN THREAT ANALYSIS & MITIGATION",
            "=" * 80,
            "",
            f"Timestamp: {self.timestamp}",
            f"Backend URL: {self.backend_url}",
            f"Output Directory: {self.session_dir}",
            "",
            "=" * 80,
            "STEP SUMMARY",
            "=" * 80,
            ""
        ]

        for step_name, step_data in self.results["steps"].items():
            status = "✓ SUCCESS" if step_data.get("success", False) else "✗ FAILED"
            report_lines.append(f"{step_name}: {status}")
            if "elapsed_time" in step_data:
                report_lines.append(f"  Time: {step_data['elapsed_time']:.2f}s")
            if "error" in step_data:
                report_lines.append(f"  Error: {step_data['error']}")
            report_lines.append("")

        report_lines.extend([
            "=" * 80,
            "TIMINGS",
            "=" * 80,
            ""
        ])

        total_time = sum(self.results["timings"].values())
        for timing_name, timing_value in self.results["timings"].items():
            report_lines.append(f"{timing_name}: {timing_value:.2f}s")
        report_lines.append(f"\nTotal time: {total_time:.2f}s")
        report_lines.append("")
        
        if self.results.get("analysis"):
            report_lines.extend([
                "=" * 80,
                "ANALYSIS",
                "=" * 80,
                ""
            ])

            analysis = self.results["analysis"]

            if "structure_comparison" in analysis and analysis["structure_comparison"]:
                comp = analysis["structure_comparison"]
                report_lines.append("Structure Comparison:")
                for key, diff in comp["differences"].items():
                    report_lines.append(
                        f"  {key}: {diff['original']} → {diff['mitigated']} "
                        f"(Δ: {diff['delta']:+d}, {diff['delta_percent']:+.1f}%)"
                    )
                report_lines.append("")

            if "original_complexity" in analysis and analysis["original_complexity"]:
                orig_comp = analysis["original_complexity"]
                report_lines.append("Original BPMN Complexity:")
                report_lines.append(f"  Total elements: {orig_comp['total_elements']}")
                report_lines.append(f"  Control-flow complexity: {orig_comp['control_flow_complexity']}")
                report_lines.append(f"  Task complexity: {orig_comp['task_complexity']}")
                report_lines.append("")

            if "mitigated_complexity" in analysis and analysis["mitigated_complexity"]:
                mit_comp = analysis["mitigated_complexity"]
                report_lines.append("Mitigated BPMN Complexity:")
                report_lines.append(f"  Total elements: {mit_comp['total_elements']}")
                report_lines.append(f"  Control-flow complexity: {mit_comp['control_flow_complexity']}")
                report_lines.append(f"  Task complexity: {mit_comp['task_complexity']}")
                report_lines.append("")

            if "ged_metrics" in analysis and analysis["ged_metrics"]:
                ged = analysis["ged_metrics"]
                report_lines.append("=== Graph Edit Distance (GED) ===")
                report_lines.append(f"  GED: {ged['ged']:.2f}")
                report_lines.append(f"  Normalised GED: {ged['normalized_ged']:.4f}")
                report_lines.append(f"  Similarity (1-nGED): {ged['similarity']:.4f} ({ged['similarity']*100:.2f}%)")
                report_lines.append(f"  Graph 1: {ged['graph1_nodes']} nodes, {ged['graph1_edges']} edges")
                report_lines.append(f"  Graph 2: {ged['graph2_nodes']} nodes, {ged['graph2_edges']} edges")
                report_lines.append("")

            if "structural_similarity_advanced" in analysis and analysis["structural_similarity_advanced"]:
                struct = analysis["structural_similarity_advanced"]
                report_lines.append("=== Advanced Structural Similarity ===")
                report_lines.append(f"  Overall: {struct['structural_similarity']:.4f} ({struct['structural_similarity']*100:.2f}%)")
                report_lines.append(f"  Node similarity: {struct['node_similarity']:.4f} ({struct['node_similarity']*100:.2f}%)")
                report_lines.append(f"  Flow similarity: {struct['flow_similarity']:.4f} ({struct['flow_similarity']*100:.2f}%)")
                report_lines.append(f"  Common nodes: {struct['nodes_common']}/{struct['nodes_bpmn1']} ∩ {struct['nodes_bpmn2']}")
                report_lines.append(f"  Common flows: {struct['flows_common']}/{struct['flows_bpmn1']} ∩ {struct['flows_bpmn2']}")
                report_lines.append("")

            if "behavioral_similarity" in analysis and analysis["behavioral_similarity"]:
                behav = analysis["behavioral_similarity"]
                report_lines.append("=== Behavioural Similarity & Fitness ===")
                report_lines.append(f"  Behavioural similarity: {behav['behavioral_similarity']:.4f} ({behav['behavioral_similarity']*100:.2f}%)")
                report_lines.append(f"  Traces analysed: {behav['num_traces']}")
                report_lines.append("")
                report_lines.append("  Original BPMN self-fitness:")
                if 'fitness_bpmn1_self' in behav and behav['fitness_bpmn1_self']:
                    f1 = behav['fitness_bpmn1_self']
                    report_lines.append(f"    - Average trace fitness: {f1.get('average_trace_fitness', 'N/A'):.4f}")
                    report_lines.append(f"    - Percentage fit traces: {f1.get('percentage_of_fitting_traces', 'N/A'):.4f}")
                report_lines.append("")
                report_lines.append("  Mitigated BPMN self-fitness:")
                if 'fitness_bpmn2_self' in behav and behav['fitness_bpmn2_self']:
                    f2 = behav['fitness_bpmn2_self']
                    report_lines.append(f"    - Average trace fitness: {f2.get('average_trace_fitness', 'N/A'):.4f}")
                    report_lines.append(f"    - Percentage fit traces: {f2.get('percentage_of_fitting_traces', 'N/A'):.4f}")
                report_lines.append("")

            if "fitness_variable_tokens" in analysis and analysis["fitness_variable_tokens"]:
                fitness_var = analysis["fitness_variable_tokens"]
                report_lines.append("=== Variable-Token Fitness (Mitigated BPMN) ===")
                report_lines.append(f"  Configurations tested: {len(fitness_var.get('token_numbers', []))}")
                report_lines.append(f"  Token range: {fitness_var.get('token_numbers', [])}")
                report_lines.append("")
                report_lines.append("  Results per configuration:")
                for detail in fitness_var.get('details', []):
                    report_lines.append(f"    Tokens: {detail['num_tokens']:3d} | "
                                      f"Avg Fitness: {detail['average_trace_fitness']:.4f} | "
                                      f"Fit Traces: {detail['percentage_of_fitting_traces']*100:6.2f}% | "
                                      f"Traces: {detail['num_traces']}")
                report_lines.append("")
                if "fitness_graph_path" in analysis:
                    report_lines.append(f"  Chart saved: {analysis['fitness_graph_path']}")
                report_lines.append("")

            if "fitness_variable_tokens_original" in analysis and analysis["fitness_variable_tokens_original"]:
                fitness_var_orig = analysis["fitness_variable_tokens_original"]
                report_lines.append("=== Variable-Token Fitness (Original BPMN - comparison) ===")
                report_lines.append(f"  Configurations tested: {len(fitness_var_orig.get('token_numbers', []))}")
                report_lines.append(f"  Token range: {fitness_var_orig.get('token_numbers', [])}")
                report_lines.append("")
                report_lines.append("  Results per configuration:")
                for detail in fitness_var_orig.get('details', []):
                    report_lines.append(f"    Tokens: {detail['num_tokens']:3d} | "
                                      f"Avg Fitness: {detail['average_trace_fitness']:.4f} | "
                                      f"Fit Traces: {detail['percentage_of_fitting_traces']*100:6.2f}% | "
                                      f"Traces: {detail['num_traces']}")
                report_lines.append("")
                report_lines.append("  Comparative chart: fitness_comparison_original_vs_mitigated.png")
                report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("End of Report")
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        report_path = self.save_file(report_content, "evaluation_report.txt")
        self.log(f"✓ Report saved to: {report_path}", "SUCCESS")
        
        return report_content
        
    def run_full_evaluation(self, bpmn_path, context, principles):
        """
        Run the full single-run evaluation pipeline.

        Args:
            bpmn_path: Path to the test BPMN file.
            context: Process context (dict).
            principles: Security principles (list).

        Returns:
            Dict with all evaluation results.
        """
        self.log("=" * 80)
        self.log("STARTING FULL EVALUATION")
        self.log("=" * 80)
        
        total_start_time = time.time()
        
        if not self.check_backend_health():
            self.log("Evaluation aborted: backend unavailable", "ERROR")
            return self.results

        original_bpmn = self.load_test_bpmn(bpmn_path)
        if not original_bpmn:
            self.log("Evaluation aborted: unable to load BPMN", "ERROR")
            return self.results

        # Step 1: Validate BPMN
        validation_result = self.validate_bpmn(bpmn_path)
        if not validation_result or not validation_result.get('valid', False):
            self.log("Warning: BPMN not valid, continuing anyway...", "WARNING")

        # Step 2: Analyze threats
        threat_analysis_result = self.analyze_threats(bpmn_path, context, principles)
        if not threat_analysis_result:
            self.log("Evaluation aborted: threat analysis failed", "ERROR")
            return self.results

        threat_analysis_text = threat_analysis_result.get('doc', '')

        # Step 3: Generate mitigated BPMN
        mitigated_bpmn = self.generate_mitigated_bpmn(
            bpmn_path,
            context,
            principles,
            threat_analysis_text
        )

        if not mitigated_bpmn:
            self.log("Evaluation aborted: mitigated BPMN generation failed", "ERROR")
            return self.results

        # Step 4: Download BPMN
        self.download_bpmn(mitigated_bpmn)

        # Step 5: Perform analysis
        self.perform_custom_analysis(original_bpmn, mitigated_bpmn, threat_analysis_result)

        total_elapsed = time.time() - total_start_time
        self.results["total_evaluation_time"] = total_elapsed

        self.generate_report()

        self.save_file(
            json.dumps(self.results, indent=2),
            "complete_results.json"
        )

        self.log("=" * 80)
        self.log(f"✓ EVALUATION COMPLETED in {total_elapsed:.2f}s", "SUCCESS")
        self.log(f"  Results saved in: {self.session_dir}")
        self.log("=" * 80)
        
        return self.results


# ============================================================================
# STANDALONE ANALYSIS: DIRECT BPMN FILE COMPARISON
# ============================================================================

def analyze_bpmn_fitness_from_files(original_bpmn_path, mitigated_bpmn_path, output_dir="fitness_analysis_results"):
    """
    Compute fitness and cross-fitness metrics between two BPMN files.

    Args:
        original_bpmn_path: Path to the original BPMN file.
        mitigated_bpmn_path: Path to the mitigated BPMN file.
        output_dir: Directory where results will be saved.

    Returns:
        Dict with all analysis results, or None on failure.
    """
    print("=" * 80)
    print("FITNESS ANALYSIS: ORIGINAL BPMN vs MITIGATED BPMN")
    print("=" * 80)
    print(f"\nOriginal BPMN: {original_bpmn_path}")
    print(f"Mitigated BPMN: {mitigated_bpmn_path}")
    print(f"Output:         {output_dir}\n")

    if not PM4PY_AVAILABLE:
        print("❌ ERROR: pm4py not available!")
        print("Install with: pip install pm4py")
        return None

    evaluator = BPMNEvaluator(output_dir=output_dir)
    
    try:
        # STEP 1: Load BPMN files
        print("\n[1/5] Loading BPMN files...")
        with open(original_bpmn_path, 'r', encoding='utf-8') as f:
            original_bpmn_content = f.read()

        with open(mitigated_bpmn_path, 'r', encoding='utf-8') as f:
            mitigated_bpmn_content = f.read()

        print(f"  ✓ Original BPMN: {len(original_bpmn_content)} chars")
        print(f"  ✓ Mitigated BPMN: {len(mitigated_bpmn_content)} chars")

        # STEP 2: Convert to pm4py objects
        print("\n[2/5] Converting BPMN to pm4py objects...")
        bpmn_original = evaluator.bpmn_string_to_object(original_bpmn_content)
        bpmn_mitigated = evaluator.bpmn_string_to_object(mitigated_bpmn_content)

        if not bpmn_original or not bpmn_mitigated:
            print("❌ ERROR: Unable to convert BPMN files")
            return None

        print("  ✓ Conversion complete")

        # STEP 3: Compute cross-fitness (behavioural similarity)
        print("\n[3/5] Computing cross-fitness (behavioural similarity)...")
        behavioral_results = evaluator.calculate_behavioral_similarity(
            bpmn_original,
            bpmn_mitigated,
            num_traces=100
        )
        
        if behavioral_results:
            print(f"  ✓ Behavioural similarity: {behavioral_results['behavioral_similarity']:.4f} ({behavioral_results['behavioral_similarity']*100:.2f}%)")
            evaluator.save_file(
                json.dumps(behavioral_results, indent=2, default=str),
                "cross_fitness_behavioral.json"
            )

        # STEP 4: Variable-token fitness
        print("\n[4/5] Computing variable-token fitness (Original vs Mitigated)...")

        trace_range = list(range(10, 210, 10))
        print(f"  Trace range: {trace_range[0]} → {trace_range[-1]} (step {trace_range[1] - trace_range[0]})")

        print("\n  → Original BPMN...")
        fitness_original = evaluator.calculate_fitness_with_variable_tokens(
            bpmn_original,
            num_tokens_range=trace_range,
            traces_per_token=1
        )

        print("\n  → Mitigated BPMN...")
        fitness_mitigated = evaluator.calculate_fitness_with_variable_tokens(
            bpmn_mitigated,
            num_tokens_range=trace_range,
            traces_per_token=1
        )

        if fitness_original:
            evaluator.save_file(
                json.dumps(fitness_original, indent=2, default=str),
                "fitness_variable_original.json"
            )
            print(f"    ✓ {len(fitness_original.get('token_numbers', []))} configurations computed")

        if fitness_mitigated:
            evaluator.save_file(
                json.dumps(fitness_mitigated, indent=2, default=str),
                "fitness_variable_mitigated.json"
            )
            print(f"    ✓ {len(fitness_mitigated.get('token_numbers', []))} configurations computed")

        # STEP 5: Generate charts
        print("\n[5/5] Generating charts...")
        
        if fitness_mitigated:
            graph_mitigated = evaluator.plot_fitness_over_tokens(
                fitness_mitigated,
                output_filename="fitness_over_traces_mitigated.png"
            )
            if graph_mitigated:
                print(f"  ✓ Mitigated BPMN chart: {graph_mitigated.name}")

        if fitness_original:
            graph_original = evaluator.plot_fitness_over_tokens(
                fitness_original,
                output_filename="fitness_over_traces_original.png"
            )
            if graph_original:
                print(f"  ✓ Original BPMN chart: {graph_original.name}")

        if fitness_original and fitness_mitigated:
            graph_comparison = evaluator.plot_fitness_comparison(
                fitness_original,
                fitness_mitigated,
                output_filename="fitness_comparison_original_vs_mitigated.png"
            )
            if graph_comparison:
                print(f"  ✓ Comparative chart: {graph_comparison.name}")

        print("\n" + "=" * 80)
        print("✓ ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\nResults saved in: {evaluator.session_dir}")

        results = {
            'behavioral_similarity': behavioral_results,
            'fitness_original': fitness_original,
            'fitness_mitigated': fitness_mitigated,
            'output_directory': str(evaluator.session_dir)
        }

        return results

    except Exception as e:
        print(f"\n❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """
    Run fitness analysis between two BPMN files.
    Edit the paths below before running.
    """
    # ==========================================
    # CONFIGURATION - SET YOUR PATHS HERE
    # ==========================================
    
    ORIGINAL_BPMN_PATH = "/mnt/c/Users/ianna/OneDrive - Uniparthenope/Uniparthenope1/Dottorato/Periodo estero/studio/Masterproject-Sourcecode/Masterproject-Sourcecode/Masterproject-Backend/test.bpmn"
    
    MITIGATED_BPMN_PATH = "/mnt/c/Users/ianna/OneDrive - Uniparthenope/Uniparthenope1/Dottorato/Periodo estero/studio/Masterproject-Sourcecode/Masterproject-Sourcecode/Masterproject-Backend/evaluation_results/session_20260217_102404/bpmn_files/mitigated_bpmn.xml"
    
    OUTPUT_DIR = "fitness_analysis_results"
    
    # ==========================================
    # RUN ANALYSIS
    # ==========================================

    results = analyze_bpmn_fitness_from_files(
        original_bpmn_path=ORIGINAL_BPMN_PATH,
        mitigated_bpmn_path=MITIGATED_BPMN_PATH,
        output_dir=OUTPUT_DIR
    )
    
    if results:
        print("\n📊 RESULTS SUMMARY:")
        print("-" * 80)

        if results.get('behavioral_similarity'):
            bs = results['behavioral_similarity']['behavioral_similarity']
            print(f"Cross-Fitness (Behavioural): {bs:.4f} ({bs*100:.2f}%)")

        if results.get('fitness_original'):
            n_orig = len(results['fitness_original'].get('token_numbers', []))
            print(f"Configurations tested (Original): {n_orig}")

        if results.get('fitness_mitigated'):
            n_mit = len(results['fitness_mitigated'].get('token_numbers', []))
            print(f"Configurations tested (Mitigated): {n_mit}")

        print(f"\n📁 Output: {results['output_directory']}")
        print("=" * 80)
    else:
        print("\n❌ Analysis failed!")


if __name__ == "__main__":
    main()
