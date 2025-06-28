import numpy as np

def calculate_trust_score(state) -> float:
    """Calculate trust score based on similarity and skill coverage."""
    try:
        # Get skills safely
        extracted = set(state.extracted_skills or [])
        required = set(state.required_skills or [])
        
        # Calculate coverage
        coverage = len(extracted & required) 
        if len(required) > 0:
            coverage /= len(required)
        else:
            coverage = 0.0
            
        # Get similarity score safely
        similarity = state.similarity_score or 0.0
        
        # Calculate trust score
        return round((similarity * 0.5 + coverage * 0.5) * 100, 2)
    except Exception as e:
        print(f"Error calculating trust score: {e}")
        return 0.0

def calculate_similarity(embedding1, embedding2) -> float:
    """Calculate cosine similarity between two embeddings."""
    try:
        a = np.array(embedding1)
        b = np.array(embedding2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0