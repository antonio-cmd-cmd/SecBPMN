"""
Evaluation Script - BPMN Threat Analysis & Mitigation
======================================================

Tests the complete application pipeline:
1. Load test BPMN
2. Threat analysis
3. Mitigated BPMN generation
4. Download mitigated BPMN
5. Comparative analysis between original and mitigated BPMN

Author: Evaluation Script Generator
Date: 2026-02-10
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


class BPMNEvaluator:
    """Evaluates the BPMN threat-analysis and mitigation web application."""

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
        
        # Timestamp per questa esecuzione
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        # Context isolation (sweep mode):
        # If EVAL_FLUSH_OLLAMA_BETWEEN_RUNS=true, models are unloaded from VRAM
        # before each sweep run to reset the KV-cache and ensure statistically
        # independent runs.
        self._eval_flush_ollama = os.getenv("EVAL_FLUSH_OLLAMA_BETWEEN_RUNS", "false").lower() == "true"

        # Evaluation results
        self.results = {
            "timestamp": self.timestamp,
            "backend_url": backend_url,
            "steps": {},
            "timings": {},
            "analysis": {}
        }
        
    def log(self, message, level="INFO"):
        """Print a log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def save_file(self, content, filename, subdir=None):
        """Save a file to the output directory."""
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
        """Check that the backend is reachable."""
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
            bpmn_path: Path to the BPMN file.

        Returns:
            BPMN file content as string.
        """
        self.log(f"Loading test BPMN from: {bpmn_path}")

        if not os.path.exists(bpmn_path):
            self.log(f"✗ BPMN file not found: {bpmn_path}", "ERROR")
            return None

        with open(bpmn_path, 'r', encoding='utf-8') as f:
            bpmn_content = f.read()

        self.save_file(bpmn_content, "original_bpmn.xml", "bpmn_files")

        self.log(f"✓ BPMN loaded ({len(bpmn_content)} chars)", "SUCCESS")
        self.results["steps"]["load_bpmn"] = {
            "success": True,
            "file_path": bpmn_path,
            "file_size": len(bpmn_content)
        }

        return bpmn_content
        
    def validate_bpmn(self, bpmn_path):
        """
        Validate the BPMN via the /validate-bpmn/ endpoint.

        Args:
            bpmn_path: Path to the BPMN file.

        Returns:
            Validation result dict, or None.
        """
        self.log("Step 1: Validating BPMN...")
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
                self.log(f"✓ Validation complete in {elapsed_time:.2f}s", "SUCCESS")
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
            self.log(f"✗ Validation failed: {e}", "ERROR")
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
            context: Process context (dict).
            principles: Security principles (list).

        Returns:
            Threat analysis result dict, or None.
        """
        self.log("Step 2: Analysing threats...")
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
                self.log(f"✓ Analysis complete in {elapsed_time:.2f}s", "SUCCESS")
                self.save_file(
                    json.dumps(result, indent=2),
                    "threat_analysis_raw.json",
                    "threat_analysis"
                )
                if 'doc' in result:
                    self.save_file(result['doc'], "threat_analysis.md", "threat_analysis")
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
            self.log(f"✗ Analysis failed: {e}", "ERROR")
            self.results["steps"]["analyze_threats"] = {
                "success": False,
                "error": str(e)
            }
            return None
            
    def generate_mitigated_bpmn(self, bpmn_path, context, principles, threat_analysis,
                                max_llm_iterations=None):
        """
        Generate the mitigated BPMN via the /generate-mitigated-bpmn/ endpoint.

        Args:
            bpmn_path: Path to the original BPMN file.
            context: Process context (dict).
            principles: Security principles (list).
            threat_analysis: Threat analysis text (markdown string).
            max_llm_iterations: Maximum Generator/Validator iterations.
                                 If None, uses the value from the backend .env.

        Returns:
            Mitigated BPMN as an XML string.
        """
        iter_label = f" (max_llm_iterations={max_llm_iterations})" if max_llm_iterations is not None else ""
        self.log(f"Step 3: Generating mitigated BPMN{iter_label}...")
        start_time = time.time()
        
        try:
            with open(bpmn_path, 'rb') as f:
                files = {'file': (os.path.basename(bpmn_path), f, 'application/xml')}
                data = {
                    'context': json.dumps(context),
                    'principles': json.dumps(principles),
                    'threat_analysis': threat_analysis
                }
                if max_llm_iterations is not None:
                    data['max_llm_iterations'] = str(max_llm_iterations)
                
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

                    self.save_file(mitigated_bpmn, "mitigated_bpmn.xml", "bpmn_files")
                    self.save_file(
                        json.dumps(result, indent=2), "mitigation_result.json", "mitigation"
                    )
                    
                    self.results["steps"]["generate_mitigated_bpmn"] = {
                        "success": True,
                        "element_count": result.get('element_count', 0),
                        "elapsed_time": elapsed_time,
                        "message": result.get('message', ''),
                        "dual_llm_info": result.get('dual_llm_info'),
                        "max_llm_iterations_used": max_llm_iterations
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
            self.log(f"✗ Generation failed: {e}", "ERROR")
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
            filename: Filename to download as.

        Returns:
            True if download succeeded, False otherwise.
        """
        self.log("Step 4: Testing BPMN download...")
        start_time = time.time()

        try:
            data = {'bpmn_xml': bpmn_xml}
            response = requests.post(f"{self.backend_url}/download-bpmn/", data=data)

            elapsed_time = time.time() - start_time
            self.results["timings"]["download_bpmn"] = elapsed_time

            if response.status_code == 200:
                self.log(f"✓ Download complete in {elapsed_time:.2f}s", "SUCCESS")
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
            self.log(f"✗ Download failed: {e}", "ERROR")
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
            Dict with BPMN element counts.
        """
        try:
            root = ET.fromstring(bpmn_content)
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
            self.log(f"XML parsing error: {e}", "ERROR")
            return None

    def compare_bpmn_structures(self, original_bpmn, mitigated_bpmn):
        """
        Compare the element counts of two BPMN structures.

        Args:
            original_bpmn: Original BPMN string.
            mitigated_bpmn: Mitigated BPMN string.

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

        self.log("✓ Structure comparison complete", "SUCCESS")

        return comparison

    def analyze_bpmn_complexity(self, bpmn_content):
        """
        Analyse the complexity of a BPMN.

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
    # ADVANCED ANALYSIS: GED, FITNESS, BEHAVIORAL SIMILARITY
    # ========================================================================

    def bpmn_string_to_object(self, bpmn_content):
        """
        Convert a BPMN XML string to a pm4py BPMN object.

        Args:
            bpmn_content: BPMN XML content as string.

        Returns:
            pm4py BPMN object, or None if pm4py is not available.
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
            bpmn_graph: BPMN object.

        Returns:
            Tuple (petri_net, initial_marking, final_marking) or None.
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
            bpmn_graph: BPMN object.
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
        Compute fitness of a BPMN against an event log.

        Args:
            bpmn_graph: BPMN object.
            event_log: Event log.

        Returns:
            Dict with fitness metrics, or None.
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
            self.log(f"Fitness computation error: {e}", "ERROR")
            return None

    def bpmn_to_networkx(self, bpmn_graph):
        """
        Convert a BPMN object to a NetworkX directed graph.

        Args:
            bpmn_graph: BPMN object.

        Returns:
            NetworkX DiGraph, or None.
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
        Compute the Graph Edit Distance (GED) between two BPMN objects.

        Args:
            bpmn1_graph: First BPMN object.
            bpmn2_graph: Second BPMN object.

        Returns:
            Dict with GED and related metrics, or None.
        """
        if not PM4PY_AVAILABLE or bpmn1_graph is None or bpmn2_graph is None:
            return None
            
        try:
            self.log("Computing Graph Edit Distance (GED)...")

            # Convert BPMN to NetworkX graphs
            G1 = self.bpmn_to_networkx(bpmn1_graph)
            G2 = self.bpmn_to_networkx(bpmn2_graph)

            if G1 is None or G2 is None:
                return None

            # Compute optimised GED with timeout
            ged_value = nx.graph_edit_distance(G1, G2, timeout=30)
            
            # Normalise GED relative to the maximum graph size
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
            self.log(f"  GED normalizzata: {normalized_ged:.4f}")
            self.log(f"  Similarity: {similarity:.4f}")
            
            return result
        except Exception as e:
            self.log(f"Errore nel calcolo GED: {e}", "ERROR")
            return None
    
    def calculate_behavioral_similarity(self, bpmn1_graph, bpmn2_graph, num_traces=100):
        """
        Compute behavioural similarity between two BPMN objects via cross-fitness.

        Args:
            bpmn1_graph: First BPMN object.
            bpmn2_graph: Second BPMN object.
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
    
    def calculate_structural_similarity_advanced(self, bpmn1_graph, bpmn2_graph):
        """
        Compute advanced structural similarity (Jaccard on nodes and flows).

        Args:
            bpmn1_graph: First BPMN object.
            bpmn2_graph: Second BPMN object.

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

        Args:
            original_bpmn: Original BPMN string.
            mitigated_bpmn: Mitigated BPMN string.
            threat_analysis: Threat analysis result (dict).

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
                # 1. Graph Edit Distance
                ged_results = self.calculate_ged(bpmn1_obj, bpmn2_obj)
                if ged_results:
                    analysis_results['ged_metrics'] = ged_results
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

                self.log("\n✓ Advanced metrics completed", "SUCCESS")
            else:
                self.log("Unable to convert BPMN to pm4py objects", "WARNING")
                analysis_results['advanced_metrics_error'] = "BPMN conversion failed"
        else:
            self.log("\npm4py not available - advanced metrics skipped", "WARNING")
            analysis_results['advanced_metrics_available'] = False

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
        
    def save_csv(self, rows, fieldnames, filename, subdir=None):
        """
        Save a list of dicts as a CSV file.

        Args:
            rows: List of dicts with the data.
            fieldnames: Ordered list of fields to include.
            filename: CSV filename.
            subdir: Optional sub-directory.
        """
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        return self.save_file(output.getvalue(), filename, subdir)

    # ========================================================================
    # CONTEXT ISOLATION HELPERS (Ollama)
    # ========================================================================

    def _flush_ollama_model(self, base_url: str, model_name: str) -> bool:
        """
        Ask the Ollama server to unload a model from VRAM by sending keep_alive=0.

        This resets the model KV-cache on the server, ensuring the next sweep run
        starts from a completely clean state with no residual context.

        Args:
            base_url:   Ollama server base URL (e.g. "http://localhost:11434").
            model_name: Name of the model to unload.

        Returns:
            True if successfully unloaded, False otherwise.
        """
        try:
            url = f"{base_url}/api/generate"
            payload = {"model": model_name, "keep_alive": 0}
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                self.log(f"  ✓ [Ollama flush] Model '{model_name}' unloaded from VRAM ({base_url})")
                return True
            else:
                self.log(
                    f"  ⚠ [Ollama flush] Unexpected response (HTTP {resp.status_code}) "
                    f"for model '{model_name}'",
                    "WARNING"
                )
                return False
        except requests.exceptions.RequestException as e:
            self.log(
                f"  ⚠ [Ollama flush] Cannot contact {base_url}: {e}",
                "WARNING"
            )
            return False

    def _flush_ollama_context(self) -> None:
        """
        Unload Generator and Validator Ollama models from VRAM to ensure
        context isolation between consecutive sweep runs.

        Why this is needed:
          1. The backend creates NEW ChatOllama instances per API call
             - no conversation history between runs ✓
          2. ChatOllama.invoke(str) sends ONLY the current message
             - no accumulated history in Python variables ✓
          3. The Ollama server keeps the model in VRAM (controlled by
             OLLAMA_KEEP_ALIVE) and may use a KV-cache for identical prefixes.
             This flush removes that cached state too.

        Configuration (.env):
            EVAL_FLUSH_OLLAMA_BETWEEN_RUNS  (true/false, default false)
            GENERATOR_LLM_PROVIDER / GENERATOR_OLLAMA_BASE_URL / GENERATOR_OLLAMA_MODEL
            VALIDATOR_LLM_PROVIDER / VALIDATOR_OLLAMA_BASE_URL / VALIDATOR_OLLAMA_MODEL
        """
        if not self._eval_flush_ollama:
            self.log(
                "  [Context isolation] Ollama flush disabled "
                "(set EVAL_FLUSH_OLLAMA_BETWEEN_RUNS=true in .env to enable)"
            )
            return

        self.log("  [Context isolation] Unloading Ollama models from VRAM...")
        flushed = 0

        # --- Generator LLM ---
        gen_provider = os.getenv("GENERATOR_LLM_PROVIDER", "ollama").lower()
        if gen_provider == "ollama":
            gen_url   = os.getenv("GENERATOR_OLLAMA_BASE_URL", "http://localhost:11434")
            gen_model = os.getenv("GENERATOR_OLLAMA_MODEL", "")
            if gen_model:
                flushed += int(self._flush_ollama_model(gen_url, gen_model))
            else:
                self.log("  ⚠ [Ollama flush] GENERATOR_OLLAMA_MODEL not configured — skip", "WARNING")
        else:
            self.log(f"  [Ollama flush] Generator provider='{gen_provider}' — no flush needed")

        # --- Validator LLM ---
        val_provider = os.getenv("VALIDATOR_LLM_PROVIDER", "ollama").lower()
        if val_provider == "ollama":
            val_url   = os.getenv("VALIDATOR_OLLAMA_BASE_URL", "http://localhost:11434")
            val_model = os.getenv("VALIDATOR_OLLAMA_MODEL", "")
            if val_model:
                flushed += int(self._flush_ollama_model(val_url, val_model))
            else:
                self.log("  ⚠ [Ollama flush] VALIDATOR_OLLAMA_MODEL not configured — skip", "WARNING")
        else:
            self.log(f"  [Ollama flush] Validator provider='{val_provider}' — no flush needed")

        if flushed > 0:
            self.log(
                f"  ✓ [Context isolation] {flushed} model(s) unloaded — "
                "next run will start from a completely clean state.",
                "SUCCESS"
            )
        else:
            self.log(
                "  [Context isolation] No Ollama models to unload "
                "(check GENERATOR/VALIDATOR_LLM_PROVIDER and model names in .env)."
            )

    def _warmup_ollama_model(self, base_url: str, model_name: str) -> bool:
        """
        Pre-load an Ollama model into VRAM by sending an empty prompt with
        keep_alive=-1 (keep in memory indefinitely).

        This ensures the model is already in VRAM before the generation timer
        starts, so model-loading time is excluded from generation_time_s.

        Args:
            base_url:   Ollama server base URL (e.g. "http://localhost:11434").
            model_name: Name of the model to pre-load.

        Returns:
            True if pre-loading succeeded, False otherwise.
        """
        try:
            url = f"{base_url}/api/generate"
            # Empty prompt + keep_alive=-1: Ollama loads the model and responds immediately.
            payload = {"model": model_name, "prompt": "", "keep_alive": -1}
            resp = requests.post(url, json=payload, timeout=120)
            if resp.status_code == 200:
                self.log(f"  ✓ [Warmup] Model '{model_name}' loaded into VRAM ({base_url})")
                return True
            else:
                self.log(
                    f"  ⚠ [Warmup] Unexpected response (HTTP {resp.status_code}) "
                    f"for model '{model_name}'",
                    "WARNING"
                )
                return False
        except requests.exceptions.RequestException as e:
            self.log(
                f"  ⚠ [Warmup] Cannot contact {base_url}: {e}",
                "WARNING"
            )
            return False

    def _warmup_ollama_models(self) -> None:
        """
        Pre-load Generator and Validator Ollama models into VRAM.

        Call this AFTER _flush_ollama_context() and BEFORE starting the
        generation timer so that model-reload time is excluded from
        generation_time_s.
        """
        if not self._eval_flush_ollama:
            # If flush is disabled, models are already in VRAM - no warmup needed.
            return

        self.log("  [Warmup] Pre-loading models into VRAM (to exclude reload from timing)...")

        # --- Generator ---
        gen_provider = os.getenv("GENERATOR_LLM_PROVIDER", "ollama").lower()
        if gen_provider == "ollama":
            gen_url   = os.getenv("GENERATOR_OLLAMA_BASE_URL", "http://localhost:11434")
            gen_model = os.getenv("GENERATOR_OLLAMA_MODEL", "")
            if gen_model:
                self._warmup_ollama_model(gen_url, gen_model)

        # --- Validator ---
        val_provider = os.getenv("VALIDATOR_LLM_PROVIDER", "ollama").lower()
        if val_provider == "ollama":
            val_url   = os.getenv("VALIDATOR_OLLAMA_BASE_URL", "http://localhost:11434")
            val_model = os.getenv("VALIDATOR_OLLAMA_MODEL", "")
            if val_model:
                self._warmup_ollama_model(val_url, val_model)

        self.log("  ✓ [Warmup] Models ready in VRAM — starting generation timer.")

    # ========================================================================
    # ITERATIONS SWEEP
    # ========================================================================

    def run_iterations_sweep(self, bpmn_path, context, principles, iterations_range):
        """
        Run the evaluation varying the number of Generator-Validator LLM iterations.

        For each value of `n` in `iterations_range`:
          - Generate a mitigated BPMN with max_llm_iterations=n
          - Compute normalised GED (RGED) between original and mitigated BPMN
          - Compute cross-fitness between original and mitigated BPMN

        The threat analysis step is executed ONCE and reused for all iterations,
        isolating the effect of the iteration count.

        Args:
            bpmn_path:        Path to the test BPMN file.
            context:          Process context (dict).
            principles:       Security principles (list).
            iterations_range: Iterable of ints (e.g. range(1, 6) or [1, 3, 5]).

        Returns:
            List of dicts with results for each iteration value.
        """
        self.log("=" * 80)
        self.log("SWEEP: ANALYSIS VARYING NUMBER OF LLM ITERATIONS")
        self.log(f"Iterations range: {list(iterations_range)}")
        self.log("=" * 80)

        sweep_start = time.time()
        iterations_list = list(iterations_range)

        # ── 0. Health check ──────────────────────────────────────────────────
        if not self.check_backend_health():
            self.log("Sweep aborted: backend unavailable", "ERROR")
            return []

        # ── 1. Load original BPMN ─────────────────────────────────────────────
        original_bpmn = self.load_test_bpmn(bpmn_path)
        if not original_bpmn:
            self.log("Sweep aborted: unable to load BPMN", "ERROR")
            return []

        # ── 2. Validation (once only) ─────────────────────────────────────────
        self.validate_bpmn(bpmn_path)

        # ── 3. Threat analysis (once only) ───────────────────────────────────
        self.log("\nRunning threat analysis (shared across all iterations)...")
        threat_result = self.analyze_threats(bpmn_path, context, principles)
        if not threat_result:
            self.log("Sweep aborted: threat analysis failed", "ERROR")
            return []
        threat_analysis_text = threat_result.get('doc', '')

        # Convert original BPMN to pm4py object (once only)
        bpmn_orig_obj = self.bpmn_string_to_object(original_bpmn) if PM4PY_AVAILABLE else None

        # ── 4. Loop over iterations ──────────────────────────────────────────
        sweep_rows = []
        detail_rows = []   # one row per LLM sub-iteration

        for n_iter in iterations_list:
            self.log("\n" + "-" * 70)
            self.log(f"LLM ITERATIONS: {n_iter}")
            self.log("-" * 70)

            # ── Context isolation ─────────────────────────────────────────────
            # The backend creates NEW Generator LLM and Validator LLM instances on
            # every API call (local variables of generate_mitigated_bpmn_dual_llm).
            # ChatOllama does not accumulate history between invocations: each
            # invoke() sends a single fresh HumanMessage with no prior context.
            # The method below also flushes any KV-cache on the server side.
            self._flush_ollama_context()

            row = {
                'max_llm_iterations': n_iter,
                'generation_success': False,
                'generation_time_s': None,
                # ── LLM iteration tracking ──────────────────────────────────
                'llm_actual_iterations': None,       # how many sub-iterations were executed
                'llm_final_status': None,            # valid | invalid | failed | syntax_error
                'llm_final_xml_valid': None,         # True/False: syntactically valid XML
                'llm_final_issues_count': None,      # issues found by Validator in last iteration
                'llm_any_xml_error': None,           # True if at least one iteration had XML error
                'llm_xml_errors_count': None,        # number of iterations with XML error
                'llm_valid_iter_count': None,        # number of iterations Validator approved
                # ── structural / behavioural metrics ──────────────────────────
                'normalized_ged': None,
                'ged_raw': None,
                'ged_similarity': None,
                'graph_orig_nodes': None,
                'graph_orig_edges': None,
                'graph_mit_nodes': None,
                'graph_mit_edges': None,
                'behavioral_similarity': None,
                'fitness_orig_self': None,
                'fitness_mit_self': None,
                'fitness_mit_on_orig_log': None,
                'fitness_orig_on_mit_log': None,
                'error': None
            }

            iter_subdir = f"sweep_iter_{n_iter}"

            # ── 4a. Generate mitigated BPMN ───────────────────────────────────
            gen_start = time.time()
            mitigated_bpmn = self.generate_mitigated_bpmn(
                bpmn_path, context, principles, threat_analysis_text,
                max_llm_iterations=n_iter
            )
            gen_elapsed = time.time() - gen_start
            row['generation_time_s'] = round(gen_elapsed, 2)

            # ── 4a-bis. Read per-iteration LLM details ──────────────────────
            step_info = self.results.get("steps", {}).get("generate_mitigated_bpmn", {})
            dual_info = step_info.get("dual_llm_info") or {}
            llm_iter_history = dual_info.get("iterations_history", [])

            if llm_iter_history:
                # Compute summary statistics
                xml_errors   = [h for h in llm_iter_history
                                if h.get('status') in ('failed', 'syntax_error')]
                valid_iters  = [h for h in llm_iter_history if h.get('status') == 'valid']
                last         = llm_iter_history[-1]

                row['llm_actual_iterations']  = len(llm_iter_history)
                row['llm_final_status']       = last.get('status')
                row['llm_final_xml_valid']    = last.get('status') not in ('failed', 'syntax_error')
                row['llm_final_issues_count'] = last.get('issues_count', 0)
                row['llm_any_xml_error']      = len(xml_errors) > 0
                row['llm_xml_errors_count']   = len(xml_errors)
                row['llm_valid_iter_count']   = len(valid_iters)

                # Save LLM iteration detail JSON
                self.save_file(
                    json.dumps(llm_iter_history, indent=2, default=str),
                    "llm_iterations_detail.json",
                    iter_subdir
                )

                # Accumulate rows for the global detail CSV
                for h in llm_iter_history:
                    issues_str = " | ".join(h.get('issues', []))
                    detail_rows.append({
                        'max_llm_iterations':   n_iter,
                        'llm_sub_iteration':    h.get('iteration'),
                        'phase':                h.get('phase'),
                        'status':               h.get('status'),
                        'xml_valid':            h.get('status') not in ('failed', 'syntax_error'),
                        'validator_passed':     h.get('status') == 'valid',
                        'issues_count':         h.get('issues_count', 0),
                        'issues':               issues_str
                    })

                # Log sub-iteration summary
                self.log(f"  LLM sub-iterations: {len(llm_iter_history)}")
                for h in llm_iter_history:
                    icon = "✓" if h.get('status') == 'valid' else "✗"
                    self.log(
                        f"    [{icon}] sub-iter {h.get('iteration')} "
                        f"| status={h.get('status')} "
                        f"| issues={h.get('issues_count', 0)} "
                        f"| xml_valid={h.get('status') not in ('failed', 'syntax_error')}"
                    )

            if not mitigated_bpmn:
                row['error'] = 'generation_failed'
                self.log(f"  ✗ Generation failed for n_iter={n_iter}", "ERROR")
                sweep_rows.append(row)
                continue

            row['generation_success'] = True

            # Save mitigated BPMN for this iteration
            self.save_file(mitigated_bpmn, f"mitigated_bpmn_iter{n_iter}.xml", iter_subdir)

            # ── 4b. GED metrics ───────────────────────────────────────────────
            if PM4PY_AVAILABLE and bpmn_orig_obj is not None:
                bpmn_mit_obj = self.bpmn_string_to_object(mitigated_bpmn)

                if bpmn_mit_obj:
                    # GED
                    ged_res = self.calculate_ged(bpmn_orig_obj, bpmn_mit_obj)
                    if ged_res:
                        row['normalized_ged']   = round(ged_res['normalized_ged'], 6)
                        row['ged_raw']          = round(ged_res['ged'], 2)
                        row['ged_similarity']   = round(ged_res['similarity'], 6)
                        row['graph_orig_nodes'] = ged_res['graph1_nodes']
                        row['graph_orig_edges'] = ged_res['graph1_edges']
                        row['graph_mit_nodes']  = ged_res['graph2_nodes']
                        row['graph_mit_edges']  = ged_res['graph2_edges']
                        self.save_file(json.dumps(ged_res, indent=2),
                                       "ged_analysis.json", iter_subdir)

                    # ── 4c. Cross-fitness ─────────────────────────────────────
                    behav_res = self.calculate_behavioral_similarity(
                        bpmn_orig_obj, bpmn_mit_obj, num_traces=100
                    )
                    if behav_res:
                        row['behavioral_similarity']     = round(behav_res['behavioral_similarity'], 6)
                        f1s = behav_res.get('fitness_bpmn1_self')
                        f2s = behav_res.get('fitness_bpmn2_self')
                        f21 = behav_res.get('fitness_bpmn2_on_log1')
                        f12 = behav_res.get('fitness_bpmn1_on_log2')
                        row['fitness_orig_self']         = round(f1s['average_trace_fitness'], 6) if f1s else None
                        row['fitness_mit_self']          = round(f2s['average_trace_fitness'], 6) if f2s else None
                        row['fitness_mit_on_orig_log']   = round(f21['average_trace_fitness'], 6) if f21 else None
                        row['fitness_orig_on_mit_log']   = round(f12['average_trace_fitness'], 6) if f12 else None
                        self.save_file(json.dumps(behav_res, indent=2, default=str),
                                       "behavioral_similarity.json", iter_subdir)
                else:
                    row['error'] = 'bpmn_mit_conversion_failed'
            else:
                row['error'] = 'pm4py_unavailable' if not PM4PY_AVAILABLE else 'bpmn_orig_conversion_failed'

            self.log(f"  ✓ n_iter={n_iter} | RGED={row['normalized_ged']} | "
                     f"BehavSim={row['behavioral_similarity']} | time={row['generation_time_s']}s")
            sweep_rows.append(row)

        # ── 5. Save aggregated results ────────────────────────────────────────
        self.log("\n" + "=" * 80)
        self.log("ITERATIONS SWEEP RESULTS")
        self.log("=" * 80)

        # Full JSON
        sweep_results = {
            'sweep_timestamp': self.timestamp,
            'bpmn_path': str(bpmn_path),
            'iterations_range': iterations_list,
            'total_sweep_time_s': round(time.time() - sweep_start, 2),
            'rows': sweep_rows,
            'llm_iterations_detail': detail_rows
        }
        self.save_file(
            json.dumps(sweep_results, indent=2, default=str),
            "sweep_iterations_results.json"
        )

        # Summary CSV (one row per max_llm_iterations value)
        csv_fields = [
            'max_llm_iterations',
            'generation_success',
            'generation_time_s',
            'llm_actual_iterations',
            'llm_final_status',
            'llm_final_xml_valid',
            'llm_final_issues_count',
            'llm_any_xml_error',
            'llm_xml_errors_count',
            'llm_valid_iter_count',
            'normalized_ged',
            'ged_raw',
            'ged_similarity',
            'graph_orig_nodes', 'graph_orig_edges',
            'graph_mit_nodes',  'graph_mit_edges',
            'behavioral_similarity',
            'fitness_orig_self',
            'fitness_mit_self',
            'fitness_mit_on_orig_log',
            'fitness_orig_on_mit_log',
            'error'
        ]
        self.save_csv(sweep_rows, csv_fields, "sweep_iterations_results.csv")

        # Detail CSV (one row per LLM sub-iteration)
        detail_fields = [
            'max_llm_iterations',
            'llm_sub_iteration',
            'phase',
            'status',
            'xml_valid',
            'validator_passed',
            'issues_count',
            'issues'
        ]
        if detail_rows:
            self.save_csv(detail_rows, detail_fields, "sweep_llm_iterations_detail.csv")

        # Print summary table
        header = (f"{'iter':>4} | {'actual':>6} | {'final_status':>12} | "
                  f"{'xml_ok':>6} | {'issues':>6} | {'xml_errs':>8} | "
                  f"{'RGED':>10} | {'BehavSim':>9} | {'time(s)':>7}")
        self.log(header)
        self.log("-" * len(header))
        for r in sweep_rows:
            def _f(v): return f"{v:.4f}" if isinstance(v, float) else str(v) if v is not None else "  N/A  "
            self.log(
                f"{r['max_llm_iterations']:>4} | "
                f"{str(r['llm_actual_iterations'] or 'N/A'):>6} | "
                f"{str(r['llm_final_status'] or 'N/A'):>12} | "
                f"{str(r['llm_final_xml_valid'] or 'N/A'):>6} | "
                f"{str(r['llm_final_issues_count'] if r['llm_final_issues_count'] is not None else 'N/A'):>6} | "
                f"{str(r['llm_xml_errors_count'] if r['llm_xml_errors_count'] is not None else 'N/A'):>8} | "
                f"{_f(r['normalized_ged']):>10} | "
                f"{_f(r['behavioral_similarity']):>9} | "
                f"{str(r['generation_time_s']):>7}"
            )

        self.log("\n✓ Sweep completed.", "SUCCESS")
        self.log(f"  JSON:         {self.session_dir}/sweep_iterations_results.json")
        self.log(f"  Summary CSV:  {self.session_dir}/sweep_iterations_results.csv")
        self.log(f"  Detail CSV:   {self.session_dir}/sweep_llm_iterations_detail.csv")

        return sweep_rows

    # ========================================================================
    # RUNS SWEEP (fixed LLM iterations)
    # ========================================================================

    def run_runs_sweep(self, bpmn_path, context, principles, num_runs, fixed_llm_iterations):
        """
        Repeat the same evaluation process for a fixed number of runs while
        keeping the number of Generator-Validator LLM iterations constant.

        For each run from 1 to `num_runs`:
          - Generate a mitigated BPMN with max_llm_iterations=fixed_llm_iterations
          - Compute normalised GED (RGED) between original and mitigated BPMN
          - Compute cross-fitness between original and mitigated BPMN

        The threat analysis step is executed ONCE and reused for all runs,
        isolating the effect of LLM stochasticity.

        Ideal output for graph generation:
          X-axis → run number (1, 2, 3, ...)
          Y-axis → metric value (RGED, BehavSim, Fitness, ...)

        Args:
            bpmn_path:              Path to the test BPMN file.
            context:                Process context (dict).
            principles:             Security principles (list).
            num_runs:               Number of runs to execute.
            fixed_llm_iterations:   Fixed number of LLM iterations per run.

        Returns:
            List of dicts with results for each run.
        """
        self.log("=" * 80)
        self.log("SWEEP: ANALYSIS VARYING NUMBER OF RUNS (fixed LLM iterations)")
        self.log(f"Number of runs:             {num_runs}")
        self.log(f"LLM iterations per run:     {fixed_llm_iterations}")
        self.log("=" * 80)

        sweep_start = time.time()

        # ── 0. Health check ──────────────────────────────────────────────────
        if not self.check_backend_health():
            self.log("Sweep aborted: backend unavailable", "ERROR")
            return []

        # ── 1. Load original BPMN ─────────────────────────────────────────────
        original_bpmn = self.load_test_bpmn(bpmn_path)
        if not original_bpmn:
            self.log("Sweep aborted: unable to load BPMN", "ERROR")
            return []

        # ── 2. Validation (once only) ─────────────────────────────────────────
        self.validate_bpmn(bpmn_path)

        # ── 3. Threat analysis (once only) ───────────────────────────────────
        self.log("\nRunning threat analysis (shared across all runs)...")
        threat_result = self.analyze_threats(bpmn_path, context, principles)
        if not threat_result:
            self.log("Sweep aborted: threat analysis failed", "ERROR")
            return []
        threat_analysis_text = threat_result.get('doc', '')

        # Convert original BPMN to pm4py object (once only)
        bpmn_orig_obj = self.bpmn_string_to_object(original_bpmn) if PM4PY_AVAILABLE else None

        # ── 4. Loop over runs ─────────────────────────────────────────────────
        sweep_rows = []
        detail_rows = []   # one row per LLM sub-iteration

        for run_num in range(1, num_runs + 1):
            self.log("\n" + "-" * 70)
            self.log(f"RUN: {run_num}/{num_runs}  (max_llm_iterations={fixed_llm_iterations})")
            self.log("-" * 70)

            # ── Context isolation ─────────────────────────────────────────────
            self._flush_ollama_context()

            # ── Warmup: pre-load models into VRAM before the timer ────────────
            # generation_time_s measures ONLY BPMN generation time,
            # excluding model reload from the GPU.
            self._warmup_ollama_models()

            row = {
                'run_number':            run_num,
                'max_llm_iterations':    fixed_llm_iterations,
                'generation_success':    False,
                'generation_time_s':     None,
                # ── LLM iteration tracking ──────────────────────────────────
                'llm_actual_iterations': None,
                'llm_final_status':      None,
                'llm_final_xml_valid':   None,
                'llm_final_issues_count':None,
                'llm_any_xml_error':     None,
                'llm_xml_errors_count':  None,
                'llm_valid_iter_count':  None,
                # ── structural / behavioural metrics ──────────────────────────
                'normalized_ged':        None,
                'ged_raw':               None,
                'ged_similarity':        None,
                'graph_orig_nodes':      None,
                'graph_orig_edges':      None,
                'graph_mit_nodes':       None,
                'graph_mit_edges':       None,
                'behavioral_similarity': None,
                'fitness_orig_self':     None,
                'fitness_mit_self':      None,
                'fitness_mit_on_orig_log': None,
                'fitness_orig_on_mit_log': None,
                'error':                 None
            }

            run_subdir = f"run_{run_num}"

            # ── 4a. Generate mitigated BPMN ─────────────────────────────────────
            gen_start = time.time()
            mitigated_bpmn = self.generate_mitigated_bpmn(
                bpmn_path, context, principles, threat_analysis_text,
                max_llm_iterations=fixed_llm_iterations
            )
            gen_elapsed = time.time() - gen_start
            row['generation_time_s'] = round(gen_elapsed, 2)

            # ── 4a-bis. Read per-iteration LLM details ────────────────────
            step_info = self.results.get("steps", {}).get("generate_mitigated_bpmn", {})
            dual_info = step_info.get("dual_llm_info") or {}
            llm_iter_history = dual_info.get("iterations_history", [])

            if llm_iter_history:
                xml_errors  = [h for h in llm_iter_history
                               if h.get('status') in ('failed', 'syntax_error')]
                valid_iters = [h for h in llm_iter_history if h.get('status') == 'valid']
                last        = llm_iter_history[-1]

                row['llm_actual_iterations']   = len(llm_iter_history)
                row['llm_final_status']        = last.get('status')
                row['llm_final_xml_valid']     = last.get('status') not in ('failed', 'syntax_error')
                row['llm_final_issues_count']  = last.get('issues_count', 0)
                row['llm_any_xml_error']       = len(xml_errors) > 0
                row['llm_xml_errors_count']    = len(xml_errors)
                row['llm_valid_iter_count']    = len(valid_iters)

                self.save_file(
                    json.dumps(llm_iter_history, indent=2, default=str),
                    "llm_iterations_detail.json",
                    run_subdir
                )

                # Accumulate rows for the global detail CSV
                for h in llm_iter_history:
                    issues_str = " | ".join(h.get('issues', []))
                    detail_rows.append({
                        'run_number':         run_num,
                        'max_llm_iterations': fixed_llm_iterations,
                        'llm_sub_iteration':  h.get('iteration'),
                        'phase':              h.get('phase'),
                        'status':             h.get('status'),
                        'xml_valid':          h.get('status') not in ('failed', 'syntax_error'),
                        'validator_passed':   h.get('status') == 'valid',
                        'issues_count':       h.get('issues_count', 0),
                        'issues':             issues_str
                    })

                self.log(f"  LLM sub-iterations: {len(llm_iter_history)}")
                for h in llm_iter_history:
                    icon = "✓" if h.get('status') == 'valid' else "✗"
                    self.log(
                        f"    [{icon}] sub-iter {h.get('iteration')} "
                        f"| status={h.get('status')} "
                        f"| issues={h.get('issues_count', 0)} "
                        f"| xml_valid={h.get('status') not in ('failed', 'syntax_error')}"
                    )

            if not mitigated_bpmn:
                row['error'] = 'generation_failed'
                self.log(f"  ✗ Generation failed for run={run_num}", "ERROR")
                sweep_rows.append(row)
                continue

            row['generation_success'] = True

            # Save mitigated BPMN for this run
            self.save_file(mitigated_bpmn, f"mitigated_bpmn_run{run_num}.xml", run_subdir)

            # ── 4b. GED metrics ───────────────────────────────────────────────
            if PM4PY_AVAILABLE and bpmn_orig_obj is not None:
                bpmn_mit_obj = self.bpmn_string_to_object(mitigated_bpmn)

                if bpmn_mit_obj:
                    # GED
                    ged_res = self.calculate_ged(bpmn_orig_obj, bpmn_mit_obj)
                    if ged_res:
                        row['normalized_ged']   = round(ged_res['normalized_ged'], 6)
                        row['ged_raw']          = round(ged_res['ged'], 2)
                        row['ged_similarity']   = round(ged_res['similarity'], 6)
                        row['graph_orig_nodes'] = ged_res['graph1_nodes']
                        row['graph_orig_edges'] = ged_res['graph1_edges']
                        row['graph_mit_nodes']  = ged_res['graph2_nodes']
                        row['graph_mit_edges']  = ged_res['graph2_edges']
                        self.save_file(json.dumps(ged_res, indent=2),
                                       "ged_analysis.json", run_subdir)

                    # ── 4c. Cross-fitness ─────────────────────────────────────
                    behav_res = self.calculate_behavioral_similarity(
                        bpmn_orig_obj, bpmn_mit_obj, num_traces=100
                    )
                    if behav_res:
                        row['behavioral_similarity']   = round(behav_res['behavioral_similarity'], 6)
                        f1s = behav_res.get('fitness_bpmn1_self')
                        f2s = behav_res.get('fitness_bpmn2_self')
                        f21 = behav_res.get('fitness_bpmn2_on_log1')
                        f12 = behav_res.get('fitness_bpmn1_on_log2')
                        row['fitness_orig_self']       = round(f1s['average_trace_fitness'], 6) if f1s else None
                        row['fitness_mit_self']        = round(f2s['average_trace_fitness'], 6) if f2s else None
                        row['fitness_mit_on_orig_log'] = round(f21['average_trace_fitness'], 6) if f21 else None
                        row['fitness_orig_on_mit_log'] = round(f12['average_trace_fitness'], 6) if f12 else None
                        self.save_file(json.dumps(behav_res, indent=2, default=str),
                                       "behavioral_similarity.json", run_subdir)
                else:
                    row['error'] = 'bpmn_mit_conversion_failed'
            else:
                row['error'] = 'pm4py_unavailable' if not PM4PY_AVAILABLE else 'bpmn_orig_conversion_failed'

            self.log(
                f"  ✓ run={run_num} | RGED={row['normalized_ged']} | "
                f"BehavSim={row['behavioral_similarity']} | time={row['generation_time_s']}s"
            )
            sweep_rows.append(row)

        # ── 5. Save aggregated results ────────────────────────────────────────
        self.log("\n" + "=" * 80)
        self.log("RUNS SWEEP RESULTS")
        self.log("=" * 80)

        # Full JSON
        sweep_results = {
            'sweep_timestamp':        self.timestamp,
            'bpmn_path':              str(bpmn_path),
            'num_runs':               num_runs,
            'fixed_llm_iterations':   fixed_llm_iterations,
            'total_sweep_time_s':     round(time.time() - sweep_start, 2),
            'rows':                   sweep_rows,
            'llm_iterations_detail':  detail_rows
        }
        self.save_file(
            json.dumps(sweep_results, indent=2, default=str),
            "runs_sweep_results.json"
        )

        # Summary CSV (one row per run)
        csv_fields = [
            'run_number',
            'max_llm_iterations',
            'generation_success',
            'generation_time_s',
            'llm_actual_iterations',
            'llm_final_status',
            'llm_final_xml_valid',
            'llm_final_issues_count',
            'llm_any_xml_error',
            'llm_xml_errors_count',
            'llm_valid_iter_count',
            'normalized_ged',
            'ged_raw',
            'ged_similarity',
            'graph_orig_nodes', 'graph_orig_edges',
            'graph_mit_nodes',  'graph_mit_edges',
            'behavioral_similarity',
            'fitness_orig_self',
            'fitness_mit_self',
            'fitness_mit_on_orig_log',
            'fitness_orig_on_mit_log',
            'error'
        ]
        self.save_csv(sweep_rows, csv_fields, "runs_sweep_results.csv")

        # Detail CSV (one row per LLM sub-iteration)
        detail_fields = [
            'run_number',
            'max_llm_iterations',
            'llm_sub_iteration',
            'phase',
            'status',
            'xml_valid',
            'validator_passed',
            'issues_count',
            'issues'
        ]
        if detail_rows:
            self.save_csv(detail_rows, detail_fields, "runs_sweep_llm_detail.csv")

        # Print summary table
        header = (
            f"{'run':>4} | {'actual':>6} | {'final_status':>12} | "
            f"{'xml_ok':>6} | {'issues':>6} | {'xml_errs':>8} | "
            f"{'RGED':>10} | {'BehavSim':>9} | {'time(s)':>7}"
        )
        self.log(header)
        self.log("-" * len(header))
        for r in sweep_rows:
            def _f(v): return f"{v:.4f}" if isinstance(v, float) else str(v) if v is not None else "  N/A  "
            self.log(
                f"{r['run_number']:>4} | "
                f"{str(r['llm_actual_iterations'] or 'N/A'):>6} | "
                f"{str(r['llm_final_status'] or 'N/A'):>12} | "
                f"{str(r['llm_final_xml_valid'] or 'N/A'):>6} | "
                f"{str(r['llm_final_issues_count'] if r['llm_final_issues_count'] is not None else 'N/A'):>6} | "
                f"{str(r['llm_xml_errors_count'] if r['llm_xml_errors_count'] is not None else 'N/A'):>8} | "
                f"{_f(r['normalized_ged']):>10} | "
                f"{_f(r['behavioral_similarity']):>9} | "
                f"{str(r['generation_time_s']):>7}"
            )

        self.log("\n✓ Runs sweep completed.", "SUCCESS")
        self.log(f"  JSON:         {self.session_dir}/runs_sweep_results.json")
        self.log(f"  Summary CSV:  {self.session_dir}/runs_sweep_results.csv")
        if detail_rows:
            self.log(f"  Detail CSV:   {self.session_dir}/runs_sweep_llm_detail.csv")

        return sweep_rows

    def generate_report(self):
        """Generate a textual evaluation report."""
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
            "STEPS SUMMARY",
            "=" * 80,
            ""
        ]

        # Steps summary
        for step_name, step_data in self.results["steps"].items():
            status = "✓ SUCCESS" if step_data.get("success", False) else "✗ FAILED"
            report_lines.append(f"{step_name}: {status}")
            if "elapsed_time" in step_data:
                report_lines.append(f"  Time: {step_data['elapsed_time']:.2f}s")
            if "error" in step_data:
                report_lines.append(f"  Error: {step_data['error']}")
            report_lines.append("")

        # Timings
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

        # Analysis
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
                report_lines.append(f"  Control flow complexity: {orig_comp['control_flow_complexity']}")
                report_lines.append(f"  Task complexity: {orig_comp['task_complexity']}")
                report_lines.append("")

            if "mitigated_complexity" in analysis and analysis["mitigated_complexity"]:
                mit_comp = analysis["mitigated_complexity"]
                report_lines.append("Mitigated BPMN Complexity:")
                report_lines.append(f"  Total elements: {mit_comp['total_elements']}")
                report_lines.append(f"  Control flow complexity: {mit_comp['control_flow_complexity']}")
                report_lines.append(f"  Task complexity: {mit_comp['task_complexity']}")
                report_lines.append("")

            if "ged_metrics" in analysis and analysis["ged_metrics"]:
                ged = analysis["ged_metrics"]
                report_lines.append("=== Graph Edit Distance (GED) ===")
                report_lines.append(f"  GED: {ged['ged']:.2f}")
                report_lines.append(f"  Normalised GED: {ged['normalized_ged']:.4f}")
                report_lines.append(f"  Similarity (1-RGED): {ged['similarity']:.4f} ({ged['similarity']*100:.2f}%)")
                report_lines.append(f"  Graph 1: {ged['graph1_nodes']} nodes, {ged['graph1_edges']} edges")
                report_lines.append(f"  Graph 2: {ged['graph2_nodes']} nodes, {ged['graph2_edges']} edges")
                report_lines.append("")

            if "structural_similarity_advanced" in analysis and analysis["structural_similarity_advanced"]:
                struct = analysis["structural_similarity_advanced"]
                report_lines.append("=== Advanced Structural Similarity ===")
                report_lines.append(f"  Overall similarity: {struct['structural_similarity']:.4f} ({struct['structural_similarity']*100:.2f}%)")
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
                report_lines.append("  Original BPMN Fitness (self):")
                if 'fitness_bpmn1_self' in behav and behav['fitness_bpmn1_self']:
                    f1 = behav['fitness_bpmn1_self']
                    report_lines.append(f"    - Average trace fitness: {f1.get('average_trace_fitness', 'N/A'):.4f}")
                    report_lines.append(f"    - Percentage fit traces: {f1.get('percentage_of_fitting_traces', 'N/A'):.4f}")
                report_lines.append("")
                report_lines.append("  Mitigated BPMN Fitness (self):")
                if 'fitness_bpmn2_self' in behav and behav['fitness_bpmn2_self']:
                    f2 = behav['fitness_bpmn2_self']
                    report_lines.append(f"    - Average trace fitness: {f2.get('average_trace_fitness', 'N/A'):.4f}")
                    report_lines.append(f"    - Percentage fit traces: {f2.get('percentage_of_fitting_traces', 'N/A'):.4f}")
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
        Run the complete evaluation pipeline.

        Args:
            bpmn_path:  Path to the test BPMN file.
            context:    Process context (dict).
            principles: Security principles (list).

        Returns:
            Dict with all results.
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

        validation_result = self.validate_bpmn(bpmn_path)
        if not validation_result or not validation_result.get('valid', False):
            self.log("Warning: BPMN is invalid, continuing anyway...", "WARNING")

        threat_analysis_result = self.analyze_threats(bpmn_path, context, principles)
        if not threat_analysis_result:
            self.log("Evaluation aborted: threat analysis failed", "ERROR")
            return self.results

        threat_analysis_text = threat_analysis_result.get('doc', '')

        mitigated_bpmn = self.generate_mitigated_bpmn(
            bpmn_path,
            context,
            principles,
            threat_analysis_text
        )

        if not mitigated_bpmn:
            self.log("Evaluation aborted: mitigated BPMN generation failed", "ERROR")
            return self.results

        self.download_bpmn(mitigated_bpmn)
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
        self.log(f"  Results saved to: {self.session_dir}")
        self.log("=" * 80)

        return self.results


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """
    BPMN Threat Analysis & Mitigation evaluation script.

    Available modes (set via EVAL_RUN_MODE in the .env file):

      'runs_sweep'  : Fixes the number of LLM iterations (EVAL_FIXED_LLM_ITERATIONS)
                      and repeats the run EVAL_NUM_RUNS times. Graphs show how
                      metrics (RGED, BehavSim, Fitness) vary across runs → ideal
                      for analysing LLM stochastic variability.

      'sweep'       : Varies the number of LLM iterations (EVAL_ITERATIONS_RANGE)
                      while keeping the BPMN and threat analysis fixed → ideal
                      for analysing how metrics change with the number of
                      Generator/Validator iterations.

      'single'      : Runs a single full evaluation using the number of iterations
                      configured via MAX_LLM_ITERATIONS in the .env.

    All parameters are configurable in .env (EVALUATION SCRIPT CONFIGURATION
    section). No need to edit this file.
    """
    from dotenv import load_dotenv
    load_dotenv()

    # =========================================================================
    # CONFIGURATION — edit values in the .env file
    # =========================================================================

    # Execution mode: 'runs_sweep' | 'sweep' | 'single'
    RUN_MODE = os.getenv("EVAL_RUN_MODE", "runs_sweep")

    # FastAPI backend URL
    BACKEND_URL = os.getenv("EVAL_BACKEND_URL", "http://localhost:8000")

    # Absolute path to the BPMN file to analyse
    BPMN_TEST_PATH = os.getenv("EVAL_BPMN_TEST_PATH", "")

    # [runs_sweep] Fixed number of LLM iterations per run
    FIXED_LLM_ITERATIONS = int(os.getenv("EVAL_FIXED_LLM_ITERATIONS", "5"))

    # [runs_sweep] Total number of runs
    NUM_RUNS = int(os.getenv("EVAL_NUM_RUNS", "10"))

    # [sweep] Iterations list: CSV string → list of ints
    # Example in .env: EVAL_ITERATIONS_RANGE=1,2,3,4,5
    _iter_raw = os.getenv("EVAL_ITERATIONS_RANGE", "1,2,3,4,5")
    ITERATIONS_RANGE = [int(x.strip()) for x in _iter_raw.split(",") if x.strip()]

    # Process context: JSON string in .env
    # Example: EVAL_CONTEXT={"process_name": "Order management"}
    CONTEXT = json.loads(os.getenv("EVAL_CONTEXT", "{}"))

    # Security principles: CSV string in .env
    # Example: EVAL_PRINCIPLES=Integrity,Confidentiality
    _princ_raw = os.getenv("EVAL_PRINCIPLES", "Integrity")
    PRINCIPLES = [p.strip() for p in _princ_raw.split(",") if p.strip()]

    # Output directory
    OUTPUT_DIR = os.getenv("EVAL_OUTPUT_DIR", "evaluation_results")

    # =========================================================================

    evaluator = BPMNEvaluator(
        backend_url=BACKEND_URL,
        output_dir=OUTPUT_DIR
    )

    if RUN_MODE == "runs_sweep":
        print("\n" + "=" * 80)
        print("MODE: RUNS SWEEP (fixed LLM iterations)")
        print(f"Fixed LLM iterations: {FIXED_LLM_ITERATIONS}")
        print(f"Number of runs:       {NUM_RUNS}")
        print("=" * 80)

        sweep_rows = evaluator.run_runs_sweep(
            bpmn_path=BPMN_TEST_PATH,
            context=CONTEXT,
            principles=PRINCIPLES,
            num_runs=NUM_RUNS,
            fixed_llm_iterations=FIXED_LLM_ITERATIONS
        )

        print("\n" + "=" * 80)
        print("RUNS SWEEP SUMMARY")
        print("=" * 80)
        successful = [r for r in sweep_rows if r.get('generation_success')]
        print(f"Runs executed         : {len(sweep_rows)}")
        print(f"Successful generations: {len(successful)}")
        print(f"Fixed LLM iterations  : {FIXED_LLM_ITERATIONS}")
        print(f"Output directory      : {evaluator.session_dir}")
        print(f"  → runs_sweep_results.csv")
        print(f"  → runs_sweep_results.json")
        print("=" * 80)

    elif RUN_MODE == "sweep":
        print("\n" + "=" * 80)
        print("MODE: LLM ITERATIONS SWEEP")
        print(f"Iterations range: {list(ITERATIONS_RANGE)}")
        print("=" * 80)

        sweep_rows = evaluator.run_iterations_sweep(
            bpmn_path=BPMN_TEST_PATH,
            context=CONTEXT,
            principles=PRINCIPLES,
            iterations_range=ITERATIONS_RANGE
        )

        print("\n" + "=" * 80)
        print("ITERATIONS SWEEP SUMMARY")
        print("=" * 80)
        successful = [r for r in sweep_rows if r.get('generation_success')]
        print(f"Iterations tested    : {len(sweep_rows)}")
        print(f"Successful generations: {len(successful)}")
        print(f"Output directory     : {evaluator.session_dir}")
        print(f"  → sweep_iterations_results.csv")
        print(f"  → sweep_iterations_results.json")
        print("=" * 80)

    else:  # 'single'
        print("\n" + "=" * 80)
        print("MODE: SINGLE EVALUATION")
        print("=" * 80)

        results = evaluator.run_full_evaluation(
            bpmn_path=BPMN_TEST_PATH,
            context=CONTEXT,
            principles=PRINCIPLES
        )

        success_count = sum(1 for step in results["steps"].values() if step.get("success", False))
        total_steps = len(results["steps"])
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        print(f"Steps completed successfully: {success_count}/{total_steps}")
        print(f"Total time: {results.get('total_evaluation_time', 0):.2f}s")
        print(f"Output directory: {evaluator.session_dir}")
        print("=" * 80)


if __name__ == "__main__":
    main()
