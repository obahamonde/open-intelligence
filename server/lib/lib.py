from openai import AsyncOpenAI
from openai._utils._proxy import LazyProxy
from pydantic import BaseModel, Field
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.shared_params.function_definition import FunctionDefinition
from abc import ABC, abstractmethod
import typing as tp
import typing_extensions as tpe

OPENAI_BASE_URL = "https://api.indiecloud.co/v1"
OPENAI_API_KEY = "sk-YOUR-OPENAI-API-KEY-HERE"

ChatModel: tpe.TypeAlias = tp.Literal[
    "llama-3.3-70b-versatile",
    "llama-3.2-90b-vision",
    "deepseek-r1-distill-llama-70b",
]
T = tp.TypeVar("T")
P = tp.ParamSpec("P")

class Tool(BaseModel, LazyProxy[AsyncOpenAI], ABC):
    """
    An abstract base class representing a tool that can be used in chat completions.

    This class combines functionality from Pydantic's BaseModel, LazyProxy, and ABC to create
    a flexible and extensible tool structure for use with OpenAI's chat completion API.
    """
    @classmethod
    def definition(cls) -> ChatCompletionToolParam:
        """
        Generates a ChatCompletionToolParam object that defines the tool for use in chat completions.

        This method creates a function-type tool definition using the class name, docstring,
        and model schema.

        Returns:
            ChatCompletionToolParam: A parameter object describing the tool for chat completions.
        """
        return ChatCompletionToolParam(
            type="function",
            function=FunctionDefinition(
                name=cls.__name__,
                description=cls.__doc__ or "[No description]",
                parameters=cls.model_json_schema().get("properties", {}),
            ),
        )

    @abstractmethod
    async def run(
        self,
    ) -> str:
        """
        An abstract method that should be implemented by subclasses to execute the tool's functionality.

        Returns:
            str: The result of running the tool, as a string.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError()

    def __load__(self):
        """
        Initializes and returns an AsyncOpenAI client with predefined base URL and API key.

        This method is used by the LazyProxy to create the OpenAI client when needed.

        Returns:
            AsyncOpenAI: An initialized AsyncOpenAI client.
        """
        return AsyncOpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
        )

class Agent(Tool):
    """
    A class representing an AI agent capable of executing chat completions.

    This agent uses a specified language model to generate responses based on
    input messages and can execute various tools.

    Attributes:
        model (ChatModel): The language model to be used for chat completion.
            Defaults to "llama-3.3-70b-versatile".
        messages (list[ChatCompletionMessageParam]): A list of messages that form
            the conversation history for the agent. Defaults to an empty list.
        max_tokens (int): The maximum number of tokens to generate in the response.
            Defaults to 8192.
    """
    model: ChatModel = Field(default="llama-3.3-70b-versatile")
    messages: list[ChatCompletionMessageParam] = Field(default_factory=list)
    max_tokens: int = Field(default=8192)

    async def execute(self) -> tp.AsyncGenerator[str, None]:
        """#+
            Executes the chat completion process using the OpenAI API.#+
        #+
            Parameters:#+
            - model (str): The model to use for the chat completion. Default is "llama-3.3-70b-versatile".#+
            - messages (list[ChatCompletionMessageParam]): A list of messages to include in the chat. Default is an empty list.#+
            - max_tokens (int): The maximum number of tokens to generate. Default is 8192.#+
        #+
            Returns:#+
            - AsyncGenerator[str, None]: An asynchronous generator that yields the content of the chat completion.#+
        #+
            Raises:#+
            - ValueError: If no content is found or if no tool calls are found.#+
        """  # +
        client = self.__load__()
        response = await client.chat.completions.create(
            model=self.model,
            tools=[d.definition() for d in Tool.__subclasses__()],
            tool_choice="auto",
            messages=self.messages,
            temperature=0.2,
            max_tokens=self.max_tokens,
            stream=False,
        )
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            content = response.choices[0].message.content
            if content:
                yield content
            else:
                raise ValueError("No content found")
        else:
            for tool_call in tool_calls:
                for d in Tool.__subclasses__():
                    if d.__name__ == tool_call.function.name:
                        tool = d.model_validate_json(tool_call.function.arguments)
                        yield await tool.run()
                        return
            raise ValueError("No tool calls found")

    async def run(self) -> str:
        data = ""
        async for line in self.execute():
            data += line
        return data
