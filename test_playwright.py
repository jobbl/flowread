from playwright.sync_api import sync_playwright
import time

def test_app():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "http://localhost:8000/static/index.html"
        print(f"Navigating to {url}...")
        page.goto(url)
        
        # We'll just use the default text already in the textarea:
        # "In this project I want to use the attention vectors of a llm to bold the most important words in an input text to improve reading comprehension."
        
        print("Clicking the 'Analyze Text' button...")
        page.click("#analyze-btn")
        
        print("Waiting for the analysis to finish (this might take a few seconds)...")
        # Wait for the loading text to disappear and spans to appear
        page.wait_for_selector(".token", timeout=60000)
        
        # Get all tokens and their classes
        tokens = page.query_selector_all(".token")
        
        print("\n--- Results ---")
        highlighted_words = []
        full_text = []
        
        for token in tokens:
            text = token.inner_text()
            classes = token.get_attribute("class")
            
            # Format output
            if "highlighted" in classes:
                full_text.append(f"**{text}**")
                highlighted_words.append(text)
            else:
                full_text.append(text)
                
        print("Full output with bolded words (marked by **):")
        # Simple join (there might be spaces in the tokens themselves based on Gemma's tokenizer)
        print("".join(full_text))
        
        print("\nWords that crossed the attention threshold:")
        print(highlighted_words)
        
        print("\nSaving screenshot to result.png...")
        page.screenshot(path="result.png", full_page=True)
        
        browser.close()
        print("Done!")

if __name__ == "__main__":
    test_app()