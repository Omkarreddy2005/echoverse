from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv
import os
import logging
import torch
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
hf_token = os.getenv("HF_TOKEN")

# Model configuration
MODEL_ID = "google/flan-t5-base"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Global variables for model and pipeline
_model = None
_tokenizer = None
_rewrite_pipeline = None

def initialize_model():
    """Initialize the model and tokenizer with proper error handling"""
    global _model, _tokenizer, _rewrite_pipeline
    
    if _rewrite_pipeline is not None:
        return _rewrite_pipeline
    
    try:
        logger.info(f"Loading model: {MODEL_ID}")
        logger.info(f"Using device: {DEVICE}")
        
        # Load tokenizer and model with updated parameter name
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID, 
            token=hf_token if hf_token else None
        )
        
        _model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_ID, 
            token=hf_token if hf_token else None,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            device_map="auto" if DEVICE == "cuda" else None
        )
        
        # Move model to device if not using device_map
        if DEVICE == "cpu":
            _model = _model.to(DEVICE)
        
        # Create pipeline
        _rewrite_pipeline = pipeline(
            "text2text-generation", 
            model=_model, 
            tokenizer=_tokenizer,
            device=0 if DEVICE == "cuda" else -1
        )
        
        logger.info("Model loaded successfully")
        return _rewrite_pipeline
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise RuntimeError(f"Model initialization failed: {str(e)}")

@lru_cache(maxsize=128)
def get_tone_prompt(tone, text_preview):
    """Generate optimized prompts for different tones with caching"""
    tone = tone.lower()
    
    tone_prompts = {
        "neutral": f"Rewrite this text clearly and objectively: {text_preview}",
        "professional": f"Rewrite this text in a professional and formal manner: {text_preview}",
        "casual": f"Rewrite this text in a casual and friendly way: {text_preview}",
        "academic": f"Rewrite this text in an academic and scholarly tone: {text_preview}",
        "creative": f"Rewrite this text in a creative and engaging style: {text_preview}",
        "formal": f"Rewrite this text using formal language and structure: {text_preview}",
        "happy": f"Rewrite this text with a positive and upbeat tone: {text_preview}",
        "sad": f"Rewrite this text with a melancholic and somber tone: {text_preview}",
        "angry": f"Rewrite this text with strong and forceful language: {text_preview}"
    }
    
    return tone_prompts.get(tone, f"Rewrite this in a {tone} tone: {text_preview}")

def validate_inputs(text, tone, creativity, max_tokens):
    """Validate input parameters"""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    if len(text.strip()) < 5:
        raise ValueError("Text is too short (minimum 5 characters)")
    
    if len(text) > 5000:
        logger.warning("Text is very long, this may take a while to process")
    
    if not 0.1 <= creativity <= 2.0:
        raise ValueError("Creativity must be between 0.1 and 2.0")
    
    if not 10 <= max_tokens <= 2048:
        raise ValueError("Max tokens must be between 10 and 2048")
    
    valid_tones = ["neutral", "professional", "casual", "academic", "creative", 
                   "formal", "happy", "sad", "angry"]
    if tone.lower() not in valid_tones:
        logger.warning(f"Unknown tone '{tone}', using 'neutral' instead")
        return "neutral"
    
    return tone.lower()

def chunk_text(text, max_chunk_size=500):
    """Split long text into manageable chunks"""
    if len(text) <= max_chunk_size:
        return [text]
    
    # Split by sentences first
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would exceed the limit, start a new chunk
        if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Single sentence is too long, split by words
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 > max_chunk_size:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = word
                        else:
                            # Single word is too long, just add it
                            chunks.append(word)
                            temp_chunk = ""
                    else:
                        temp_chunk += (" " + word) if temp_chunk else word
                
                if temp_chunk:
                    current_chunk = temp_chunk
        else:
            current_chunk += (". " + sentence) if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def rewrite_text(text, tone="Neutral", creativity=0.7, max_tokens=256):
    """
    Rewrite text with improved error handling and features
    
    Args:
        text (str): Input text to rewrite
        tone (str): Tone for rewriting (neutral, professional, casual, etc.)
        creativity (float): Temperature for generation (0.1-2.0)
        max_tokens (int): Maximum tokens to generate (10-2048)
    
    Returns:
        str: Rewritten text
    
    Raises:
        ValueError: If input parameters are invalid
        RuntimeError: If model processing fails
    """
    try:
        # Validate inputs
        tone = validate_inputs(text, tone, creativity, max_tokens)
        
        # Initialize model if needed
        pipeline_model = initialize_model()
        
        # Clean input text
        text = text.strip()
        
        # Handle long texts by chunking
        if len(text) > 500:
            logger.info("Processing long text in chunks")
            chunks = chunk_text(text, max_chunk_size=400)
            rewritten_chunks = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Create prompt for this chunk
                prompt = get_tone_prompt(tone, chunk)
                
                # Generate rewrite for chunk
                try:
                    result = pipeline_model(
                        prompt,
                        max_new_tokens=min(max_tokens // len(chunks) + 50, max_tokens),
                        temperature=creativity,
                        do_sample=True if creativity > 0.1 else False,
                        top_p=0.9,
                        repetition_penalty=1.1,
                        pad_token_id=_tokenizer.eos_token_id
                    )
                    
                    chunk_result = result[0]["generated_text"].strip()
                    rewritten_chunks.append(chunk_result)
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {str(e)}")
                    # Fallback: use original chunk
                    rewritten_chunks.append(chunk)
            
            # Combine chunks
            final_result = " ".join(rewritten_chunks)
        else:
            # Process short text normally
            prompt = get_tone_prompt(tone, text)
            
            try:
                result = pipeline_model(
                    prompt,
                    max_new_tokens=max_tokens,
                    temperature=creativity,
                    do_sample=True if creativity > 0.1 else False,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    pad_token_id=_tokenizer.eos_token_id
                )
                
                final_result = result[0]["generated_text"].strip()
                
            except Exception as e:
                logger.error(f"Error during text generation: {str(e)}")
                raise RuntimeError(f"Text generation failed: {str(e)}")
        
        # Post-process result
        final_result = post_process_text(final_result)
        
        # Validate output
        if not final_result or len(final_result.strip()) < 5:
            logger.warning("Generated text is too short, returning original")
            return text
        
        logger.info("Text rewriting completed successfully")
        return final_result
        
    except ValueError as e:
        logger.error(f"Input validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during rewriting: {str(e)}")
        raise RuntimeError(f"Rewriting failed: {str(e)}")

def post_process_text(text):
    """Clean up the generated text"""
    if not text:
        return text
    
    # Remove common artifacts
    text = text.replace("  ", " ")  # Double spaces
    text = text.replace(" .", ".")  # Space before period
    text = text.replace(" ,", ",")  # Space before comma
    text = text.replace(" !", "!")  # Space before exclamation
    text = text.replace(" ?", "?")  # Space before question mark
    
    # Ensure proper capitalization
    sentences = text.split('. ')
    cleaned_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(sentence) > 1:
            # Capitalize first letter
            sentence = sentence[0].upper() + sentence[1:]
            cleaned_sentences.append(sentence)
    
    return '. '.join(cleaned_sentences)

def get_model_info():
    """Get information about the loaded model"""
    return {
        "model_id": MODEL_ID,
        "device": DEVICE,
        "is_loaded": _rewrite_pipeline is not None,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available()
    }

# Test function
def test_rewrite():
    """Test the rewrite functionality"""
    try:
        test_text = "This is a simple test sentence to verify the rewriting functionality."
        result = rewrite_text(test_text, tone="professional", creativity=0.5, max_tokens=100)
        print(f"Test successful!\nOriginal: {test_text}\nRewritten: {result}")
        return True
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Model Info:", get_model_info())
    test_rewrite()
