# Game: Catch Blue 

## 1. Overview

This game takes heavy inspiration from Premedvillage's Catch Blue, a game in which the player answers MCAT questions in an attempt to catch "Blue", a dog who has escaped. As the player answers questions correctly, they get closer to Blue, while incorrect answers allow Blue to get farther away. 

The aim of the current project is to expand the game in both content and mechanics. 

## 2. Core Gameplay

The core gameplay loop is similar to that in Premedvillage. The player and Blue start on opposite ends of a 5 x 5 grid, and the player selects an adjacent topic square. Upon clicking, a flashcard- or fill-in-the-blank-style question pops up. Blue does not move if the player answers correctly. The game ends when the player clicks on Blue (they must be adjacent).

- Note: there may be a loss condition which occurs when the player runs out of moves, set in the game settings.

The major contribution of this project beyond academic content is the addition of a new game mode, "Run from Red", of which there are two variants:

**Escape mode**: In escape mode, the game is limited to a certain number of turns.
- Win condition: Player gets to the edge of the 9 x 9 map.
- Lose condition: Player is caught by Red.

**Marathon mode**: In Marathon mode, the question difficulty is adaptive
- End condition: The player does not increase question difficulty for a predetermined number of turns. Score is calculated as average difficulty of questions answered.
- Lose condition: Player is caught by Red.

## 3. Systems (rules)

Movement

Object interactions
- Players and NPC (Blue/Red)
- Players and game grid

## 4. Content

Game grids 
- 5 x 5 for Catch Blue
- 9 x 9 (may be larger or smaller) for Run from Red: Escape mode
- "Unlimited" / procedural generation for Run from Red: Marathon Mode

Characters / Classes
- Player class 
- NPC class
  - *Currently* planning for Blue and Red to be subclasses of NPC. 

Academic content / question sourcing
- Textbook, questions I've created 
- Will need to determine how to set "difficulty" levels

## 5. UX and UI

Menus 

In-Game

Accessibility
- Colorblind modes 
- Blind / low-vision

# 6. Production

Milestones

Unknowns
- Web app vs executable file, or just leave as .py 
- Timeframe, may need to reduce scope if >40 hours required
  - Start with Catch Blue, only add Run from Red if under 30 hours 
