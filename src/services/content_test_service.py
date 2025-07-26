# src/services/content_test_service.py
from src.utils.logger import setup_logger

class ContentTestService:
    """
    Handles testing of creative content (ads, emails, etc.) against simulated audiences.
    """
    def __init__(self, audience_service, persona_service):
        """
        Initializes the ContentTestService.

        Args:
            audience_service: Service for sampling audiences.
            persona_service: Service for getting persona responses.
        """
        self.audience_service = audience_service
        self.persona_service = persona_service
        # Default application logger instance
        self.app_logger = setup_logger()
        self.app_logger.info("ContentTestService initialized.")

    def test_content(self, audience_id: str, content: dict, sample_size: int = 15):
        """
        Tests a piece of content against a specified audience.

        Args:
            audience_id (str): The ID of the audience to test against.
            content (dict): The content to be tested, e.g., {'type': 'ad', 'text': '...', 'image_data': '...'}.
            sample_size (int): The number of personas to sample for the test.

        Returns:
            dict: A dictionary containing analytics and feedback from the test.
        """
        self.app_logger.info(f"Testing content of type '{content.get('type')}' against audience {audience_id}.")

        # 1. Get a sample of personas from the audience
        personas = self.audience_service.sample_personas_from_audience(audience_id, count=sample_size)
        
        all_feedback = []
        # 2. For each persona, get their detailed feedback on the content
        for persona in personas:
            # persona_id = persona.get('id')
            # stimulus = {"type": "content_test", **content}
            # feedback = self.persona_service.get_persona_response_to_stimulus(persona_id, stimulus)
            
            # Placeholder logic
            feedback = {
                "sentiment": "positive",
                "clarity_score": 8,
                "recommendations": "Make the call-to-action more prominent.",
                "summary": "The persona found the ad visually appealing but the text was a bit long."
            }
            all_feedback.append(feedback)

        # 3. Aggregate the feedback into a comprehensive analysis
        analysis = self._analyze_feedback(all_feedback)
        
        return analysis

    def _analyze_feedback(self, all_feedback: list) -> dict:
        """
        Aggregates individual persona feedback into a final report.
        """
        if not all_feedback:
            return {"error": "No feedback to analyze."}

        # Placeholder analysis logic
        import numpy as np
        from collections import Counter

        sentiments = [f['sentiment'] for f in all_feedback]
        clarity_scores = [f['clarity_score'] for f in all_feedback]

        sentiment_counts = Counter(sentiments)
        
        analysis_summary = {
            "total_responses": len(all_feedback),
            "overall_sentiment": sentiment_counts.most_common(1)[0][0] if sentiment_counts else "N/A",
            "sentiment_breakdown": dict(sentiment_counts),
            "average_clarity_score": np.mean(clarity_scores),
            "key_recommendations": [f['recommendations'] for f in all_feedback if f['recommendations']][:3],
            "common_themes": [
                "Visuals are strong",
                "Text could be more concise",
                "Call-to-action needs emphasis"
            ] # This would be derived from NLP in a real implementation
        }
        
        return analysis_summary 