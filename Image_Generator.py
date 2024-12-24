import random
import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Initialize session state variables
def init_session_state():
    if 'used_words' not in st.session_state:
        st.session_state.used_words = []
    if 'current_word' not in st.session_state:
        st.session_state.current_word = None
    if 'image_url' not in st.session_state:
        st.session_state.image_url = None
    if 'options' not in st.session_state:
        st.session_state.options = []
    if 'correct_answer' not in st.session_state:
        st.session_state.correct_answer = None

# Define the vocabulary list organized by categories
VOCABULARY = {
    'Nature': [
        "Sun", "Moon", "Star", "Cloud", "Rain", "Tree", "Mountain", "River",
        "Ocean", "Flower", "Leaf", "Grass", "Sand", "Stone", "Fire"
    ],
    'Animals': [
        "Dog", "Cat", "Bird", "Fish", "Elephant", "Tiger", "Lion", "Monkey",
        "Rabbit", "Horse", "Cow", "Snake", "Frog", "Butterfly", "Ant"
    ],
    'Body Parts': [
        "Eye", "Ear", "Nose", "Mouth", "Hand", "Foot", "Hair", "Teeth",
        "Tongue", "Finger"
    ],
    'Common Objects': [
        "Chair", "Table", "Bed", "Cup", "Plate", "Spoon", "Knife", "Bottle",
        "Clock", "Pen", "Book", "Bag", "Umbrella", "Hat", "Shoes"
    ],
    'Food & Drink': [
        "Apple", "Banana", "Orange", "Bread", "Rice", "Milk", "Water",
        "Egg", "Cake", "Ice Cream"
    ],
    'People & Relationships': [
        "Man", "Woman", "Child", "Baby", "Mother", "Father",
        "Friend", "Family", "Boy", "Girl"
    ]
}

def get_new_word():
    """Select a random word that hasn't been used in the current session."""
    all_words = [word for category in VOCABULARY.values() for word in category]
    
    if len(st.session_state.used_words) >= len(all_words):
        st.session_state.used_words = []
    
    available_words = [word for word in all_words if word not in st.session_state.used_words]
    new_word = random.choice(available_words)
    st.session_state.used_words.append(new_word)
    return new_word

def generate_options(word):
    """Generate Sanskrit translation options using GPT."""
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Sanskrit teacher. Provide accurate Sanskrit translations with transliterations."},
                {
                    "role": "user", 
                    "content": f"""Generate 4 Sanskrit words with transliterations. One must be for the word '{word}'.
                    Mark the translation for '{word}' with an asterisk (*).
                    Output in this format: Sanskrit-Transliteration*"""
                }
            ],
            temperature=1.2
        )
        response = completion.choices[0].message.content
        print("First GPT call:")
        print(response)

        # Second GPT call to format into numbered options
        completion_1 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Format Sanskrit translations into numbered options."
                },
                {
                    "role": "user",
                    "content": f"""Format these Sanskrit words into 4 numbered options:
                    {response}
                    
                    Format each line as:
                    1. Sanskrit_word (Transliteration)
                    2. Sanskrit_word (Transliteration)
                    3. Sanskrit_word (Transliteration) 
                    4. Sanskrit_word (Transliteration)
                    
                    Put the correct answer (the word with the asterisk*) at the end between <ANSWER> tags.
                    Example:
                    1. पुस्तक (pustaka)
                    2. जल (jala) 
                    3. अग्नि (agni)
                    4. वृक्ष (vriksha)
                    <ANSWER>जल (jala)</ANSWER>"""
                }
            ],
            temperature=0.3
        )
        response_text = completion_1.choices[0].message.content
        print("Second GPT call:")
        print(response_text)

        # Process the formatted response to get numbered options
        options = [line.strip() for line in response_text.split('\n') if line.strip() and not line.startswith('<ANSWER>') and not line.startswith('</ANSWER>')]

        # Extract just the Sanskrit words and transliterations without numbers
        options = [opt.split('. ')[1] for opt in options if '. ' in opt]

        # Extract correct answer between <ANSWER> tags
        start_tag = '<ANSWER>'
        end_tag = '</ANSWER>'
        start_idx = response_text.find(start_tag) + len(start_tag)
        end_idx = response_text.find(end_tag)
        correct_answer = response_text[start_idx:end_idx].strip()

        random.shuffle(options)

        
        return options, correct_answer
        
    except Exception as e:
        st.error(f"Error generating options: {str(e)}")
        return ["Option 1", "Option 2", "Option 3", "Option 4"], "Option 1"

def generate_image(word):
    """Generate image using DALL-E."""
    try:
        response = client.images.generate(
            model="dall-e-2",
            prompt=f"Display a clear, simple {word}",
            size="512x512",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"Error generating image: {str(e)}")
        return None

def reset_game_state():
    """Reset the game state with new word, image, and options."""
    st.session_state.current_word = get_new_word()
    st.session_state.image_url = generate_image(st.session_state.current_word)
    st.session_state.options, st.session_state.correct_answer = generate_options(st.session_state.current_word)

def main():
    st.title("Sanskrit Learning Game")
    
    # Initialize session state
    init_session_state()
    
    # Initialize or reset game state
    if st.session_state.current_word is None:
        reset_game_state()

    # Display current word and image
    if st.session_state.image_url:
        st.image(st.session_state.image_url)
        st.write("What is this object called in Sanskrit?")

    # Handle answer selection
    if st.session_state.options:
        user_choice = st.radio("Select the correct answer:", st.session_state.options)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Answer"):
                if user_choice == st.session_state.correct_answer:
                    st.success("Correct! Well done!")
                    with st.spinner(text="Loading Next Word..."):
                        reset_game_state()            
                    with col2:
                        st.button("Next Word")      
                else:
                    st.error(f"Incorrect. The correct answer was: {st.session_state.correct_answer}")
        
        # with col2:
        #     st.button("Next Word")
            # if st.button("Next Word"):
            #     reset_game_state()
                #st.rerun()

if __name__ == "__main__":
    main()
