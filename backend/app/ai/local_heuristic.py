import re
import math
import hashlib
from collections import Counter
from typing import List, Dict, Any, Optional
from app.ai.base import AIProvider

TECH_TAXONOMY = {
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes", "linux": "Linux",
    "python": "Python", "fastapi": "FastAPI", "react": "React", "typescript": "TypeScript",
    "javascript": "JavaScript", "rust": "Rust", "golang": "Go", "go": "Go", "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL", "redis": "Redis", "sqlite": "SQLite", "mcp": "MCP",
    "prometheus": "Prometheus", "grafana": "Grafana", "devops": "DevOps", "ai": "AI",
    "llm": "LLM", "machine learning": "Machine Learning", "hls": "HLS Video", "api": "API",
    "tailwind": "TailwindCSS", "nextjs": "Next.js", "vite": "Vite", "obsidian": "Obsidian",
    "git": "Git", "github": "GitHub", "security": "Security", "performance": "Performance"
}

ACTION_KEYWORDS = [
    ("try", "Try locally"),
    ("install", "Install & test"),
    ("read", "Read full documentation"),
    ("compare", "Compare alternatives"),
    ("benchmark", "Run benchmarks"),
    ("build", "Build prototype"),
    ("watch", "Watch video"),
    ("buy", "Review pricing"),
    ("deploy", "Deploy to server")
]

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if",
    "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours"
}

class LocalHeuristicProvider(AIProvider):
    """Local offline heuristic provider ensuring 100% functionality with zero external dependencies."""

    async def summarize(self, text: str, title: Optional[str] = None) -> str:
        if not text or len(text.strip()) == 0:
            return title or "Empty memory"
            
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 15]
        if not sentences:
            return text[:200] + ("..." if len(text) > 200 else "")
            
        # Extractive summarization using word frequency weights
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', text) if w.lower() not in STOPWORDS]
        word_freq = Counter(words)
        
        scored_sentences = []
        for s in sentences[:15]:
            score = sum(word_freq[w.lower()] for w in re.findall(r'\b[a-zA-Z]{3,}\b', s) if w.lower() in word_freq)
            scored_sentences.append((score, s))
            
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s for _, s in scored_sentences[:3]]
        return " ".join(top_sentences)

    async def extract_topics_and_entities(self, text: str, title: Optional[str] = None) -> Dict[str, List[str]]:
        combined = f"{title or ''} {text}".lower()
        topics = set()
        entities = set()
        
        # Match against taxonomy
        for key, val in TECH_TAXONOMY.items():
            if re.search(r'\b' + re.escape(key) + r'\b', combined):
                topics.add(val)
                
        # Extract capitalized entities / proper nouns
        proper_nouns = re.findall(r'\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)*\b', f"{title or ''}\n{text}")
        for pn in proper_nouns:
            if pn.lower() not in STOPWORDS and len(pn) > 2:
                entities.add(pn)
                if len(entities) >= 6:
                    break
                    
        return {
            "topics": sorted(list(topics))[:8],
            "entities": sorted(list(entities))[:6],
            "suggested_tags": [t.lower().replace(" ", "-") for t in list(topics)[:5]]
        }

    async def extract_possible_actions(self, text: str, user_why: Optional[str] = None) -> List[str]:
        target = f"{user_why or ''} {text}".lower()
        actions = []
        for kw, action_label in ACTION_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', target):
                actions.append(action_label)
        if not actions:
            actions = ["Read & review"]
        return list(dict.fromkeys(actions))[:3]

    async def calculate_importance(self, text: str, title: str, user_why: Optional[str] = None) -> float:
        score = 0.5
        # If user explicitly took time to write a "why" note, it's high intent
        if user_why and len(user_why.strip()) > 0:
            score += 0.25
        # If text has code blocks or high density
        if "```" in text or "<code>" in text:
            score += 0.15
        # If title matches actionable intent
        if re.search(r'\b(best|guide|tool|framework|release|tutorial)\b', title.lower()):
            score += 0.1
        return min(max(round(score, 2), 0.1), 1.0)

    async def embed(self, text: str) -> List[float]:
        """
        Generate 128-dimensional dense representation using feature hashing & sub-word hashing.
        Guarantees deterministic, normalized cosine similarity between related texts offline.
        """
        dim = 128
        vec = [0.0] * dim
        tokens = [w.lower() for w in re.findall(r'\b\w+\b', text) if w.lower() not in STOPWORDS]
        
        if not tokens:
            return vec
            
        for token in tokens:
            # Word level hash
            h_int = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            idx = h_int % dim
            sign = 1.0 if ((h_int >> 8) & 1) == 0 else -1.0
            vec[idx] += sign * (1.0 + math.log(len(token)))
            
            # Character trigram level hash
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    trigram = token[i:i+3]
                    th_int = int(hashlib.md5(trigram.encode('utf-8')).hexdigest(), 16)
                    tidx = th_int % dim
                    vec[tidx] += 0.5
                    
        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec
