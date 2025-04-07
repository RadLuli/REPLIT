import random
import datetime
from translation import translate_to_portuguese

# Set of photography tip topics for variety
PHOTOGRAPHY_TIP_TOPICS = [
    "composition",
    "lighting",
    "portrait photography",
    "landscape photography",
    "street photography",
    "macro photography",
    "night photography",
    "wildlife photography",
    "architectural photography",
    "black and white photography",
    "golden hour photography",
    "rule of thirds",
    "depth of field",
    "exposure",
    "camera settings",
    "focus techniques",
    "post-processing",
    "color theory",
    "storytelling",
    "flash photography"
]

# Example tips for fallback when LLM isn't available
FALLBACK_TIPS = [
    "Use leading lines to guide the viewer's eye through the image.",
    "For portrait photography, focus on the eyes to create engaging connection.",
    "When shooting landscapes, use a small aperture (f/11-f/16) for greater depth of field.",
    "Use the golden hour (just after sunrise or before sunset) for warm, flattering light.",
    "Apply the rule of thirds by placing key elements at the intersections of grid lines.",
    "For sharp handheld photos, use a shutter speed of at least 1/focal length.",
    "Use a polarizing filter to reduce reflections and enhance sky colors.",
    "Experiment with different perspectives to create more interesting compositions.",
    "Remember that shadows can be as important as highlights in creating dimension.",
    "Clean your lens regularly for the sharpest possible images.",
    "Learn to use your camera's histogram to avoid blown highlights.",
    "For wildlife photography, patience is often more important than equipment.",
    "Use continuous shooting mode to capture fast-moving subjects.",
    "Consider negative space to create more impactful compositions.",
    "Use exposure compensation when shooting in challenging lighting conditions.",
    "Shoot in RAW format for maximum flexibility in post-processing.",
    "Try black and white conversion to emphasize texture and form.",
    "Use a tripod for night photography to allow longer exposures.",
    "Practice with manual focus for more control in difficult situations.",
    "Experiment with intentional camera movement for creative abstract effects."
]


def generate_tip_prompt(topic=None):
    """
    Generate a prompt for the LLM to create a photography tip of the day
    
    Args:
        topic: Optional specific photography topic
    
    Returns:
        str: Prompt for the LLM
    """
    if topic is None:
        topic = random.choice(PHOTOGRAPHY_TIP_TOPICS)
    
    return f"""Generate a helpful photography tip of the day about {topic}.
    The tip should be concise (maximum 150 words), practical, and valuable for photography students.
    Include one specific technique or suggestion that can be immediately applied.
    Format the tip with a clear title and a brief explanation of the technique and its benefits.
    """


def get_tip_of_the_day(model, force_refresh=False):
    """
    Get the photography tip of the day
    
    Args:
        model: The LLM model to use for generating the tip
        force_refresh: Whether to force a new tip even if one was generated today
    
    Returns:
        dict: Contains tip title, content, and topic
    """
    # Use date as seed for consistent daily tip
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Use today's date to seed the random generator for consistent topic selection
    random.seed(today)
    
    # Select a topic based on the date
    topic = random.choice(PHOTOGRAPHY_TIP_TOPICS)
    
    # Generate prompt for the LLM
    prompt = generate_tip_prompt(topic)
    
    try:
        # Generate tip using the LLM
        tip_text = model.invoke(prompt)
        
        # Parse the tip text to extract title and content
        lines = tip_text.strip().split('\n')
        
        if len(lines) > 1:
            title = lines[0].strip().replace('# ', '').replace('#', '')
            content = '\n'.join(lines[1:]).strip()
        else:
            # Fallback if formatting is unexpected
            title = f"Dica sobre {topic}"
            content = tip_text.strip()
        
        # Translate to Portuguese
        portuguese_title = translate_to_portuguese(title)
        portuguese_content = translate_to_portuguese(content)
        
        return {
            "title": portuguese_title,
            "content": portuguese_content,
            "topic": topic,
            "date": today
        }
    
    except Exception as e:
        # Fallback to predefined tips if LLM fails
        fallback_tip = random.choice(FALLBACK_TIPS)
        
        # Translate the fallback tip
        portuguese_tip = translate_to_portuguese(fallback_tip)
        
        return {
            "title": translate_to_portuguese(f"Dica de {topic}"),
            "content": portuguese_tip,
            "topic": topic,
            "date": today,
            "fallback": True
        }


def get_tip_by_topic(model, specific_topic):
    """
    Get a photography tip for a specific topic
    
    Args:
        model: The LLM model to use for generating the tip
        specific_topic: The specific photography topic to generate a tip for
    
    Returns:
        dict: Contains tip title, content, and topic
    """
    # Generate prompt for the LLM
    prompt = generate_tip_prompt(specific_topic)
    
    try:
        # Generate tip using the LLM
        tip_text = model.invoke(prompt)
        
        # Parse the tip text to extract title and content
        lines = tip_text.strip().split('\n')
        
        if len(lines) > 1:
            title = lines[0].strip().replace('# ', '').replace('#', '')
            content = '\n'.join(lines[1:]).strip()
        else:
            # Fallback if formatting is unexpected
            title = f"Dica sobre {specific_topic}"
            content = tip_text.strip()
        
        # Translate to Portuguese
        portuguese_title = translate_to_portuguese(title)
        portuguese_content = translate_to_portuguese(content)
        
        return {
            "title": portuguese_title,
            "content": portuguese_content,
            "topic": specific_topic,
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
    
    except Exception as e:
        # Find the most relevant fallback tip for the topic
        # This is a simple approach - in a real system, you might use embeddings to find the most relevant tip
        fallback_tip = FALLBACK_TIPS[hash(specific_topic) % len(FALLBACK_TIPS)]
        
        # Translate the fallback tip
        portuguese_tip = translate_to_portuguese(fallback_tip)
        
        return {
            "title": translate_to_portuguese(f"Dica de {specific_topic}"),
            "content": portuguese_tip,
            "topic": specific_topic,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "fallback": True
        }