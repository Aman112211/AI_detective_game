# AI Detective — How to Play

AI Detective is a single-player mystery game where the player interrogates a fictional detective, gathers clues, and finally makes a criminal accusation.

The current active mode is the pirate case: The Vanished Doubloons of the Crimson Gull. The noir mode is present in the project structure but is not fully playable yet.

## Game Overview

You are assigned to solve a theft on a pirate ship.

The captain's locked chest of 500 gold doubloons has vanished during a stormy night. Your job is to ask smart questions, uncover the right evidence, and identify the culprit before you run out of questions.

The game uses a structured detective loop:

1. Start a case
2. Read the briefing
3. Ask questions about suspects, locations, timelines, and clues
4. Watch for newly revealed evidence
5. Build a theory about who did it and how
6. Submit an accusation before your question limit is used up

## What the Player Sees

At the start screen, the player selects a game mode.

The playable current mode is:

- Pirate case: The Vanished Doubloons of the Crimson Gull

The interface includes:

- a suspect board
- a detective interrogation panel
- an evidence board
- a question counter
- a final accusation modal
- a score screen when the round ends

## Objective

Your goal is to determine:

- who stole the treasure
- how the theft was carried out
- why they did it
- which evidence supports the accusation

The investigation is won only when the accusation matches the server-side answer key.

## Game Flow

### 1. Start a new game

From the start screen, choose the pirate mode and press Open the Case.

This creates a session on the backend and returns:

- the session ID
- the case title
- the briefing
- the suspect list
- the number of remaining questions

### 2. Read the briefing

The briefing gives the background of the case and states the central mystery.

For the pirate case, the key facts are:

- the captain's chest of 500 doubloons disappeared overnight
- a storm covered the deck from midnight to 3am
- the cabin door was found locked from the outside
- the cabin porthole was unlatched
- four suspects had enough access or motive to be relevant

### 3. Ask questions

The player types a question into the interrogation box and sends it.

Good questions usually target one of these areas:

- a suspect's motive
- a suspect's alibi
- a timeline event
- a physical clue
- a location or object
- what happened during the storm

Examples of effective questions:

- Who had access to the captain's cabin?
- What does Toby do on deck?
- Did anyone leave the ship during the storm?
- Was anyone seen near the porthole?
- What evidence is tied to Toby?

The backend checks the message against the case data and unlocks evidence when the question matches a clue or structured fact.

### 4. Evidence discovery

As the player investigates, evidence items are revealed when the question matches them.

These are the main clues in the pirate case:

- wire_tool
- watch_log
- torn_cloth
- fisherman_report
- dice_witnesses
- kitchen_log
- boatswain_account

Evidence is intentionally structured so the player can piece together the truth without the answer being exposed directly.

### 5. Use the suspect board

The suspect board shows each crew member and their basic profile.

The current suspects are:

- Quartermaster Finch
- Cook Mags Halloway
- Cabin Boy Pip
- Rigger Toby Vane

Each suspect has:

- a bio
- a motive hint
- an alibi
- an initial suspicion rating

The question is not to guess randomly. It is to test which suspect's motive, access, timing, and evidence line up.

## Core Rules

### Question limit

Each case has a limited number of questions.

The pirate case starts with 15 questions.

When the counter reaches zero, the player can no longer ask investigative questions.

### Server-side authority

The backend controls:

- session creation
- question counting
- evidence discovery
- accusation validity
- scoring
- game status

The frontend only exposes the public case details and user input. The answer key remains in the backend.

### No direct answer leakage

The LLM is instructed to stay in character and not reveal the solution directly.

Instead, it responds as First Mate Salty Sable, providing clues, redirecting the player, and guiding the investigation without stating the culprit outright.

## How to Win

When the player believes they know the culprit, they click Make Accusation.

The accusation form asks for:

- culprit
- method
- motive
- supporting evidence checkboxes

The backend then scores the submission.

### Scoring system

The total score is out of 25 points.

- Identity: 10 points
- Method: 5 points
- Motive: 5 points
- Evidence: 5 points

A correct accusation can score all 25 points.

### Correct solution for the pirate case

The correct culprit is Toby Vane.

The correct method is:

- Toby picked the cabin lock during his watch shift
- used a wire tool to unlock it
- used the storm to mask the noise
- lowered the stolen chest through the porthole to a waiting rowboat

The correct motive is:

- Toby was paid by rival Captain Voss to weaken the Crimson Gull and steal the treasure

The strongest evidence is:

- wire_tool
- watch_log
- torn_cloth
- fisherman_report

## What Counts as a Good Accusation

A strong accusation includes all of the following:

- the correct suspect
- a method consistent with the evidence
- a motive that matches the case
- enough supporting evidence to back the conclusion

A wrong accusation may still earn partial credit, but it does not win the game.

## Win and Lose Conditions

### Win

The round is won when the player submits a correct accusation and the score reaches the maximum outcome.

### Lose

The round is lost when:

- the accusation is incorrect
- the current evidence does not support the conclusion
- the player runs out of questions before solving the case

## Tips for Playing

- Start with the suspects with the strongest motive and access.
- Ask about the timeline and who had access to the cabin.
- Pay attention to the exact wording of evidence descriptions.
- The right answer is usually built from several clues together, not one single fact.
- Do not accuse too early; the game rewards evidence-based reasoning.
- The storm, porthole, and watch shift are key operational clues.

## Current Known Status

At the time of writing:

- Pirate mode is the active, fully playable case.
- Noir mode is included as a future path but is not yet the complete game state.
- The project is structured so the backend remains the truth source for the mystery and scoring.

## Local Setup

### Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python backend\app.py
```

The backend listens on:

- http://127.0.0.1:5000

### Frontend

From the frontend folder:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs in Vite and points to the Flask backend through the local proxy.

### Environment variables

Create a `.env` file at the project root with the LLM settings for local testing:

```env
FLASK_ENV=development
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false

LLM_API_KEY=your-groq-or-openai-key
LLM_MODEL=openai/gpt-oss-20b
LLM_API_URL=https://api.groq.com/openai/v1/chat/completions
```

Note: `.env` should never be committed to version control.

## Deployment Notes

The app is designed to separate the frontend and backend:

- Frontend can be hosted on Vercel
- Backend can be hosted on Render or another Python hosting service
- The frontend reads the live backend URL from `VITE_API_URL`

This keeps the secret answer key and LLM token off the browser and out of the public client code.

## Quick Summary

AI Detective is a deduction game about solving a theft using limited questions, discovered evidence, and a final accusation.

The play loop is:

- start case
- investigate suspects and clues
- gather evidence
- accuse the right culprit
- win by matching the hidden truth

If you read the briefing, ask smart questions, and track the evidence, the culprit becomes clear.
