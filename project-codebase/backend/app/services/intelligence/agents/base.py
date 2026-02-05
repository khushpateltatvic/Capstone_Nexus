"""
Base Agent with Hybrid Model Dispatch (Groq + Gemini)
"""

import logging
import json
import re
import asyncio
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# Langchain Imports
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models.chat_models import BaseChatModel

# Handle optional Google import
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logging.warning("langchain_google_genai not installed. Gemini models will be unavailable.")

from app.core.config import settings

# --- Configuration & Data Structures ---

@dataclass
class ModelConfig:
    name: str # API Model Name
    provider: str # 'groq' or 'google'
    tpm_limit: int # Tokens Per Minute Limit
    rpm_limit: int # Requests Per Minute Limit
    daily_req_limit: Optional[int] = None # None = Unlimited
    alias: str = "custom"

# 1. Groq Tier (Token Limited, RPD Free) - Sorted by Capacity ASC
# "Measure Twice, Cut Once": We check input size against these limits strictly.
GROQ_MODELS = [
    # Intelligent but restricted
    ModelConfig("meta-llama/llama-4-maverick-17b-128e-instruct", "groq", 6000, 30, None, "Maverick 6k"),
    # Balanced
    ModelConfig("moonshotai/kimi-k2-instruct", "groq", 10000, 60, None, "Kimi 10k"),
    ModelConfig("moonshotai/kimi-k2-instruct-0905", "groq", 10000, 60, None, "Kimi-0905 10k"),
    # High Capacity
    ModelConfig("meta-llama/llama-4-scout-17b-16e-instruct", "groq", 30000, 30, None, "Scout 30k"),
]

# 2. Gemini Tier (Strict 20 RPD) - Emergency / Massive Context Only
GEMINI_MODELS = [
    ModelConfig("gemini-2.5-flash-lite", "google", 1000000, 15, 20, "Gemini 2.5 Lite"),
    ModelConfig("gemini-2.5-flash", "google", 1000000, 15, 20, "Gemini 2.5 Flash"),
    ModelConfig("gemini-3-flash", "google", 1000000, 15, 20, "Gemini 3 Flash"),
]

MODEL_REGISTRY = GROQ_MODELS + GEMINI_MODELS

# --- Persistence Layer ---

class UsageStats:
    """Tracks daily request counts for Gemini models to enforce 20 RPD."""
    FILE_PATH = Path("data/usage_stats.json")

    def __init__(self):
        self.stats = {}
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self._load()

    def _load(self):
        if self.FILE_PATH.exists():
            try:
                with open(self.FILE_PATH, "r") as f:
                    data = json.load(f)
                    
                    # Reset if new day
                    if data.get("date") != self.current_date:
                        self.stats = {}
                        self.save()
                    else:
                        self.stats = data.get("counts", {})
            except Exception as e:
                logging.error(f"Failed to load usage stats: {e}")
                self.stats = {}
        else:
            # Ensure directory exists
            self.FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    def save(self):
        try:
            with open(self.FILE_PATH, "w") as f:
                json.dump({
                    "date": self.current_date,
                    "counts": self.stats
                }, f)
        except Exception as e:
            logging.error(f"Failed to save usage stats: {e}")

    def get_count(self, model_name: str) -> int:
        return self.stats.get(model_name, 0)

    def increment(self, model_name: str):
        self.stats[model_name] = self.stats.get(model_name, 0) + 1
        self.save()

# Global Usage Tracker
USAGE_TRACKER = UsageStats()


def repair_json(malformed_json: str) -> Dict[str, Any]:
    """Attempts to repair common JSON issues from LLM outputs."""
    if not malformed_json: return {}
    text = "".join(char for char in malformed_json if char.isprintable() or char in "\n\r\t")
    
    try: return json.loads(text)
    except: pass
    
    try:
        text = re.sub(r"([{,]\s*)'([^']+)':", r'\1"\2":', text)
        text = re.sub(r":\s*'([^']*)'([\s,}\]])", r': "\1"\2', text)
        text = re.sub(r',\s*([}\]])', r'\1', text)
        open_b, close_b = text.count('{'), text.count('}')
        if open_b > close_b: text += '}' * (open_b - close_b)
        open_s, close_s = text.count('['), text.count(']')
        if open_s > close_s: text += ']' * (open_s - close_s)
        return json.loads(text)
    except: pass
    
    try:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            candidate = match.group(1)
            candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
            return json.loads(candidate)
    except: pass
    return {}


class RateLimiter:
    """Simple Token Bucket for Rate Limiting (RPM & TPM)."""
    def __init__(self, rpm_limit=30, tpm_limit=6000):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.requests = []
        self.tokens = []
    
    async def wait_for_slot(self, estimated_tokens=1000):
        now = time.time()
        # Clean up old data
        self.requests = [t for t in self.requests if now - t < 60]
        self.tokens = [(t, ts) for t, ts in self.tokens if now - ts < 60]
        
        # Check RPM
        while len(self.requests) >= self.rpm_limit:
            wait_time = 60 - (now - self.requests[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.time()
            self.requests = [t for t in self.requests if now - t < 60]

        # Check TPM
        current_tokens = sum(t for t, ts in self.tokens)
        while current_tokens + estimated_tokens > self.tpm_limit:
            if not self.tokens: break
            wait_time = 60 - (now - self.tokens[0][1])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.time()
            self.tokens = [(t, ts) for t, ts in self.tokens if now - ts < 60]
            current_tokens = sum(t for t, ts in self.tokens)

        self.requests.append(now)
        self.tokens.append((estimated_tokens, now))

    def has_capacity(self, estimated_tokens: int) -> bool:
        """Check if the bucket has immediate capacity for these tokens."""
        now = time.time()
        # Peek at current state without mutating
        current_tokens = sum(t for t, ts in self.tokens if now - ts < 60)
        return (current_tokens + estimated_tokens) <= self.tpm_limit

# Global limiters - One per Groq Model
MODEL_LIMITERS = {
    m.name: RateLimiter(rpm_limit=m.rpm_limit, tpm_limit=m.tpm_limit) 
    for m in GROQ_MODELS
}


class BaseAgent:
    """
    Smart Dispatch Agent that routes requests based on size and daily quotas.
    """
    MAX_RETRIES = 3 
    RETRY_DELAY_BASE = 2.0
    
    def __init__(self, name: str):
        self.name = name
        
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing via Settings.")
        
        self.parser = JsonOutputParser()

    def _get_llm_instance(self, config: ModelConfig) -> BaseChatModel:
        """Instantiate the correct LangChain model based on provider."""
        if config.provider == "groq":
            return ChatGroq(
                temperature=0.1,
                model_name=config.name,
                groq_api_key=settings.GROQ_API_KEY,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
        elif config.provider == "google":
            if not GOOGLE_AVAILABLE:
                raise ImportError("Google Generative AI library not found.")
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is missing.")
            
            return ChatGoogleGenerativeAI(
                model=config.name,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1,
                convert_system_message_to_human=True 
            )
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    def select_model(self, input_chars: int) -> ModelConfig:
        """
        Smart Router Logic:
        1. Est Tokens = Chars / 4
        2. Try Groq (Fit First): Use smallest model where Limit > Tokens * 1.2
        3. Try Gemini (Daily Quota): If too big for Groq, use Gemini if Daily < 20
        """
        est_tokens = input_chars // 4
        
        
        # 1. Groq Search (Token Limited + Live Capacity Check)
        # We try to fit into the smallest model that HAS CAPACITY right now.
        for model in GROQ_MODELS:
            # Static check: Does it fit max context?
            safe_limit = model.tpm_limit / 1.2
            if est_tokens < safe_limit:
                # Dynamic check: Is it currently overloaded?
                limiter = MODEL_LIMITERS.get(model.name)
                if limiter and limiter.has_capacity(est_tokens):
                     logging.info(f"[{self.name}] Selected {model.alias} (Available Capacity)")
                     return model
        
        # 2. If all preferred Groq models are busy, try strict fallback to larger Groq models
        # (ignoring "smallest fit" rule to prioritize throughput)
        for model in GROQ_MODELS:
             if est_tokens < model.tpm_limit:
                 limiter = MODEL_LIMITERS.get(model.name)
                 if limiter and limiter.has_capacity(est_tokens):
                     logging.info(f"[{self.name}] Spillover to {model.alias} (Capacity Found)")
                     return model

        # 3. Gemini Fallback (Daily Req Limited)
        for model in GEMINI_MODELS:
            usage = USAGE_TRACKER.get_count(model.name)
            if usage < (model.daily_req_limit or 20):
                logging.info(f"[{self.name}] Switching to Gemini ({model.alias}). Usage: {usage}/20")
                return model
                
        # 4. Last Resort: Largest Groq Model (Wait in line)
        logging.warning(f"[{self.name}] CRITICAL: System saturated. Forcing wait on Compound.")
        return GROQ_MODELS[-1]

    async def call_llm(
        self, 
        prompt_template: ChatPromptTemplate, 
        inputs: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        
        # 1. Calculate Size & Select Model
        total_chars = sum(len(str(v)) for v in inputs.values() if isinstance(v, str))
        selected_config = self.select_model(total_chars)
        
        logging.info(f"[{self.name}] Routing {total_chars} chars (~{total_chars//4} toks) to {selected_config.alias}")

        # 2. Initialize LLM
        try:
            llm = self._get_llm_instance(selected_config)
        except Exception as e:
            logging.error(f"[{self.name}] Failed to init {selected_config.name}: {e}")
            return {}

        # 3. Rate Limit Wait (Only for Groq)
        if selected_config.provider == "groq":
            limiter = MODEL_LIMITERS.get(selected_config.name)
            if limiter:
                await limiter.wait_for_slot(estimated_tokens=total_chars//4)

        try:
            chain = prompt_template | llm | self.parser
            result = await chain.ainvoke(inputs)
            
            # Record Usage if Gemini
            if selected_config.provider == "google":
                USAGE_TRACKER.increment(selected_config.name)
            
            if not isinstance(result, dict):
                return {}
            return result
            
        except Exception as e:
            error_str = str(e)
            
            # Handle Quota/Rate Errors
            if "429" in error_str or "quota" in error_str.lower():
                logging.warning(f"[{self.name}] Rate Limit on {selected_config.alias}. Retrying...")
                await asyncio.sleep(5 * (retry_count + 1))
            
            # JSON Repair
            if "json" in error_str.lower():
                 # ... (Simple repair attempt could go here if text is accessible)
                 pass

            # Retry with DIFFERENT model if possible (Rotation)
            if retry_count < self.MAX_RETRIES:
                 # Force a larger model or just retry
                 await asyncio.sleep(self.RETRY_DELAY_BASE * (2 ** retry_count))
                 return await self.call_llm(prompt_template, inputs, retry_count + 1)
            
            logging.error(f"[{self.name}] Final Failure: {e}")
            return {}

    async def call_llm_with_fallback(self, template, inputs, fallback_data=None):
        res = await self.call_llm(template, inputs)
        return res if res else (fallback_data or {})
