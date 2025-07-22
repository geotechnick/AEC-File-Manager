"""
Local LLM Integration for AEC File Manager
Supports multiple local LLM backends including llama-cpp, Ollama, and transformers
"""

import os
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LocalLLMManager:
    """Manages local LLM integration with fallback options"""
    
    def __init__(self):
        self.llm = None
        self.llm_type = os.getenv('LLM_MODEL_TYPE', 'auto')
        self.use_local_llm = os.getenv('USE_LOCAL_LLM', 'true').lower() == 'true'
        self.model_path = os.getenv('LLM_MODEL_PATH', './models/llama-2-7b.ggml')
        self.context_size = int(os.getenv('LLM_CONTEXT_SIZE', '2048'))
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '512'))
        
        self.initialize_llm()
    
    def initialize_llm(self):
        """Initialize the appropriate LLM backend"""
        if not self.use_local_llm:
            logger.info("Local LLM disabled, using fallback text processing")
            return
        
        try:
            if self.llm_type == 'ollama' or os.getenv('OLLAMA_BASE_URL'):
                self._init_ollama()
            elif self.llm_type == 'llama-cpp' or self.model_path.endswith(('.ggml', '.gguf')):
                self._init_llama_cpp()
            elif self.llm_type == 'transformers':
                self._init_transformers()
            else:
                # Auto-detect based on available libraries
                self._auto_init()
                
        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}. Falling back to text processing.")
            self.llm = None
    
    def _init_ollama(self):
        """Initialize Ollama client"""
        try:
            import ollama
            self.llm_backend = 'ollama'
            self.ollama_client = ollama.Client(
                host=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            )
            self.model_name = os.getenv('OLLAMA_MODEL', 'llama2')
            logger.info(f"Initialized Ollama with model: {self.model_name}")
        except ImportError:
            raise Exception("Ollama library not installed. Install with: pip install ollama")
    
    def _init_llama_cpp(self):
        """Initialize llama-cpp-python"""
        try:
            from llama_cpp import Llama
            
            if not os.path.exists(self.model_path):
                raise Exception(f"Model file not found: {self.model_path}")
            
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.context_size,
                verbose=False
            )
            self.llm_backend = 'llama-cpp'
            logger.info(f"Initialized llama-cpp with model: {self.model_path}")
            
        except ImportError:
            raise Exception("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
    
    def _init_transformers(self):
        """Initialize Transformers with local model"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            import torch
            
            model_name = os.getenv('TRANSFORMERS_MODEL', 'microsoft/DialoGPT-medium')
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            self.llm = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=self.max_tokens,
                device=0 if torch.cuda.is_available() else -1
            )
            
            self.llm_backend = 'transformers'
            logger.info(f"Initialized Transformers with model: {model_name}")
            
        except ImportError:
            raise Exception("Transformers not installed. Install with: pip install transformers torch")
    
    def _auto_init(self):
        """Auto-detect and initialize available LLM backend"""
        backends_to_try = [
            ('ollama', self._init_ollama),
            ('llama-cpp', self._init_llama_cpp),
            ('transformers', self._init_transformers)
        ]
        
        for backend_name, init_func in backends_to_try:
            try:
                init_func()
                logger.info(f"Successfully initialized {backend_name}")
                return
            except Exception as e:
                logger.debug(f"Failed to initialize {backend_name}: {e}")
                continue
        
        raise Exception("No compatible LLM backend found")
    
    def generate_response(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate response using the initialized LLM"""
        if self.llm is None:
            return self._fallback_response(prompt)
        
        max_tokens = max_tokens or self.max_tokens
        
        try:
            if self.llm_backend == 'ollama':
                response = self.ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        'num_predict': max_tokens,
                        'temperature': 0.7
                    }
                )
                return response['response']
                
            elif self.llm_backend == 'llama-cpp':
                output = self.llm(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    stop=["Human:", "\n\n"]
                )
                return output['choices'][0]['text'].strip()
                
            elif self.llm_backend == 'transformers':
                response = self.llm(prompt, max_length=len(prompt.split()) + max_tokens)
                return response[0]['generated_text'][len(prompt):].strip()
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback text processing when LLM is not available"""
        prompt_lower = prompt.lower()
        
        # Simple pattern matching for AEC-specific queries
        if "change order" in prompt_lower:
            return "I would help you find change orders, but local LLM is not available. Please check the 01_CORRESPONDENCE/Change_Orders folder."
        elif "structural" in prompt_lower and "calc" in prompt_lower:
            return "I would help you find structural calculations, but local LLM is not available. Please check the 04_CALCULATIONS/Structural folder."
        elif "rfi" in prompt_lower:
            return "I would help you find RFI documents, but local LLM is not available. Please check the 01_CORRESPONDENCE/RFIs folder."
        elif "qc" in prompt_lower or "quality" in prompt_lower:
            return "I would help you with QC information, but local LLM is not available. Please use the QC Dashboard in the UI."
        else:
            return f"Local LLM is not available. Your query '{prompt}' could not be processed with AI assistance. Please use the file browser or specific search functions."
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for semantic search (requires sentence-transformers)"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use a lightweight model for embeddings
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            return embeddings.tolist()
            
        except ImportError:
            logger.warning("sentence-transformers not available. Embeddings disabled.")
            return []
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return []
    
    def semantic_search(self, query: str, document_embeddings: List[List[float]], 
                       documents: List[str], top_k: int = 5) -> List[Dict]:
        """Perform semantic search using embeddings"""
        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Get query embedding
            query_embedding = self.create_embeddings([query])
            if not query_embedding:
                return []
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, document_embeddings)[0]
            
            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    results.append({
                        "document": documents[idx],
                        "similarity": float(similarities[idx]),
                        "index": int(idx)
                    })
            
            return results
            
        except ImportError:
            logger.warning("scikit-learn not available. Semantic search disabled.")
            return []
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []


class AECDocumentProcessor:
    """Processes AEC documents with LLM enhancement"""
    
    def __init__(self, llm_manager: LocalLLMManager):
        self.llm_manager = llm_manager
    
    def summarize_document(self, file_path: str, content: str = None) -> str:
        """Generate a summary of an AEC document"""
        if content is None:
            content = self._extract_text(file_path)
        
        if not content:
            return "Could not extract content for summarization"
        
        # Truncate content to fit context window
        max_content_length = self.llm_manager.context_size - 200
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        prompt = f"""
Please provide a concise summary of this AEC document:

Document: {os.path.basename(file_path)}
Content: {content}

Summary (focus on key technical details, requirements, and decisions):
"""
        
        return self.llm_manager.generate_response(prompt, max_tokens=200)
    
    def classify_document_type(self, file_path: str, content: str = None) -> Dict[str, str]:
        """Classify AEC document type using LLM"""
        if content is None:
            content = self._extract_text(file_path)
        
        filename = os.path.basename(file_path)
        
        prompt = f"""
Classify this AEC document based on its filename and content:

Filename: {filename}
Content preview: {content[:500] if content else "No content available"}

Classify into one of these categories:
- Drawing (plans, elevations, sections, details)
- Specification (technical specifications, standards)
- Calculation (structural, MEP, energy calculations)
- Correspondence (RFIs, submittals, emails, letters)
- Report (geotechnical, survey, testing, inspection)
- Permit (building permits, approvals, zoning)
- Contract (agreements, change orders, proposals)
- Model (BIM files, 3D models)

Classification:"""
        
        response = self.llm_manager.generate_response(prompt, max_tokens=50)
        
        # Parse response to extract classification
        classification = response.strip().lower()
        
        category_mapping = {
            "drawing": "02_DRAWINGS",
            "specification": "03_SPECIFICATIONS", 
            "calculation": "04_CALCULATIONS",
            "correspondence": "01_CORRESPONDENCE",
            "report": "05_REPORTS",
            "permit": "06_PERMITS",
            "contract": "00_PROJECT_MANAGEMENT",
            "model": "08_MODELS"
        }
        
        for key, folder in category_mapping.items():
            if key in classification:
                return {"category": key, "suggested_folder": folder, "confidence": "high"}
        
        return {"category": "unknown", "suggested_folder": "10_ARCHIVE", "confidence": "low"}
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text content from various file types"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pdf':
                return self._extract_pdf_text(file_path)
            elif ext == '.docx':
                return self._extract_docx_text(file_path)
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            return text
            
        except ImportError:
            logger.warning("PyPDF2 not available. PDF text extraction disabled.")
            return ""
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
            
        except ImportError:
            logger.warning("python-docx not available. DOCX text extraction disabled.")
            return ""
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""


# Example usage and testing
if __name__ == "__main__":
    # Initialize LLM manager
    llm_manager = LocalLLMManager()
    
    # Test basic functionality
    test_query = "What are the latest change orders in this project?"
    response = llm_manager.generate_response(test_query)
    print(f"Query: {test_query}")
    print(f"Response: {response}")
    
    # Test document processor
    doc_processor = AECDocumentProcessor(llm_manager)
    
    # Example document classification
    test_filename = "PROJ123_S_001_R2_2024-01-15.pdf"
    classification = doc_processor.classify_document_type(test_filename)
    print(f"\nDocument: {test_filename}")
    print(f"Classification: {classification}")