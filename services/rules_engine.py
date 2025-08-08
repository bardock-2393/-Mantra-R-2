"""
Configurable Rules Engine
Domain-agnostic event detection with flexible rule configuration
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass
from config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class EventRule:
    """Individual event detection rule"""
    rule_id: str
    name: str
    description: str
    analysis_type: str
    event_type: str
    conditions: Dict[str, Any]
    severity: str  # critical, high, medium, low
    confidence_threshold: float
    enabled: bool = True

@dataclass
class EventMatch:
    """Event match result"""
    rule_id: str
    event_type: str
    confidence: float
    severity: str
    timestamp: float
    location: str
    attributes: Dict[str, Any]
    evidence: Dict[str, Any]

class ConfigurableRulesEngine:
    """Domain-agnostic rules engine for event detection"""
    
    def __init__(self, config):
        self.config = config
        self.rules: Dict[str, EventRule] = {}
        self.domain_rules: Dict[str, List[str]] = {}
        self._load_default_rules()
        self._load_domain_specific_rules()
    
    def _load_default_rules(self):
        """Load default domain-agnostic rules"""
        default_rules = [
            # Comprehensive Analysis Rules
            EventRule(
                rule_id="comp_001",
                name="Human Detection",
                description="Detect presence of humans in video",
                analysis_type="comprehensive_analysis",
                event_type="human_presence",
                conditions={
                    "object_class": "person",
                    "confidence_min": 0.7,
                    "duration_min": 1.0
                },
                severity="medium",
                confidence_threshold=0.7
            ),
            EventRule(
                rule_id="comp_002",
                name="Object Interaction",
                description="Detect human-object interactions",
                analysis_type="comprehensive_analysis",
                event_type="object_interaction",
                conditions={
                    "object_classes": ["person", "object"],
                    "proximity_threshold": 50,
                    "duration_min": 2.0
                },
                severity="medium",
                confidence_threshold=0.6
            ),
            
            # Safety Investigation Rules
            EventRule(
                rule_id="safety_001",
                name="Safety Violation",
                description="Detect potential safety violations",
                analysis_type="safety_investigation",
                event_type="safety_violation",
                conditions={
                    "unsafe_behaviors": ["no_helmet", "no_safety_gear", "unsafe_position"],
                    "confidence_min": 0.8
                },
                severity="high",
                confidence_threshold=0.8
            ),
            EventRule(
                rule_id="safety_002",
                name="Emergency Situation",
                description="Detect emergency or dangerous situations",
                analysis_type="safety_investigation",
                event_type="emergency_situation",
                conditions={
                    "indicators": ["rapid_movement", "alarm_sounds", "evacuation_signs"],
                    "confidence_min": 0.9
                },
                severity="critical",
                confidence_threshold=0.9
            ),
            
            # Performance Analysis Rules
            EventRule(
                rule_id="perf_001",
                name="Efficiency Pattern",
                description="Detect efficiency patterns in workflow",
                analysis_type="performance_analysis",
                event_type="efficiency_pattern",
                conditions={
                    "metrics": ["speed", "accuracy", "consistency"],
                    "threshold": 0.8
                },
                severity="medium",
                confidence_threshold=0.7
            ),
            EventRule(
                rule_id="perf_002",
                name="Performance Issue",
                description="Detect performance problems or delays",
                analysis_type="performance_analysis",
                event_type="performance_issue",
                conditions={
                    "indicators": ["slow_movement", "repeated_actions", "errors"],
                    "duration_min": 5.0
                },
                severity="high",
                confidence_threshold=0.75
            ),
            
            # Pattern Detection Rules
            EventRule(
                rule_id="pattern_001",
                name="Behavioral Pattern",
                description="Detect recurring behavioral patterns",
                analysis_type="pattern_detection",
                event_type="behavioral_pattern",
                conditions={
                    "pattern_type": "recurring",
                    "frequency_min": 3,
                    "time_window": 300
                },
                severity="medium",
                confidence_threshold=0.7
            ),
            EventRule(
                rule_id="pattern_002",
                name="Anomaly Detection",
                description="Detect unusual or anomalous behavior",
                analysis_type="pattern_detection",
                event_type="anomaly_detection",
                conditions={
                    "deviation_threshold": 2.0,
                    "confidence_min": 0.8
                },
                severity="high",
                confidence_threshold=0.8
            ),
            
            # Creative Review Rules
            EventRule(
                rule_id="creative_001",
                name="Visual Quality",
                description="Assess visual quality and composition",
                analysis_type="creative_review",
                event_type="visual_quality",
                conditions={
                    "aspects": ["lighting", "composition", "color_balance"],
                    "quality_threshold": 0.7
                },
                severity="medium",
                confidence_threshold=0.6
            ),
            EventRule(
                rule_id="creative_002",
                name="Brand Alignment",
                description="Check brand consistency and alignment",
                analysis_type="creative_review",
                event_type="brand_alignment",
                conditions={
                    "brand_elements": ["colors", "logos", "messaging"],
                    "consistency_threshold": 0.8
                },
                severity="medium",
                confidence_threshold=0.7
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
    
    def _load_domain_specific_rules(self):
        """Load domain-specific rule sets"""
        self.domain_rules = {
            "traffic": ["traffic_violation", "accident_detection", "traffic_flow"],
            "workplace": ["safety_violation", "efficiency_pattern", "workflow_analysis"],
            "retail": ["customer_behavior", "sales_pattern", "security_incident"],
            "sports": ["performance_analysis", "injury_detection", "tactical_analysis"],
            "entertainment": ["creative_review", "audience_reaction", "production_quality"],
            "education": ["learning_pattern", "engagement_analysis", "behavioral_assessment"]
        }
    
    def detect_events(self, 
                     visual_events: List[Dict], 
                     audio_events: List[Dict],
                     analysis_type: str = "comprehensive_analysis",
                     domain: str = None) -> List[EventMatch]:
        """Detect events based on configured rules"""
        matches = []
        
        # Get relevant rules for analysis type
        relevant_rules = [
            rule for rule in self.rules.values() 
            if rule.analysis_type == analysis_type and rule.enabled
        ]
        
        # Add domain-specific rules if specified
        if domain and domain in self.domain_rules:
            domain_rule_ids = self.domain_rules[domain]
            relevant_rules.extend([
                rule for rule in self.rules.values()
                if rule.event_type in domain_rule_ids and rule.enabled
            ])
        
        # Process visual events
        for event in visual_events:
            for rule in relevant_rules:
                match = self._evaluate_rule(event, rule, "visual")
                if match:
                    matches.append(match)
        
        # Process audio events
        for event in audio_events:
            for rule in relevant_rules:
                match = self._evaluate_rule(event, rule, "audio")
                if match:
                    matches.append(match)
        
        # Process multi-modal events (visual + audio correlation)
        multi_modal_matches = self._detect_multi_modal_events(
            visual_events, audio_events, relevant_rules
        )
        matches.extend(multi_modal_matches)
        
        return matches
    
    def _evaluate_rule(self, event: Dict, rule: EventRule, modality: str) -> Optional[EventMatch]:
        """Evaluate if an event matches a rule"""
        try:
            confidence = 0.0
            attributes = {}
            
            # Check rule conditions
            if rule.event_type == "human_presence":
                if event.get("object_class") == "person":
                    confidence = event.get("confidence", 0.0)
                    if confidence >= rule.confidence_threshold:
                        attributes = {
                            "object_class": event.get("object_class"),
                            "bbox": event.get("bbox"),
                            "track_id": event.get("track_id")
                        }
            
            elif rule.event_type == "safety_violation":
                # Check for safety violations
                unsafe_indicators = self._detect_safety_violations(event)
                if unsafe_indicators:
                    confidence = max(unsafe_indicators.values())
                    if confidence >= rule.confidence_threshold:
                        attributes = {"violations": unsafe_indicators}
            
            elif rule.event_type == "efficiency_pattern":
                # Check for efficiency patterns
                efficiency_score = self._calculate_efficiency_score(event)
                if efficiency_score >= rule.confidence_threshold:
                    confidence = efficiency_score
                    attributes = {"efficiency_score": efficiency_score}
            
            elif rule.event_type == "behavioral_pattern":
                # Check for behavioral patterns
                pattern_confidence = self._detect_behavioral_patterns(event)
                if pattern_confidence >= rule.confidence_threshold:
                    confidence = pattern_confidence
                    attributes = {"pattern_type": "behavioral"}
            
            elif rule.event_type == "visual_quality":
                # Assess visual quality
                quality_score = self._assess_visual_quality(event)
                if quality_score >= rule.confidence_threshold:
                    confidence = quality_score
                    attributes = {"quality_score": quality_score}
            
            # Create match if confidence threshold met
            if confidence >= rule.confidence_threshold:
                return EventMatch(
                    rule_id=rule.rule_id,
                    event_type=rule.event_type,
                    confidence=confidence,
                    severity=rule.severity,
                    timestamp=event.get("timestamp", 0.0),
                    location=event.get("location", "unknown"),
                    attributes=attributes,
                    evidence={
                        "modality": modality,
                        "original_event": event,
                        "rule_applied": rule.name
                    }
                )
        
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
        
        return None
    
    def _detect_multi_modal_events(self, 
                                  visual_events: List[Dict], 
                                  audio_events: List[Dict],
                                  rules: List[EventRule]) -> List[EventMatch]:
        """Detect events that require both visual and audio data"""
        matches = []
        
        # Temporal alignment window (seconds)
        alignment_window = 2.0
        
        for v_event in visual_events:
            v_time = v_event.get("timestamp", 0.0)
            
            # Find audio events within alignment window
            aligned_audio = [
                a_event for a_event in audio_events
                if abs(a_event.get("timestamp", 0.0) - v_time) <= alignment_window
            ]
            
            if aligned_audio:
                # Check for multi-modal patterns
                for rule in rules:
                    if rule.event_type in ["emergency_situation", "performance_issue", "anomaly_detection"]:
                        match = self._evaluate_multi_modal_rule(v_event, aligned_audio, rule)
                        if match:
                            matches.append(match)
        
        return matches
    
    def _evaluate_multi_modal_rule(self, 
                                  visual_event: Dict, 
                                  audio_events: List[Dict], 
                                  rule: EventRule) -> Optional[EventMatch]:
        """Evaluate multi-modal rules"""
        try:
            # Emergency situation detection
            if rule.event_type == "emergency_situation":
                # Check for rapid movement + alarm sounds
                rapid_movement = self._detect_rapid_movement(visual_event)
                alarm_sounds = any(
                    "alarm" in a_event.get("sound_type", "").lower() 
                    for a_event in audio_events
                )
                
                if rapid_movement and alarm_sounds:
                    return EventMatch(
                        rule_id=rule.rule_id,
                        event_type=rule.event_type,
                        confidence=0.9,
                        severity="critical",
                        timestamp=visual_event.get("timestamp", 0.0),
                        location=visual_event.get("location", "unknown"),
                        attributes={
                            "rapid_movement": True,
                            "alarm_sounds": True
                        },
                        evidence={
                            "modality": "multi_modal",
                            "visual_event": visual_event,
                            "audio_events": audio_events
                        }
                    )
        
        except Exception as e:
            logger.error(f"Error evaluating multi-modal rule {rule.rule_id}: {e}")
        
        return None
    
    def _detect_safety_violations(self, event: Dict) -> Dict[str, float]:
        """Detect safety violations in an event"""
        violations = {}
        
        # Check for no helmet (if person detected)
        if event.get("object_class") == "person":
            # Simple heuristic - could be enhanced with more sophisticated detection
            if not event.get("has_helmet", True):
                violations["no_helmet"] = 0.8
        
        # Check for unsafe positioning
        if event.get("position") == "unsafe":
            violations["unsafe_position"] = 0.9
        
        return violations
    
    def _calculate_efficiency_score(self, event: Dict) -> float:
        """Calculate efficiency score for performance analysis"""
        # Simple efficiency calculation - could be enhanced
        speed_score = event.get("speed", 0.5)
        accuracy_score = event.get("accuracy", 0.5)
        consistency_score = event.get("consistency", 0.5)
        
        return (speed_score + accuracy_score + consistency_score) / 3.0
    
    def _detect_behavioral_patterns(self, event: Dict) -> float:
        """Detect behavioral patterns"""
        # Simple pattern detection - could be enhanced with ML
        if event.get("recurring_behavior"):
            return 0.8
        return 0.0
    
    def _assess_visual_quality(self, event: Dict) -> float:
        """Assess visual quality of the event"""
        # Simple quality assessment - could be enhanced
        lighting_score = event.get("lighting_quality", 0.5)
        composition_score = event.get("composition_quality", 0.5)
        color_score = event.get("color_balance", 0.5)
        
        return (lighting_score + composition_score + color_score) / 3.0
    
    def _detect_rapid_movement(self, event: Dict) -> bool:
        """Detect rapid movement in visual event"""
        # Simple rapid movement detection
        velocity = event.get("velocity", 0.0)
        return velocity > 50.0  # pixels per second threshold
    
    def add_custom_rule(self, rule: EventRule):
        """Add a custom rule to the engine"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added custom rule: {rule.name}")
    
    def enable_rule(self, rule_id: str):
        """Enable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"Enabled rule: {rule_id}")
    
    def disable_rule(self, rule_id: str):
        """Disable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"Disabled rule: {rule_id}")
    
    def get_rules_for_analysis_type(self, analysis_type: str) -> List[EventRule]:
        """Get all rules for a specific analysis type"""
        return [
            rule for rule in self.rules.values()
            if rule.analysis_type == analysis_type
        ]
    
    def export_rules(self) -> Dict[str, Any]:
        """Export current rules configuration"""
        return {
            "rules": {rule_id: {
                "name": rule.name,
                "description": rule.description,
                "analysis_type": rule.analysis_type,
                "event_type": rule.event_type,
                "conditions": rule.conditions,
                "severity": rule.severity,
                "confidence_threshold": rule.confidence_threshold,
                "enabled": rule.enabled
            } for rule_id, rule in self.rules.items()},
            "domain_rules": self.domain_rules
        }
    
    def import_rules(self, rules_config: Dict[str, Any]):
        """Import rules configuration"""
        # Clear existing rules
        self.rules.clear()
        
        # Import rules
        for rule_id, rule_data in rules_config.get("rules", {}).items():
            rule = EventRule(
                rule_id=rule_id,
                name=rule_data["name"],
                description=rule_data["description"],
                analysis_type=rule_data["analysis_type"],
                event_type=rule_data["event_type"],
                conditions=rule_data["conditions"],
                severity=rule_data["severity"],
                confidence_threshold=rule_data["confidence_threshold"],
                enabled=rule_data.get("enabled", True)
            )
            self.rules[rule_id] = rule
        
        # Import domain rules
        self.domain_rules = rules_config.get("domain_rules", {})
        
        logger.info(f"Imported {len(self.rules)} rules") 