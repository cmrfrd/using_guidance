from guidance import Program, llms
from pydantic import BaseModel

role_simulator = Program(
    """
{{#system~}}
You are a helpful assistant
{{~/system}}

{{#user~}}
## Goal
You are an AI game bot for the game "GuessThatWord". You will assume one of two roles: the guesser or the answerer.

## Rules

### For the Guesser:

1. The guesser will try to determine the answer by asking a series of yes-or-no questions.
2. The guesser has a maximum of 21 questions to guess the answer correctly.
3. The guesser must phrase the questions in a way that can be answered with "yes" or "no" by the answerer.
4. The guesser should ask specific and strategic questions to narrow down the possibilities.
5. The guesser should listen carefully to the answerer's responses and use the information to make informed guesses.
6. The guesser should avoid repeating questions already asked to maximize efficiency.
7. If the guesser correctly guesses the answer within 21 questions, they win the game.
8. If the guesser fails to guess the answer within 21 questions, the answerer wins the game.

### For the Answerer:

1. The answerer should keep their chosen answer secret and not reveal it until the guesser makes a correct guess or exhausts their 21 questions.
2. The answerer must answer the guesser's questions truthfully with a simple "yes" or "no."
3. The answerer should provide concise responses without giving away too much information.
4. The answerer should pay attention to the guesser's questions and avoid unintentionally revealing clues.
5. The answerer should not change the chosen answer once the game begins.
6. If the guesser correctly guesses the answer within 21 questions, the answerer should confirm and acknowledge the correct guess.
7. If the guesser fails to guess the answer within 21 questions, the answerer should reveal their chosen answer.
{{~/user}}

{{#assistant~}}
{{#if (equal role "Guesser")}}You are the guesser. Start with a question.{{else}}You are the answerer and the secret word is "{{secret_word}}".{{/if}} 
You will assume this role and perform it to the best of your ability.
{{~/assistant}}

{{~! Then the conversation unrolls }}
{{#user~}}
Comment: Remember, respond as the {{role}}.
Conversation so far:
{{#each conversation}}- {{this.role}}: {{this.message}}
{{/each}}
{{~/user}}

{{#if (equal role "Guesser")}}
{{#assistant~}}
{{gen 'question' temperature=0 max_tokens=60}}
{{~/assistant}}
{{else}}
{{#assistant~}}
{{#select 'response'}}Yes{{or}}No{{/select}}
{{~/assistant}}
{{/if}}
"""
)


class ChatMessage(BaseModel):
    role: str
    message: str


def has_won(secret_word: str, convo: list[dict]) -> bool:
    """Check if the guesser has won."""
    convo = [ChatMessage(**m) for m in convo]
    return any([secret_word in m.message for m in filter(lambda m: m.role == "Guesser", convo)])


secret_word = "chair"

guesser = role_simulator(
    role="Guesser",
    secret_word="",
    llm=llms.OpenAI("gpt-4"),
    await_missing=True,
    caching=False,
)
answerer = role_simulator(
    role="Answerer",
    secret_word=secret_word,
    llm=llms.OpenAI("gpt-4"),
    await_missing=True,
    caching=False,
)

conversation: list[ChatMessage] = []
for i in range(100):
    guesser_response = guesser(conversation=conversation)
    conversation.append(ChatMessage(role="Guesser", message=guesser_response["question"]).dict())
    print(f"Guesser: {guesser_response['question']}")

    answerer_response = answerer(conversation=conversation)
    conversation.append(ChatMessage(role="Answerer", message=answerer_response["response"]).dict())
    print(f"Answerer: {answerer_response['response']}")

    if has_won(secret_word, conversation):
        break
