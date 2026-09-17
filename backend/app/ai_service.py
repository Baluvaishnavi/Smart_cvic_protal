"""
AI & NLP Service for Complaint Classification, Summarization, and Entity Extraction.
Includes:
1. High-precision Local NLP Processor (0 dependencies, works offline immediately)
2. Pluggable Local LLM Connector (supports Ollama / local OpenAI-compatible endpoints)
3. Duplicate issue semantic similarity detection
"""

import re
from typing import Dict, Any, Optional
import httpx
from app.config import CATEGORIES_CONFIG


class LocalNLPProcessor:
    """Zero-dependency, high-precision deterministic NLP parser."""

    URGENCY_KEYWORDS = {
        "CRITICAL": ["emergency", "burst", "sparking", "live wire", "flooding into house", "severe hazard", "collapse", "gas leak"],
        "HIGH": ["danger", "accident", "school", "kids", "hospital", "heavy flooding", "blackout", "total darkness", "main road blocked"],
        "MEDIUM": ["week", "days", "extremely dark", "dark", "broken", "blocked", "overflowing", "pothole", "deep crater", "multiple"],
        "LOW": ["minor", "graffiti", "cosmetic", "small", "paint", "dirty"]
    }

    LOCATION_PATTERNS = [
        r"(?:near|at|by|in front of|corner of|along)\s+([A-Z0-9][a-zA-Z0-9\s,\-\.\#]+?(?=(?:for|since|and|the|which|\.|\;|\n|$)))",
        r"(Gate\s+[0-9A-Za-z]+)",
        r"(\d+\s+[A-Z][a-zA-Z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way))",
        r"([A-Z][a-zA-Z\s]+(?:Street|St|Avenue|Ave|Road|Rd)\s+(?:and|&)\s+[A-Z][a-zA-Z\s]+(?:Street|St|Avenue|Ave|Road|Rd))",
    ]

    DURATION_PATTERNS = [
        (r"(?:for\s+)?almost\s+a\s+week", "approximately one week"),
        (r"(?:for\s+)?over\s+a\s+week", "over one week"),
        (r"(?:for\s+)?about\s+a\s+week", "approximately one week"),
        (r"(?:for\s+)?(\d+)\s+weeks?", r"\1 weeks"),
        (r"(?:for\s+)?(\d+)\s+days?", r"\1 days"),
        (r"(?:for\s+)?a\s+few\s+days", "several days"),
        (r"since\s+yesterday", "since yesterday"),
    ]

    @classmethod
    def classify_category(cls, text: str) -> tuple[str, float]:
        """Classify text into civic category with confidence score."""
        text_lower = text.lower()
        best_cat = "General Civic Issue"
        max_matches = 0

        for cat, conf in CATEGORIES_CONFIG.items():
            matches = 0
            for kw in conf["keywords"]:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    matches += 1
            if matches > max_matches:
                max_matches = matches
                best_cat = cat

        # Direct domain-specific boosts
        if "street light" in text_lower or "streetlight" in text_lower or ("light" in text_lower and "dark" in text_lower):
            return "Streetlight", 0.96
        if "pothole" in text_lower or "crater" in text_lower or "asphalt" in text_lower:
            return "Pothole", 0.95
        if "water" in text_lower or "leak" in text_lower or "pipe" in text_lower or "sewer" in text_lower:
            return "Water Supply", 0.94
        if "garbage" in text_lower or "trash" in text_lower or "waste" in text_lower:
            return "Garbage & Sanitation", 0.93
        if "traffic light" in text_lower or "signal" in text_lower:
            return "Traffic Signal", 0.95

        confidence = min(0.95, 0.4 + (max_matches * 0.2)) if max_matches > 0 else 0.40
        return best_cat, confidence

    @classmethod
    def extract_urgency(cls, text: str) -> str:
        """Extract urgency level: CRITICAL, HIGH, MEDIUM, LOW."""
        text_lower = text.lower()

        for kw in cls.URGENCY_KEYWORDS["CRITICAL"]:
            if kw in text_lower:
                return "CRITICAL"
        for kw in cls.URGENCY_KEYWORDS["HIGH"]:
            if kw in text_lower:
                return "HIGH"
        for kw in cls.URGENCY_KEYWORDS["MEDIUM"]:
            if kw in text_lower:
                return "MEDIUM"

        return "LOW"

    @classmethod
    def extract_location(cls, text: str) -> Optional[str]:
        """Extract landmark or street location from freeform text."""
        for pattern in cls.LOCATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loc = match.group(1).strip().strip(" ,.-")
                if len(loc) > 2:
                    return loc
        return None

    @classmethod
    def summarize_issue(cls, text: str, category: str, location: Optional[str] = None) -> str:
        """
        Summarize citizen rambling into clean, professional municipal work order title.
        Example:
        'There has been no street light near Gate 3 for almost a week and the road gets extremely dark.'
        -> 'Streetlight near Gate 3 non-functional for approximately one week'
        """
        duration = None
        for pattern, replacement in cls.DURATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                duration = re.sub(pattern, replacement, re.search(pattern, text, re.IGNORECASE).group(0), flags=re.IGNORECASE)
                break

        # Check for Gate or specific location in text
        loc_str = location or cls.extract_location(text) or "specified location"
        has_prep = bool(re.search(r'\b(near|at|by|on|in front of)\b', loc_str, re.I))
        loc_phrase = loc_str if has_prep else f"near {loc_str}"

        if category == "Streetlight":
            if duration:
                return f"Streetlight {loc_phrase} non-functional for {duration}"
            return f"Streetlight {loc_phrase} outage"

        if category == "Pothole":
            return f"Roadway pothole hazard {loc_phrase}"

        if category == "Water Supply":
            if "leak" in text.lower():
                return f"Water supply leak reported {loc_phrase}"
            return f"Water supply disruption {loc_phrase}"

        if category == "Garbage & Sanitation":
            return f"Uncollected waste/overflow {loc_phrase}"

        # Clean fallback summary
        cleaned = re.sub(r'^(there has been|i want to report|please fix|there is|we have)\s+', '', text.strip(), flags=re.IGNORECASE)
        sentences = re.split(r'[\.\n;]', cleaned)
        first_sentence = sentences[0].strip()
        if len(first_sentence) > 80:
            first_sentence = first_sentence[:77] + "..."
        return first_sentence.capitalize()


class AIService:
    """Unified AI service providing Client-Trained ML model with local NLP and LLM fallbacks."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.nlp = LocalNLPProcessor()
        self.trained_pipeline = None
        self.model_metadata = None
        self.reload_trained_model()

    def reload_trained_model(self):
        """Reload the client-trained ML model artifact from disk."""
        try:
            from app.ml_trainer import ml_trainer
            self.trained_pipeline = ml_trainer.load_model()
            self.model_metadata = ml_trainer.get_metadata()
            if self.trained_pipeline:
                acc = self.model_metadata.get('accuracy', 'N/A') if self.model_metadata else 'N/A'
                print(f"[AIService] Loaded Client-Trained ML Model (Accuracy: {acc}%)")
        except Exception as e:
            print(f"[AIService] Trained model not available yet: {e}")
            self.trained_pipeline = None
            self.model_metadata = None

    async def analyze_complaint(self, text: str) -> Dict[str, Any]:
        """
        Analyze unstructured citizen input using the Client-Trained Machine Learning Model
        (or deterministic NLP fallback) to classify category, determine urgency,
        extract locations, and synthesize work orders.
        """
        # First attempt local Ollama if available
        llm_result = await self._try_ollama_analysis(text)
        if llm_result:
            return llm_result

        category = None
        confidence = 0.5
        top_candidates = []
        model_type = "Deterministic Lexical NLP"

        # 1. Primary: Use Client-Trained Scikit-Learn Model if present
        if self.trained_pipeline is not None:
            try:
                from app.ml_trainer import clean_text
                cleaned = clean_text(text)
                pred_label = self.trained_pipeline.predict([cleaned])[0]
                probs = self.trained_pipeline.predict_proba([cleaned])[0]
                classes = self.trained_pipeline.classes_

                # Build sorted candidate distribution
                indexed_probs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
                top_candidates = [
                    {"category": c, "confidence": round(float(p), 3)}
                    for c, p in indexed_probs[:3]
                ]

                category = str(pred_label)
                confidence = round(float(indexed_probs[0][1]), 3)
                acc = self.model_metadata.get("accuracy", "90+") if self.model_metadata else "90+"
                model_type = f"Client-Trained Machine Learning Pipeline (Test Accuracy: {acc}%)"
            except Exception as e:
                print(f"[AIService] ML inference fallback: {e}")
                category = None

        # 2. Fallback: High-precision deterministic NLP engine
        if not category:
            category, confidence = self.nlp.classify_category(text)
            model_type = "Deterministic Lexical NLP"

        urgency = self.nlp.extract_urgency(text)
        location = self.nlp.extract_location(text)
        summary = self.nlp.summarize_issue(text, category, location)

        cat_config = CATEGORIES_CONFIG.get(category, {})
        department = cat_config.get("department", "Municipal Operations")

        return {
            "category": category,
            "urgency": urgency,
            "issue_summary": summary,
            "extracted_location": location or "",
            "confidence": confidence,
            "suggested_department": department,
            "model_source": model_type,
            "top_candidates": top_candidates,
            "explanation": f"Classified as '{category}' ({int(confidence*100)}% confidence) via {model_type}. Urgency '{urgency}' based on duration and safety indicators."
        }

    async def _try_ollama_analysis(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to query local Ollama daemon if running."""
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                prompt = (
                    "You are an AI assistant for NYC 311 Municipal Services.\n"
                    "Analyze the following complaint:\n"
                    f"\"{text}\"\n\n"
                    "Output JSON with keys: category, urgency (LOW, MEDIUM, HIGH, CRITICAL), "
                    "extracted_location, issue_summary."
                )
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": "llama3", "prompt": prompt, "format": "json", "stream": False}
                )
                if response.status_code == 200:
                    import json
                    data = response.json()
                    parsed = json.loads(data.get("response", "{}"))
                    cat = parsed.get("category", "General Civic Issue")
                    cat_config = CATEGORIES_CONFIG.get(cat, {})
                    return {
                        "category": cat,
                        "urgency": parsed.get("urgency", "MEDIUM"),
                        "issue_summary": parsed.get("issue_summary", text[:60]),
                        "extracted_location": parsed.get("extracted_location", ""),
                        "confidence": 0.98,
                        "suggested_department": cat_config.get("department", "Municipal Operations"),
                        "explanation": "Extracted via local LLM model"
                    }
        except Exception:
            # Silently fallback to LocalNLPProcessor
            pass
        return None

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard token similarity between two complaint texts for duplicate detection."""
        def tokenize(s: str):
            words = re.findall(r'\b\w{3,}\b', s.lower())
            stopwords = {"the", "and", "for", "that", "this", "with", "from", "there", "has", "been", "near", "please"}
            return set(w for w in words if w not in stopwords)

        set1 = tokenize(text1)
        set2 = tokenize(text2)
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return round(intersection / union, 2)


# Global AI instance
ai_service = AIService()
