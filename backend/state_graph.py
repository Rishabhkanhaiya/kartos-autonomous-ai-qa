"""
State Graph Engine (Finite State Machine / Directed Graph Explorer)
Computes structural hashes of interactive DOM trees and tracks UI transitions (URLs, modals, drawers).
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Tuple

class StateNode:
    def __init__(
        self,
        node_id: str,
        state_hash: str,
        url: str,
        title: str,
        interactive_elements: Dict[str, Any],
        screenshot_b64: Optional[str] = None
    ):
        self.id = node_id
        self.state_hash = state_hash
        self.url = url
        self.title = title
        self.element_count = len(interactive_elements)
        self.screenshot_b64 = screenshot_b64
        self.timestamp = time.time()
        self.visits = 1
        self.bug_count = 0
        self.is_buggy = False
        self.bugs: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "state_hash": self.state_hash,
            "url": self.url,
            "title": self.title,
            "element_count": self.element_count,
            "screenshot_b64": self.screenshot_b64,
            "timestamp": self.timestamp,
            "visits": self.visits,
            "bug_count": self.bug_count,
            "is_buggy": self.is_buggy,
            "bugs": self.bugs
        }

class StateEdge:
    def __init__(
        self,
        from_node: str,
        to_node: str,
        action_type: str,
        mark_id: Optional[int] = None,
        target_description: str = ""
    ):
        self.id = f"{from_node}->{to_node}:{action_type}:{mark_id or 0}"
        self.from_node = from_node
        self.to_node = to_node
        self.action_type = action_type
        self.mark_id = mark_id
        self.target_description = target_description
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from": self.from_node,
            "to": self.to_node,
            "action_type": self.action_type,
            "mark_id": self.mark_id,
            "target_description": self.target_description,
            "timestamp": self.timestamp
        }

class StateGraph:
    """
    Maintains the directed state graph G = (V, E) of UI states and transitions.
    """
    def __init__(self):
        self.nodes: Dict[str, StateNode] = {}
        self.edges: List[StateEdge] = []
        self.hash_to_node_id: Dict[str, str] = {}
        self.node_counter = 0
        self.current_node_id: Optional[str] = None

    @staticmethod
    def compute_hash(url: str, elements: Dict[str, Any]) -> str:
        """
        Calculates deterministic MD5 hash based on URL and sorted interactive element signatures.
        """
        signatures = []
        for mark_id, el in elements.items():
            sig = f"{el.get('tag')}|{el.get('role')}|{el.get('text', '')[:30]}|{el.get('selector', '')}"
            signatures.append(sig)
        
        signatures.sort()
        raw_payload = f"{url}::{'///'.join(signatures)}"
        return hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()[:16]

    def register_or_update_state(
        self,
        url: str,
        title: str,
        elements: Dict[str, Any],
        screenshot_b64: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Registers a state if new, or updates visit count if already seen.
        Returns (node_id, is_new).
        """
        state_hash = self.compute_hash(url, elements)

        if state_hash in self.hash_to_node_id:
            node_id = self.hash_to_node_id[state_hash]
            node = self.nodes[node_id]
            node.visits += 1
            if screenshot_b64 and not node.screenshot_b64:
                node.screenshot_b64 = screenshot_b64
            self.current_node_id = node_id
            return node_id, False

        # New unique UI state discovered!
        self.node_counter += 1
        node_id = f"state_{self.node_counter}"
        new_node = StateNode(
            node_id=node_id,
            state_hash=state_hash,
            url=url,
            title=title or f"State {self.node_counter}",
            interactive_elements=elements,
            screenshot_b64=screenshot_b64
        )
        self.nodes[node_id] = new_node
        self.hash_to_node_id[state_hash] = node_id
        self.current_node_id = node_id
        return node_id, True

    def record_transition(
        self,
        from_id: str,
        to_id: str,
        action_type: str,
        mark_id: Optional[int] = None,
        target_description: str = ""
    ) -> StateEdge:
        """
        Records an edge between two UI states.
        """
        edge = StateEdge(
            from_node=from_id,
            to_node=to_id,
            action_type=action_type,
            mark_id=mark_id,
            target_description=target_description
        )
        # Avoid duplicate identical parallel edges
        for existing in self.edges:
            if (
                existing.from_node == from_id and
                existing.to_node == to_id and
                existing.action_type == action_type and
                existing.mark_id == mark_id
            ):
                return existing

        self.edges.append(edge)
        return edge

    def mark_bug(self, node_id: str, bug_title: str) -> None:
        """
        Flags a state node as containing a verified bug.
        """
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.is_buggy = True
            node.bug_count += 1
            node.bugs.append(bug_title)

    def to_dict(self) -> Dict[str, Any]:
        """
        Exports the entire graph for frontend visualization and telemetry.
        """
        return {
            "current_node_id": self.current_node_id,
            "total_states": len(self.nodes),
            "total_transitions": len(self.edges),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges]
        }
