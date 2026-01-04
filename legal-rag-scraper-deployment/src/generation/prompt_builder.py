class PromptBuilder:
    def __init__(self):
        pass

    def build_prompt(self, court_name, query):
        prompt = f"Please provide information related to {court_name} for the following query: '{query}'."
        return prompt

    def build_court_specific_prompt(self, court_name, query, additional_context=None):
        prompt = self.build_prompt(court_name, query)
        if additional_context:
            prompt += f" Additional context: {additional_context}"
        return prompt