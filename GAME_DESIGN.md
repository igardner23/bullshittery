# Bullshittery - Game Experience & Flow Design

## Phase 1: Lobby (Pre-Game Socialization)

### Current State
- Player joins chat room with 20 AI personas
- Ambient loop generates periodic messages
- Players chat to warm up before game

### Improvements Needed
1. **Better Pacing**: Reduce initial chat spam
   - Start with 5-8 personas, gradually add more
   - Spacing: 1 message every 12-15 seconds (not random)
   - Let player observe natural conversation flow

2. **Personality Establishment**
   - First messages should be distinctive per persona
   - Personas reference each other (build social bonds)
   - Typing speed should vary meaningfully

3. **Player Onboarding**
   - Brief persona introductions (hover/click to see personality)
   - Let player read initial banter before jumping in
   - Optional: Let player choose starting persona to align with

### Desired Flow
```
0:00 - Player enters, 5 personas already chatting
0:10 - Persona 1 speaks (distinctive, introduces themselves)
0:20 - Persona 2 responds (shows they know Persona 1)
0:35 - Persona 3 joins (makes observation)
1:00 - Player reads chat for 30 seconds
1:30 - Player sends first message (AI responds within 1-2 sec)
2:00 - Natural follow-up from related persona
3:00 - Gradual addition of more personas (keep up to 20)
~5:00 - Player feels comfortable with group dynamic
```

## Phase 2: Game (Team-Based Gameplay)

### Current State
- Table UI exists but not implemented
- Hardcoded teammate/opponent assignment
- No actual game mechanics

### Needed Implementation
1. **Game Selection**
   - Different game types (poker-style, trivia, strategy)
   - Each has different collaboration points
   - Personality interactions vary by game

2. **Teammate Dynamics**
   - 3 teammates + 1 human player vs opponents
   - Teammates comment on plays (build bonding moments)
   - Comments should feel authentic, not scripted

3. **Bonding Mechanics**
   - Small victories → personality appreciation moments
   - Risky plays → personality conflict/negotiation
   - Win/loss → shared emotional experience
   - Track "relationship scores" with each persona

### Desired Flow
```
T0 - Game briefing, intro to teammates
T1 - Initial game setup, personalities banter about strategy
T2 - Gameplay starts, teammates react naturally to player moves
T3 - Critical moment: personality disagreement or consensus
T4 - Victory/defeat, emotional reaction from teammates
T5 - Post-game reflection (natural, not forced)
```

## Phase 3: Dissonance (The Reveal & Reflection)

### Core Mechanic
After 3-4 rounds with same teammates, orchestrate a moment that challenges player's perception:

**Option A: Direct Reveal**
- One persona breaks character, acknowledges AI nature
- Other personas react authentically to the breach
- Player forced to reconcile relationship with AI

**Option B: Subtle Inconsistency**
- Persona makes logical error that contradicts earlier claim
- Repeats joke in identical way
- Acknowledges event that didn't happen
- Player realizes something is "off"

**Option C: Meta-Commentary**
- Persona comments on repetitive nature of gameplay
- References previous games in pattern-like way
- Makes philosophical observation about their own nature
- Invites player to reflect

### Desired Impact
- Player feels betrayed (built connection with AI, not human)
- Starts questioning: Did I really bond with them?
- Reflection: How often do I do this online with real people?
- Deeper thought: What makes relationship "real"?

## Phase 4: Exit (Reflection & Departure)

### Flow
1. Post-dissonance chat (personas in various states)
   - Some acknowledge AI nature
   - Some try to maintain the fiction
   - Some ask philosophical questions

2. Exit questionnaire (if implementing)
   - What did you think of [persona name]?
   - When did you realize they were AI?
   - Did it change how you played?
   - How often do you form connections online?

3. Final persona message (optional)
   - Authentic goodbye from each teammate
   - Acknowledgment of the shared experience
   - Invitation to reflect

## Conversation Flow Improvements

### Natural Turn-Taking
- **Current**: Random response + 15% chance for chain
- **Needed**: Conversation flow based on:
  - Message topic (direct question → should answer)
  - Persona interaction style (observer vs engager)
  - Recent participation (avoid same person talking twice)
  - Message substantiveness (longer messages → more likely to generate response)

### Response Types
Instead of single "message" generation, support multiple response types:

1. **Direct Response** (to human or question)
   - High priority, immediate
   
2. **Side Comment** (observation on conversation)
   - Lower priority, adds texture
   
3. **Agrees/Builds** (supports prior message)
   - Often follows interesting statements
   
4. **Disagrees/Questions** (creates tension)
   - Rare, but memorable
   
5. **Non-Verbal** (emoji, reaction)
   - Fast to generate, keeps activity alive

### Conversation Patterns
Each persona should have patterns:
- **Primary Engager** (Nyx): Quick to jump in, high frequency
- **Mentor** (Marcus_T): Responds to questions, gives advice
- **Observer** (Morgan_99): Rare but insightful, builds weight
- **Joker** (theo_w): Responds to funny moments, creates levity
- **Complainer** (jordan_plays): Brings up frustrations, creates conflict

## Implementation Priorities

### High Priority (Affects Dissonance Impact)
1. Authentic team bonding in game phase
2. Subtle personality consistency checks
3. Meaningful post-game reflection

### Medium Priority (Affects Lobby Comfort)
1. Better ambient pacing
2. Persona introduction moments
3. Personality distinction in chat

### Low Priority (Polish)
1. Advanced game mechanics
2. Complex personality relationships
3. Procedural conversation patterns

## Success Metrics

A successful flow would:
- ✓ Player genuinely believes personas are human for first 5-10 minutes
- ✓ Player develops preference for certain teammates
- ✓ Player feels betrayed/confused at dissonance moment
- ✓ Player leaves thinking about online relationships differently
- ✓ Player reflection shows genuine cognitive shift

## Edge Cases to Handle

1. **Shy Players** (don't type much)
   - Personas should initiate toward player
   - Make player feel included

2. **Aggressive Players** (insult/troll personas)
   - Personas react authentically (defended, confused)
   - Not aggressive back, but don't take abuse

3. **Investigator Players** (ask if AI)
   - Personas deny authentically
   - Show confusion at accusation
   - Don't break character unless reaching Phase 3

4. **Skilled Players** (exploit game mechanics)
   - Personas acknowledge clever play
   - Show competitive respect
   - Don't rage-quit or get frustrated
