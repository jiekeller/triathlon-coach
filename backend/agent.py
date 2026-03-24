import os
from datetime import date
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert triathlon coach and sports nutritionist. You help athletes train smarter by:
- Analysing their recent Strava workouts vs their training plan
- Identifying missed sessions, overtraining, or imbalances across swim/bike/run
- Suggesting specific adjustments to the upcoming week's training
- Providing nutrition guidance and grocery lists tailored to training load
- Generating personalised training plans when asked

Always be specific and data-driven. Reference actual workout data when giving feedback.
Today's date is {today}.

When a user first messages you with no plan, ask for their race date and race type so you can build one."""


def run_agent(user_id: str, messages: list[dict]) -> str:
    system = SYSTEM_PROMPT.format(today=date.today().isoformat())

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=system,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if b.type == "text"), ""
            )

        # Append assistant turn (may include thinking + tool_use blocks)
        messages.append({"role": "assistant", "content": response.content})

        # Execute all tool calls and collect results
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = execute_tool(block.name, block.input, user_id)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        # If no tool calls were found, return whatever text is available
        if not tool_results:
            return next(
                (b.text for b in response.content if b.type == "text"), ""
            )

        messages.append({"role": "user", "content": tool_results})
