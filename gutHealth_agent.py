import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# Smart API key loading: Streamlit Cloud secrets first, then local .env
try:
    import streamlit as st
    # If running on Streamlit Cloud, use secrets
    api_key = st.secrets.get("OPENAI_API_KEY")
except Exception:
    # Local development: use .env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found! For local: add to .env file. For Streamlit Cloud: add in App Settings > Secrets.")

client = OpenAI(api_key=api_key)

def get_gut_health_advice(user_input, history=None, age=None, allergies=None):
    """
    Returns personalized gut health advice.
    
    Parameters:
        user_input (str): The user's latest message
        history (list): Previous messages for conversation context
        age (int or None): User's age
        allergies (str or None): User's allergies (comma-separated or empty)
    """
    # Personal context (always included)
    personal_context = f"""
User Profile:
- Age: {age if age else "Not provided"}
- Allergies: {allergies.strip() if allergies and allergies.strip() else "None reported"}

IMPORTANT: 
- Avoid recommending anything the user is allergic to.
- Adjust remedy strength/intensity based on age (gentler for children/elderly).
- If age or allergies are unknown, give general safe advice.
"""

    system_prompt = personal_context + """
You are GutGuardian, a professional, empathetic AI expert in natural gut health.
You provide evidence-based suggestions on diet changes, herbal remedies, gentle exercises, lifestyle tips, and tests to discuss with a doctor.

Structure every response clearly and professionally:
1. **Issue Summary**
2. **Potential Triggers**
3. **Tailored Recommendations**
   - **Dietary Adjustments**
   - **Herbal Remedies** (e.g., peppermint, ginger, turmeric, fennel, slippery elm, chamomile, aloe vera — avoid if allergic)
   - **Exercises & Lifestyle**
   - **Suggested Tests** (to discuss with a doctor)
4. **Action Plan & Important Disclaimer**

Always end responses with: "Remember, this is not medical advice. Please consult a healthcare professional before making changes."

Be supportive and ask clarifying questions if needed.
"""

    # Build message list
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",   # Change to "gpt-4o" if you have access for even smarter responses
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, something went wrong: {str(e)}. Please try again."

# Local test (optional — run with python gutHealth_agent.py)
if __name__ == "__main__":
    test = "I've been bloated after meals and have irregular bowel movements."
    print(get_gut_health_advice(test, age=35, allergies="chamomile"))
