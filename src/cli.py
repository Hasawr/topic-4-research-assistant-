import argparse
import logging
import sys
import asyncio

# Import your core engine components
#  Correct import path (looks for researcher.py in your root directory)
try:
    from dotenv import load_dotenv
    # This finds the .env file in the root folder relative to where you run the command
    load_dotenv()
except ImportError:
    pass
from src.core.researcher import ResearchAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 1000
def validate_question(question: str) -> str:
    """Validates the input question string."""
    cleaned = question.strip() if question else ""

    if not cleaned:
        logger.error("Validation Error: Question cannot be empty.")
        sys.exit(1)
    if len(cleaned) > MAX_QUESTION_LENGTH:
        logger.error(f"Validation Error: Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters.")
        sys.exit(1)

    return cleaned



def handle_ask(args):
    """Handles the execution of the 'ask' command by running the async engine."""
    question = validate_question(args.question)

    logger.info(f"Processing question: '{question}'")
    if args.no_cache:
        logger.info("Cache bypass flag (--no-cache) detected.")
    if args.sources:
        logger.info(f"Source filtering requested for: {args.sources}")

    logger.info("Initializing Research Assistant engine...")
    assistant = ResearchAssistant()

    logger.info("Handing off control to the Async Orchestration layer...")
    try:
        # Run the async core research task
        result = asyncio.run(assistant.conduct_research(question))

        # --- PRETTY PRINTING LOGIC ---
        print("\n" + "=" * 60)
        print("                 AI RESEARCH ASSISTANT REPORT                  ")
        print("=" * 60)
        print(f"QUESTION: {question}\n")
        print("-" * 60)
        print("SUMMARY ANSWER:")
        print("-" * 60)

        # If the result is a string but structured like an object, or a real object:
        if hasattr(result, 'answer'):
            print(result.answer)
            display_citations(getattr(result, 'citations', []))
        elif isinstance(result, dict) and 'answer' in result:
            print(result['answer'])
            display_citations(result.get('citations', []))
        else:
            # If it's just a raw text fallback
            print(result)

        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"An unexpected error occurred during execution: {e}")
        sys.exit(1)

def display_citations(citations):
    """Helper function to format and print references beautifully."""
    if not citations:
        return

    print("\n" + "-" * 60)
    print("SOURCES & CITATIONS:")
    print("-" * 60)

    for c in citations:
        # Handle both object attributes and dict keys seamlessly
        idx = getattr(c, 'index', '?') if not isinstance(c, dict) else c.get('index', '?')
        source = getattr(c, 'source', None) if not isinstance(c, dict) else c.get('source', {})

        if source:
            title = getattr(source, 'title', 'Unknown Title') if not isinstance(source, dict) else source.get('title',
                                                                                                              'Unknown Title')
            url = getattr(source, 'url', '') if not isinstance(source, dict) else source.get('url', '')
            origin = getattr(source, 'origin', 'web') if not isinstance(source, dict) else source.get('origin', 'web')

            print(f"[{idx}] ({origin.upper()}) {title}")
            if url:
                print(f"    URL: {url}")

def main():
    parser = argparse.ArgumentParser(description="AI Researcher CLI Platform")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Define the 'ask' sub-command
    ask_parser = subparsers.add_parser("ask", help="Ask the AI researcher a question")
    ask_parser.add_argument("question", type=str, help="The research question enclosed in quotes")
    ask_parser.add_argument("--no-cache", action="store_true", help="Bypass the local cache layer")
    ask_parser.add_argument("--sources", type=str, help="Filter specific research sources (comma-separated)")

    args = parser.parse_args()
    if args.command == "ask":
        handle_ask(args)


if __name__ == "__main__":
    main()