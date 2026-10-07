import json
from copy import deepcopy
from types import SimpleNamespace

import httpx
import pytest
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from study_agent.agent import AgentLimitError, StudyAgent
from study_agent.config import Settings


def call(name, arguments="{}", call_id="call_1"):
    return {
        "type": "function",
        "id": call_id,
        "function": {"name": name, "arguments": arguments},
    }


def response(*items, text="", status="completed"):
    message = ChatCompletionMessage(
        role="assistant", content=text or None, tool_calls=list(items) or None
    )
    finish = "length" if status != "completed" else ("tool_calls" if items else "stop")
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=finish)])


class ScriptedClient:
    def __init__(self, responses):
        self.chat = self
        self.completions = self
        self.queue = iter(responses)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(deepcopy(kwargs))
        return next(self.queue)


def test_agent_uses_observations_and_creates_real_quiz(tools, quiz):
    client = ScriptedClient(
        [
            response(call("get_scores")),
            response(call("search_notes", '{"query":"loops"}', "call_2")),
            response(call("create_quiz", quiz.model_dump_json(), "call_3")),
            response(text="Your quiz is ready."),
        ]
    )
    trace = []
    agent = StudyAgent(Settings(), tools, trace.append, client)
    assert agent.run("Help me practise loops") == "Your quiz is ready."
    assert trace == ["get_scores", "search_notes", "create_quiz"]
    observations = [item for item in client.requests[-1]["messages"] if item.get("role") == "tool"]
    assert json.loads(observations[0]["content"])["completed_quizzes"] == 0
    assert "loops.md" in observations[1]["content"]
    assert len(tools.store.pending_quizzes()) == 1
    assert tools.store.get_scores()["completed_quizzes"] == 0


def test_bad_tool_arguments_return_feedback_and_allow_recovery(tools):
    client = ScriptedClient(
        [
            response(call("search_notes", "not-json")),
            response(call("search_notes", '{"query":"loops"}', "call_2")),
            response(text="A loop repeats a block."),
        ]
    )
    agent = StudyAgent(Settings(), tools, client=client)
    assert "loop" in agent.run("Explain loops")
    assert "error" in json.loads(client.requests[1]["messages"][-1]["content"])


def test_agent_stops_instead_of_looping_forever(tools):
    client = ScriptedClient([response(call("get_scores")) for _ in range(2)])
    agent = StudyAgent(Settings(), tools, client=client, max_rounds=2)
    with pytest.raises(AgentLimitError, match="2-request limit"):
        agent.run("Plan practice")
    assert len(client.requests) == 2
    assert agent.history == []


def test_incomplete_model_output_does_not_execute_partial_actions(tools, quiz):
    client = ScriptedClient(
        [response(call("create_quiz", quiz.model_dump_json()), status="incomplete")]
    )
    with pytest.raises(RuntimeError, match="incomplete"):
        StudyAgent(Settings(), tools, client=client).run("Quiz me")
    assert tools.store.pending_quizzes() == []


def test_empty_answer_fails_clearly(tools):
    client = ScriptedClient([response()])
    with pytest.raises(RuntimeError, match="no answer"):
        StudyAgent(Settings(), tools, client=client).run("Hello")


def test_chat_keeps_only_three_complete_turns(tools):
    client = ScriptedClient([response(text="Hello") for _ in range(5)])
    agent = StudyAgent(Settings(), tools, client=client)
    for i in range(5):
        agent.run(f"Request {i}")
    assert len(agent.history) == 3
    prompts = [
        item["content"]
        for item in client.requests[-1]["messages"]
        if isinstance(item, dict) and item.get("role") == "user"
    ]
    assert prompts == ["Request 1", "Request 2", "Request 3", "Request 4"]


@pytest.mark.parametrize(
    "base_url",
    [
        "https://api.groq.com/openai/v1",
        "https://api.openai.com/v1",
        "https://custom.example/v1",
        "https://api.deepseek.com",
    ],
)
def test_actual_sdk_sends_tool_loop_to_configured_endpoint(tools, monkeypatch, base_url):
    requests = []
    deepseek = base_url == "https://api.deepseek.com"
    model = "deepseek-flash" if deepseek else "openai/gpt-oss-120b"

    def handler(request):
        assert str(request.url) == base_url + "/chat/completions"
        assert request.headers["authorization"] == "Bearer test-not-a-real-key"
        payload = json.loads(request.content)
        requests.append(payload)
        first = len(requests) == 1
        message = {"role": "assistant", "content": None if first else "Start with loops."}
        if first:
            message["tool_calls"] = [call("get_scores")]
        return httpx.Response(
            200,
            json={
                "id": f"chatcmpl_{len(requests)}",
                "object": "chat.completion",
                "created": 0,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": "tool_calls" if first else "stop",
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(
            "study_agent.agent.OpenAI", lambda **kwargs: OpenAI(http_client=http, **kwargs)
        )
        agent = StudyAgent(
            Settings(api_key="test-not-a-real-key", base_url=base_url, model=model), tools
        )
        assert agent.run("Suggest practice") == "Start with loops."
    assert requests[0]["model"] == model
    for request in requests:
        if deepseek:
            assert request["max_tokens"] == 2400
            assert request["thinking"] == {"type": "disabled"}
            assert "max_completion_tokens" not in request
            assert "parallel_tool_calls" not in request
        else:
            assert request["parallel_tool_calls"] is False
            assert request["max_completion_tokens"] == 2400
            assert "thinking" not in request
    assert "input" not in requests[0]
    assert "store" not in requests[0]
    assert requests[0]["tools"][0]["function"]["name"] == "get_scores"
    assert requests[1]["messages"][-1]["tool_call_id"] == "call_1"
    assert json.loads(requests[1]["messages"][-1]["content"])["completed_quizzes"] == 0
