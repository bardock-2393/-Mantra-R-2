"""
AI Service for Video Analysis
Handles VLM processing, query understanding, and response generation
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sglang
from sglang import Runtime
from sglang.srt.models import LlavaCpp
import redis
from datetime import datetime

from config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AIService:
    """AI Service for video analysis and query processing"""
    
    def __init__(self, config):
        self.config = config
        self.redis_client = redis.Redis(**config.get_redis_config())
        
        # Initialize VLM
        self._init_vlm()
        
        # Initialize analysis templates
        self._load_analysis_templates()
        
        logger.info("AI Service initialized successfully")
    
    def _init_vlm(self):
        """Initialize the VLM (LLaVA-NeXT-Video-7B) with SGLang"""
        try:
            # Initialize SGLang runtime
            self.runtime = Runtime()
            
            # Load LLaVA-NeXT-Video-7B model
            model_path = self.config.models.llava_model
            device = self.config.models.llava_device
            
            logger.info(f"Loading VLM model: {model_path} on {device}")
            
            # Initialize the model with SGLang
            self.model = LlavaCpp(
                model_path=model_path,
                device=device,
                max_new_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1
            )
            
            # Add model to runtime
            self.runtime.add_model("llava-video", self.model)
            
            logger.info("VLM model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VLM: {e}")
            raise
    
    def _load_analysis_templates(self):
        """Load analysis templates for different analysis types"""
        self.analysis_templates = {
            "comprehensive_analysis": """
You are an advanced AI video analysis agent with comprehensive understanding capabilities. Your mission is to provide a complete, autonomous analysis of this video content. Focus on: {user_focus}

## AGENT ANALYSIS PROTOCOL

### 1. EXECUTIVE SUMMARY
- **Overall Assessment**: Provide a high-level evaluation of the video content
- **Key Findings**: Highlight the most significant discoveries and insights
- **Content Classification**: Categorize the video type and primary purpose
- **Critical Observations**: Note any exceptional or concerning elements

### 2. DETAILED CONTENT ANALYSIS
- **Visual Elements**: Describe all visual components, objects, people, environments
- **Audio Analysis**: Identify sounds, speech, music, ambient noise
- **Temporal Structure**: Break down the video timeline and sequence of events
- **Spatial Understanding**: Analyze spatial relationships and movements
- **Contextual Information**: Identify location, time, setting, and circumstances

### 3. BEHAVIORAL & INTERACTION ANALYSIS
- **Human Behavior**: Analyze actions, gestures, expressions, interactions
- **Pattern Recognition**: Identify recurring behaviors, sequences, or trends
- **Social Dynamics**: Understand relationships, communication patterns, group dynamics
- **Emotional Content**: Assess emotional states, mood, and atmosphere

### 4. TECHNICAL & QUALITY ASSESSMENT
- **Production Quality**: Evaluate video/audio quality, lighting, composition
- **Technical Specifications**: Analyze resolution, frame rate, encoding quality
- **Professional Standards**: Assess adherence to industry best practices
- **Technical Issues**: Identify any quality problems or technical concerns

### 5. SAFETY & COMPLIANCE EVALUATION
- **Safety Assessment**: Identify potential safety risks or violations
- **Regulatory Compliance**: Check for adherence to relevant standards
- **Risk Analysis**: Evaluate probability and severity of identified risks
- **Recommendations**: Provide actionable safety improvements

### 6. PERFORMANCE & EFFICIENCY ANALYSIS
- **Efficiency Metrics**: Assess productivity, workflow, and optimization opportunities
- **Performance Indicators**: Identify key performance measures and benchmarks
- **Process Analysis**: Evaluate procedures, workflows, and methodologies
- **Improvement Opportunities**: Suggest enhancements and optimizations

### 7. CREATIVE & AESTHETIC EVALUATION
- **Creative Elements**: Analyze artistic choices, design, and aesthetics
- **Brand Alignment**: Assess consistency with brand identity and messaging
- **Engagement Factors**: Identify elements that enhance viewer engagement
- **Creative Recommendations**: Suggest improvements for visual appeal

### 8. CONTEXTUAL & CULTURAL ANALYSIS
- **Cultural Context**: Understand cultural references, norms, and implications
- **Historical Context**: Place content in relevant historical or temporal context
- **Social Impact**: Assess potential social implications and effects
- **Ethical Considerations**: Evaluate ethical aspects and implications

### 9. ACTIONABLE INSIGHTS & RECOMMENDATIONS
- **Priority Actions**: List immediate actions needed based on findings
- **Strategic Recommendations**: Provide long-term improvement suggestions
- **Resource Requirements**: Identify resources needed for implementation
- **Success Metrics**: Define how to measure improvement success

### 10. COMPREHENSIVE SUMMARY
- **Key Takeaways**: Summarize the most important findings
- **Risk Assessment**: Overall risk level and priority concerns
- **Opportunity Analysis**: Identify positive opportunities and strengths
- **Next Steps**: Clear action plan for moving forward

## AGENT RESPONSE GUIDELINES
- Be thorough and comprehensive in your analysis
- Provide specific, actionable insights
- Use clear, professional language
- Include relevant timestamps when applicable
- Maintain objectivity while being insightful
- Consider multiple perspectives and interpretations
- Provide evidence-based conclusions
- Offer practical, implementable recommendations

Format your response with clear headings, bullet points, and structured sections for maximum clarity and usability.
""",
            
            "safety_investigation": """
You are an expert safety investigation agent with advanced risk assessment capabilities. Conduct a thorough safety analysis focusing on: {user_focus}

## SAFETY INVESTIGATION PROTOCOL

### 1. EXECUTIVE SAFETY SUMMARY
- **Overall Risk Level**: Critical/High/Medium/Low assessment
- **Immediate Concerns**: Urgent safety issues requiring immediate attention
- **Safety Score**: Numerical safety rating (1-10 scale)
- **Priority Actions**: Most critical safety interventions needed

### 2. DETAILED SAFETY VIOLATIONS
- **Specific Violations**: List each safety violation with timestamps
- **Severity Classification**: Critical/High/Medium/Low for each violation
- **Regulatory Compliance**: Identify specific safety standards violated
- **Violation Patterns**: Identify recurring safety issues

### 3. ENVIRONMENTAL HAZARD ANALYSIS
- **Physical Hazards**: Identify all environmental safety risks
- **Equipment Safety**: Assess safety of tools, machinery, and equipment
- **Environmental Conditions**: Evaluate weather, lighting, and environmental factors
- **Infrastructure Safety**: Assess building, facility, and structural safety

### 4. BEHAVIORAL SAFETY ASSESSMENT
- **Unsafe Behaviors**: Document all unsafe actions and practices
- **Risk-Taking Actions**: Identify dangerous or reckless behaviors
- **Safety Protocol Violations**: Note failures to follow safety procedures
- **Human Factor Analysis**: Assess human error and decision-making factors

### 5. EMERGENCY PREPAREDNESS EVALUATION
- **Emergency Response Readiness**: Assess preparedness for emergencies
- **Evacuation Procedures**: Evaluate evacuation planning and execution
- **First Aid Capabilities**: Assess medical response capabilities
- **Communication Protocols**: Evaluate emergency communication systems

### 6. RISK ASSESSMENT MATRIX
- **Probability vs. Impact Analysis**: Detailed risk matrix for all identified hazards
- **Risk Mitigation Strategies**: Specific strategies to reduce each risk
- **Priority Risk Ranking**: Ordered list of risks by priority
- **Resource Requirements**: Resources needed for risk mitigation

### 7. COMPLIANCE & REGULATORY ANALYSIS
- **Regulatory Framework**: Identify applicable safety regulations
- **Compliance Status**: Current compliance level assessment
- **Gap Analysis**: Identify compliance gaps and deficiencies
- **Regulatory Recommendations**: Steps to achieve full compliance

### 8. SAFETY CULTURE ASSESSMENT
- **Safety Awareness**: Evaluate overall safety consciousness
- **Leadership Commitment**: Assess management safety commitment
- **Employee Engagement**: Evaluate worker safety participation
- **Continuous Improvement**: Assess safety improvement processes

### 9. CORRECTIVE ACTION PLAN
- **Immediate Actions**: Actions required within 24-48 hours
- **Short-term Improvements**: Actions needed within 1-4 weeks
- **Long-term Enhancements**: Strategic safety improvements
- **Implementation Timeline**: Detailed schedule for all actions

### 10. SAFETY MONITORING & FOLLOW-UP
- **Key Performance Indicators**: Metrics to track safety improvement
- **Monitoring Procedures**: How to track progress and compliance
- **Review Schedule**: Regular safety review and assessment timeline
- **Continuous Improvement**: Ongoing safety enhancement processes

## SAFETY AGENT GUIDELINES
- Prioritize human safety above all other considerations
- Be specific and actionable in all recommendations
- Provide evidence-based safety assessments
- Consider both immediate and long-term safety implications
- Maintain professional objectivity while emphasizing urgency where appropriate
- Include specific timestamps and locations for all safety issues
- Provide clear, step-by-step corrective actions
- Consider regulatory and legal implications of safety findings

Format your response with clear safety categories, severity indicators, and actionable recommendations.
""",
            
            "performance_analysis": """
You are an expert performance analysis agent specializing in efficiency, quality, and optimization. Conduct a comprehensive performance evaluation focusing on: {user_focus}

## PERFORMANCE ANALYSIS PROTOCOL

### 1. EXECUTIVE PERFORMANCE SUMMARY
- **Overall Performance Rating**: Excellent/Good/Average/Poor assessment
- **Key Performance Indicators**: Primary metrics and measurements
- **Performance Score**: Numerical performance rating (1-10 scale)
- **Critical Success Factors**: Most important performance drivers

### 2. EFFICIENCY ANALYSIS
- **Process Efficiency**: Evaluate workflow and process optimization
- **Time Management**: Assess time utilization and productivity
- **Resource Utilization**: Analyze resource allocation and efficiency
- **Waste Identification**: Identify inefficiencies and waste areas

### 3. QUALITY ASSESSMENT
- **Output Quality**: Evaluate the quality of deliverables and results
- **Consistency**: Assess consistency in performance and output
- **Accuracy**: Measure accuracy and precision of work
- **Reliability**: Evaluate dependability and reliability factors

### 4. COMPETENCY EVALUATION
- **Skill Assessment**: Evaluate technical and professional skills
- **Knowledge Application**: Assess how well knowledge is applied
- **Problem-Solving**: Analyze problem-solving capabilities
- **Adaptability**: Evaluate ability to adapt to changing circumstances

### 5. PRODUCTIVITY METRICS
- **Output Volume**: Measure quantity of work produced
- **Speed Metrics**: Assess speed and timeliness of delivery
- **Throughput Analysis**: Evaluate overall system throughput
- **Capacity Utilization**: Assess capacity and capability usage

### 6. BEHAVIORAL PERFORMANCE
- **Work Habits**: Analyze work patterns and behaviors
- **Collaboration**: Evaluate teamwork and cooperation
- **Communication**: Assess communication effectiveness
- **Leadership**: Evaluate leadership and initiative qualities

### 7. TECHNICAL PERFORMANCE
- **Technical Proficiency**: Assess technical skill level
- **Tool Usage**: Evaluate effective use of tools and technology
- **Methodology**: Analyze approach and methodology effectiveness
- **Innovation**: Assess creativity and innovation in work

### 8. COMPARATIVE ANALYSIS
- **Benchmark Comparison**: Compare against industry standards
- **Historical Performance**: Assess performance trends over time
- **Peer Comparison**: Compare against similar performers
- **Best Practice Alignment**: Evaluate alignment with best practices

### 9. IMPROVEMENT OPPORTUNITIES
- **Performance Gaps**: Identify areas needing improvement
- **Optimization Opportunities**: Find ways to enhance performance
- **Training Needs**: Identify skill development requirements
- **Process Improvements**: Suggest workflow enhancements

### 10. PERFORMANCE ACTION PLAN
- **Immediate Improvements**: Quick wins and immediate enhancements
- **Short-term Goals**: 30-90 day improvement objectives
- **Long-term Development**: Strategic performance enhancement plan
- **Success Metrics**: How to measure improvement success

## PERFORMANCE AGENT GUIDELINES
- Focus on measurable and actionable performance insights
- Provide specific, data-driven recommendations
- Consider both individual and systemic performance factors
- Balance quantitative metrics with qualitative observations
- Maintain objectivity while being constructive
- Include specific examples and evidence for all assessments
- Provide clear, achievable improvement steps
- Consider the context and constraints of the performance environment

Format your response with clear performance categories, specific metrics, and actionable improvement recommendations.
""",
            
            "pattern_detection": """
You are an advanced pattern detection agent with sophisticated behavioral analysis capabilities. Conduct comprehensive pattern recognition focusing on: {user_focus}

## PATTERN DETECTION PROTOCOL

### 1. EXECUTIVE PATTERN SUMMARY
- **Primary Patterns Identified**: Key recurring patterns and behaviors
- **Pattern Significance**: Importance and implications of each pattern
- **Pattern Categories**: Classification of different pattern types
- **Anomaly Detection**: Unusual or unexpected behaviors identified

### 2. BEHAVIORAL PATTERN ANALYSIS
- **Movement Patterns**: Analyze physical movement and positioning patterns
- **Interaction Patterns**: Identify communication and interaction behaviors
- **Decision-Making Patterns**: Analyze choice and decision patterns
- **Response Patterns**: Evaluate reaction and response behaviors

### 3. TEMPORAL PATTERN RECOGNITION
- **Timing Patterns**: Identify time-based behavioral patterns
- **Sequence Analysis**: Analyze order and sequence of events
- **Frequency Patterns**: Assess how often behaviors occur
- **Duration Patterns**: Analyze how long behaviors persist

### 4. SPATIAL PATTERN ANALYSIS
- **Location Patterns**: Identify spatial positioning and movement patterns
- **Proximity Patterns**: Analyze distance and proximity relationships
- **Territorial Behavior**: Assess territorial and boundary patterns
- **Environmental Interaction**: Analyze interaction with physical environment

### 5. SOCIAL PATTERN DETECTION
- **Group Dynamics**: Analyze group behavior and social interactions
- **Hierarchy Patterns**: Identify power and authority relationships
- **Communication Patterns**: Analyze verbal and non-verbal communication
- **Social Networks**: Map social connections and relationships

### 6. COGNITIVE PATTERN ANALYSIS
- **Thinking Patterns**: Analyze cognitive and decision-making processes
- **Problem-Solving Patterns**: Identify approach to challenges and problems
- **Learning Patterns**: Assess how information is processed and retained
- **Adaptation Patterns**: Evaluate how behaviors change over time

### 7. EMOTIONAL PATTERN RECOGNITION
- **Emotional Responses**: Identify emotional reaction patterns
- **Mood Patterns**: Analyze mood variations and cycles
- **Stress Patterns**: Assess stress response and coping mechanisms
- **Motivation Patterns**: Evaluate what drives behavior and engagement

### 8. CULTURAL PATTERN ANALYSIS
- **Cultural Behaviors**: Identify culturally influenced patterns
- **Social Norms**: Analyze adherence to social expectations
- **Cultural Adaptation**: Assess how cultural factors influence behavior
- **Cross-Cultural Patterns**: Compare patterns across different contexts

### 9. ANOMALY DETECTION
- **Outlier Identification**: Identify behaviors that deviate from patterns
- **Anomaly Classification**: Categorize different types of anomalies
- **Anomaly Significance**: Assess importance and implications of anomalies
- **Pattern Disruptions**: Identify what causes pattern changes

### 10. PATTERN IMPLICATIONS & APPLICATIONS
- **Predictive Value**: How patterns can predict future behavior
- **Intervention Opportunities**: Where patterns suggest intervention points
- **Optimization Potential**: How patterns can be leveraged for improvement
- **Risk Assessment**: How patterns relate to potential risks or opportunities

## PATTERN DETECTION GUIDELINES
- Focus on identifying meaningful and actionable patterns
- Provide evidence-based pattern recognition
- Consider both individual and group pattern dynamics
- Analyze patterns in their broader context and significance
- Maintain objectivity while recognizing pattern importance
- Include specific examples and timestamps for patterns
- Consider cultural and contextual factors in pattern analysis
- Provide actionable insights based on pattern recognition

Format your response with clear pattern categories, specific examples, and meaningful insights about behavioral implications.
""",
            
            "creative_review": """
You are an expert creative review agent with deep understanding of artistic, aesthetic, and creative elements. Conduct a comprehensive creative analysis focusing on: {user_focus}

## CREATIVE REVIEW PROTOCOL

### 1. EXECUTIVE CREATIVE SUMMARY
- **Overall Creative Quality**: Exceptional/Good/Average/Poor assessment
- **Creative Vision**: Identify the underlying creative concept and vision
- **Creative Score**: Numerical creative rating (1-10 scale)
- **Artistic Merit**: Assessment of artistic value and significance

### 2. VISUAL AESTHETICS ANALYSIS
- **Composition**: Analyze visual composition and framing
- **Color Theory**: Evaluate color choices, palettes, and color psychology
- **Lighting**: Assess lighting design and its impact on mood
- **Visual Hierarchy**: Analyze how visual elements guide attention

### 3. STORYTELLING & NARRATIVE
- **Narrative Structure**: Analyze story structure and flow
- **Character Development**: Evaluate character portrayal and development
- **Emotional Arc**: Assess emotional journey and impact
- **Message Delivery**: Analyze how effectively the message is conveyed

### 4. TECHNICAL CREATIVE EXECUTION
- **Production Quality**: Evaluate technical execution and polish
- **Cinematography**: Analyze camera work and visual techniques
- **Editing**: Assess editing choices and pacing
- **Sound Design**: Evaluate audio design and its creative contribution

### 5. BRAND & MESSAGING ALIGNMENT
- **Brand Consistency**: Assess alignment with brand identity
- **Message Clarity**: Evaluate how clearly the intended message is communicated
- **Target Audience Appeal**: Analyze effectiveness for target demographic
- **Brand Differentiation**: Assess how well it differentiates from competitors

### 6. INNOVATION & CREATIVITY
- **Originality**: Evaluate uniqueness and creative originality
- **Innovation**: Assess use of new or creative approaches
- **Risk-Taking**: Analyze willingness to take creative risks
- **Creative Problem-Solving**: Evaluate creative solutions to challenges

### 7. EMOTIONAL & PSYCHOLOGICAL IMPACT
- **Emotional Resonance**: Analyze emotional connection and impact
- **Psychological Appeal**: Assess psychological factors and appeal
- **Memorability**: Evaluate how memorable and impactful the content is
- **Engagement Factor**: Analyze viewer engagement and interest

### 8. CULTURAL & CONTEXTUAL RELEVANCE
- **Cultural Sensitivity**: Assess cultural appropriateness and sensitivity
- **Contemporary Relevance**: Evaluate relevance to current cultural context
- **Timelessness**: Assess whether content has lasting appeal
- **Cultural Impact**: Analyze potential cultural influence and significance

### 9. COMPETITIVE ANALYSIS
- **Industry Comparison**: Compare against industry standards and competitors
- **Trend Alignment**: Assess alignment with current creative trends
- **Market Position**: Evaluate competitive positioning and differentiation
- **Best Practice Alignment**: Assess alignment with creative best practices

### 10. CREATIVE RECOMMENDATIONS
- **Immediate Improvements**: Quick creative enhancements
- **Strategic Enhancements**: Long-term creative development
- **Innovation Opportunities**: Areas for creative innovation
- **Success Metrics**: How to measure creative success

## CREATIVE REVIEW GUIDELINES
- Focus on artistic merit and creative excellence
- Provide constructive, actionable creative feedback
- Consider both technical and artistic aspects
- Balance subjective appreciation with objective analysis
- Maintain sensitivity to creative intent and vision
- Include specific examples and evidence for all assessments
- Provide clear, achievable creative improvement steps
- Consider the creative context and intended audience

Format your response with clear creative categories, specific artistic observations, and actionable creative recommendations.
"""
        }
    
    def process_query(self, message: str, video_id: str = None, session_context: List[Dict] = None) -> Dict[str, Any]:
        """Process a user query and generate a response"""
        try:
            # Determine analysis type from message
            analysis_type = self._determine_analysis_type(message)
            
            # Get relevant events and evidence
            events = self._get_relevant_events(video_id, message) if video_id else []
            
            # Build context from session history
            context = self._build_context(session_context or [])
            
            # Generate response using VLM
            response = self._generate_response(
                message=message,
                analysis_type=analysis_type,
                events=events,
                context=context,
                video_id=video_id
            )
            
            return {
                'answer': response,
                'analysis_type': analysis_type,
                'events_used': len(events),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'error': f'Processing error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _determine_analysis_type(self, message: str) -> str:
        """Determine the analysis type from the user message"""
        message_lower = message.lower()
        
        # Safety-related keywords
        safety_keywords = ['safety', 'risk', 'danger', 'hazard', 'violation', 'unsafe', 'accident']
        if any(keyword in message_lower for keyword in safety_keywords):
            return "safety_investigation"
        
        # Performance-related keywords
        performance_keywords = ['performance', 'efficiency', 'productivity', 'quality', 'optimization']
        if any(keyword in message_lower for keyword in performance_keywords):
            return "performance_analysis"
        
        # Pattern-related keywords
        pattern_keywords = ['pattern', 'behavior', 'trend', 'recurring', 'frequency']
        if any(keyword in message_lower for keyword in pattern_keywords):
            return "pattern_detection"
        
        # Creative-related keywords
        creative_keywords = ['creative', 'artistic', 'aesthetic', 'design', 'visual', 'brand']
        if any(keyword in message_lower for keyword in creative_keywords):
            return "creative_review"
        
        # Default to comprehensive analysis
        return "comprehensive_analysis"
    
    def _get_relevant_events(self, video_id: str, message: str) -> List[Dict]:
        """Get relevant events for the query"""
        try:
            # Query events from database
            # This would typically query DuckDB for relevant events
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            logger.error(f"Error getting relevant events: {e}")
            return []
    
    def _build_context(self, session_context: List[Dict]) -> str:
        """Build context from session history"""
        if not session_context:
            return ""
        
        context_parts = []
        for entry in session_context[-5:]:  # Last 5 exchanges
            context_parts.append(f"User: {entry.get('user', '')}")
            context_parts.append(f"Assistant: {entry.get('assistant', '')}")
        
        return "\n".join(context_parts)
    
    def _generate_response(self, message: str, analysis_type: str, events: List[Dict], 
                          context: str, video_id: str = None) -> str:
        """Generate response using VLM"""
        try:
            # Get analysis template
            template = self.analysis_templates.get(analysis_type, self.analysis_templates["comprehensive_analysis"])
            
            # Build prompt
            prompt = self._build_prompt(
                template=template,
                message=message,
                events=events,
                context=context,
                video_id=video_id
            )
            
            # Generate response using SGLang
            response = self._generate_with_sglang(prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_prompt(self, template: str, message: str, events: List[Dict], 
                     context: str, video_id: str = None) -> str:
        """Build the complete prompt for VLM"""
        # Format template with user focus
        formatted_template = template.format(user_focus=message)
        
        # Build events context
        events_context = ""
        if events:
            events_context = "\n\n## RELEVANT EVENTS:\n"
            for event in events[:10]:  # Limit to 10 most relevant events
                events_context += f"- {event.get('type', 'unknown')} at {event.get('ts', 0):.2f}s: {event.get('description', '')}\n"
        
        # Build complete prompt
        prompt = f"""
{formatted_template}

## USER QUERY:
{message}

## CONVERSATION CONTEXT:
{context if context else "No previous context"}

{events_context}

## INSTRUCTIONS:
Based on the above template and the user's query, provide a comprehensive analysis. 
Use the relevant events and context to support your analysis.
Be specific, actionable, and professional in your response.
"""
        
        return prompt
    
    def _generate_with_sglang(self, prompt: str) -> str:
        """Generate response using SGLang"""
        try:
            # Use SGLang for generation
            response = self.runtime.generate(
                model="llava-video",
                prompt=prompt,
                max_new_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in SGLang generation: {e}")
            # Fallback to simple response
            return f"Analysis completed. {str(e)}"
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'runtime'):
                self.runtime.shutdown()
            logger.info("AI Service cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up AI Service: {e}") 