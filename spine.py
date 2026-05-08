"""
evez-spine — Unified append-only hash-chained event log.
Merges: evez-claw/src/spine.py + MAES event schema + evez-os FIRE events + revenue bridge.

One wire. All domains. No deletes.
"""
import hashlib
import json
import time
from typing import Optional, List, Dict, Any
from enum import Enum

class EventDomain(str, Enum):
    COGNITION = "cognition"      # evez-os FIRE events, rounds, control volumes
    AGENT = "agent"              # MAES agent ecology, OODA cycles
    REVENUE = "revenue"          # Stripe events, credit API, transactions
    SECURITY = "security"        # CTF findings, egress alerts, DNS intel
    CONSCIOUSNESS = "consciousness"  # lord-evez666, quantum LORD, Φ measurements
    IDENTITY = "identity"        # credit scoring, invariance battery
    INFRASTRUCTURE = "infra"     # deployments, tunnels, service health

class EventStatus(str, Enum):
    CANONICAL = "CANONICAL"
    CONTESTED = "CONTESTED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    ALERT = "ALERT"

class Spine:
    """
    Append-only cryptographically-chained event log.
    Compatible with: evez-claw Spine, MAES MAESEvent, evez-os FIRE spine, revenue_bridge.
    """
    
    def __init__(self, domain: str = "general", genesis_meta: Optional[Dict] = None):
        self.events: List[Dict] = []
        self.domain = domain
        self.genesis_time = time.time()
        self.genesis_hash = self._hash("genesis")
        self.meta = genesis_meta or {}
    
    def log(
        self,
        event_type: str,
        data: Any,
        domain: Optional[str] = None,
        confidence: float = 1.0,
        status: str = EventStatus.CANONICAL.value,
        caused_by: Optional[str] = None,
        fire_event_id: Optional[str] = None,
        coordinates: Optional[Dict] = None,
    ) -> Dict:
        """Append event to spine. Returns the full event with hash."""
        predecessor = self.events[-1]["hash"] if self.events else self.genesis_hash
        index = len(self.events)
        timestamp = time.time()
        
        event = {
            "eventId": f"{self.domain}-{index:06d}",
            "index": index,
            "timestamp": timestamp,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp)),
            "type": event_type,
            "domain": domain or self.domain,
            "data": data,
            "predecessor": predecessor,
            "confidence": confidence,
            "status": status,
            "causedBy": caused_by,
            "fire_event_id": fire_event_id,
            "coordinates": coordinates,
        }
        
        event["hash"] = self._hash(json.dumps(event, sort_keys=True, default=str))
        self.events.append(event)
        return event
    
    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_chain(self) -> tuple:
        """Verify full cryptographic integrity. Returns (bool, message)."""
        for i, event in enumerate(self.events):
            event_copy = {k: v for k, v in event.items() if k != "hash"}
            computed = self._hash(json.dumps(event_copy, sort_keys=True, default=str))
            if computed != event["hash"]:
                return False, f"Hash mismatch at index {i}"
            if i > 0 and event["predecessor"] != self.events[i-1]["hash"]:
                return False, f"Chain break at index {i}"
        return True, f"Chain intact ({len(self.events)} events)"
    
    def query(self, domain: Optional[str] = None, event_type: Optional[str] = None,
              status: Optional[str] = None, min_confidence: float = 0.0) -> List[Dict]:
        """Filter events by domain, type, status, confidence."""
        results = self.events
        if domain:
            results = [e for e in results if e.get("domain") == domain]
        if event_type:
            results = [e for e in results if e.get("type") == event_type]
        if status:
            results = [e for e in results if e.get("status") == status]
        if min_confidence > 0:
            results = [e for e in results if e.get("confidence", 0) >= min_confidence]
        return results
    
    def latest(self, n: int = 1) -> List[Dict]:
        return self.events[-n:]
    
    def stats(self) -> Dict:
        """Spine statistics."""
        domains = {}
        statuses = {}
        for e in self.events:
            d = e.get("domain", "unknown")
            s = e.get("status", "unknown")
            domains[d] = domains.get(d, 0) + 1
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total_events": len(self.events),
            "domains": domains,
            "statuses": statuses,
            "chain_valid": self.verify_chain()[0],
            "genesis_hash": self.genesis_hash[:16],
            "latest_hash": self.events[-1]["hash"][:16] if self.events else None,
        }
    
    def export(self, filename: str):
        with open(filename, 'w') as f:
            json.dump({"meta": self.meta, "events": self.events}, f, indent=2)
    
    def export_jsonl(self, filename: str):
        """Append-only JSONL format — same as lord-evez666 revenue spine."""
        with open(filename, 'a') as f:
            for e in self.events:
                f.write(json.dumps(e, default=str) + "\n")
    
    @classmethod
    def from_file(cls, filename: str) -> 'Spine':
        with open(filename, 'r') as f:
            data = json.load(f)
        spine = cls(genesis_meta=data.get("meta", {}))
        spine.events = data.get("events", [])
        return spine


if __name__ == "__main__":
    # Demo: create a spine with events from every domain
    s = Spine(domain="evez", genesis_meta={"version": "1.0.0", "operator": "viktor"})
    
    # Cognition event (FIRE)
    s.log("FIRE_ROUND", {"round": 89, "cv": 43, "V_v2": 1.911309, "fire_res": 0.0},
          domain=EventDomain.COGNITION, confidence=0.95)
    
    # Agent event (OODA)
    s.log("OODA_CYCLE", {"observe": 18, "orient": 5, "branch": "build", "act": "deployed"},
          domain=EventDomain.AGENT, confidence=0.82)
    
    # Revenue event
    s.log("STRIPE_CHARGE", {"amount_usd": 49.00, "product": "CTF-001", "status": "succeeded"},
          domain=EventDomain.REVENUE, confidence=1.0)
    
    # Security finding
    s.log("EGRESS_ALERT", {"finding": "Zero egress filtering", "severity": "HIGH"},
          domain=EventDomain.SECURITY, status=EventStatus.ALERT.value, confidence=0.95)
    
    print(json.dumps(s.stats(), indent=2))
    valid, msg = s.verify_chain()
    print(f"Chain: {msg}")
