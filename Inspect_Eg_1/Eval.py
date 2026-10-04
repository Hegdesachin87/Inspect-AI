import os
from inspect_ai import Task, task, eval
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, chain_of_thought
from inspect_ai.scorer import match

# Configure your DeepSeek API credentials
os.environ["OPENAI_API_KEY"] = "sk-7f4df226fb82451caea4eee23a982ff6"
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com"

@task
def deepseek_evaluation_task():
    """
    An Inspect AI evaluation task testing technical knowledge and reasoning
    using the DeepSeek API.
    """
    return Task(
        # 1. Dataset: The test questions and correct answers (Target)
        dataset=[
            Sample(
                input="What data structure is optimized for high-dimensional vector similarity search in RAG systems?",
                target="vector database"
            ),
            Sample(
                input="Which Python library is widely used for building agentic multi-node workflows using graphs?",
                target="LangGraph"
            ),
            Sample(
                input="What is the capital of France?",
                target="Paris"
            ),
        ],
        
        # 2. Solver: Instructions on how the AI should think and answer
        solver=[
            chain_of_thought(),  # Encourages the model to reason step by step before answering
            generate()           # Calls the AI model to generate the response
        ],
        
        # 3. Scorer: Automatically grades if the AI's output contains the target answer
        scorer=match(ignore_case=True)
    )

if __name__ == "__main__":
    # Run the evaluation task using DeepSeek's chat model
    eval(
        tasks=deepseek_evaluation_task(),
        model="openai/deepseek-chat"
    )