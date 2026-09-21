# Game: Catch Blue 

## 1. Overview

Catch Blue is inspired by the MCAT review game of the same name by John Wetzel on Premedvillage. In the game, the player answers multiple-choice course content questions in an attempt to catch "Blue", a dog who has escaped. As the player answers questions correctly, they get closer to Blue, while incorrect answers allow Blue to get farther away. 

The current project serves as a method to learn game development in Python, as well as build a fun and engaging resource for students learning Anatomy & Physiology, Organic Chemistry, and other courses. 

## 2. Core Gameplay

### Catch Blue
The player starts in the corner of the grid (usually 5 x 5--see Systems), and Blue starts in the middle. The player may select an orthogonally adjacent topic square to answer a question. Upon clicking, they are presented with a multiple-choice question selected from the topic displayed on the square; answering it, right or wrong, reduces the move counter by one. If they answer correctly, the Player moves to the square they clicked on, and Blue does not move. If they answer incorrectly, Blue moves and the Player does not. The game ends when the Player clicks on Blue and answers the final question correctly, or when the Player runs out of moves.

Beyond simply replicating John Wetzel's game in Python, the current project will also add three new game modes: Run from Red, Race Green, and Find Yellow.

### Run from Red
In Run from Red, the roles are reversed: the Player starts in the middle, Red starts in the corner, and the goal is to run away! Red must catch the Player, by landing on the Player's square, within a certain number of turns. As in Catch Blue, the Player must answer questions to move. Correct answers move the Player forward, incorrect answers allow Red to catch up. The win condition is the reverse of Catch Blue's early loss: the Player wins once the moves left are fewer than the distance Red needs to close, so Red can no longer catch them.

### Race Green
In Race Green, the Player and Green each start at the bottom of their own vertical strip (3 wide, 9 tall by default) and race to the top. The first to reach the top wins! Movement is forward-only: every move is one row up, straight or diagonal, so a runner in the middle column has three squares to choose from and a runner on an edge has two. The Player answers a question from the square they pick; correct, they move there; incorrect, Green advances one row instead (this may change for the Medium and Hard difficulties). Because every move is progress, the Player's real decision each turn is which subtopic to answer next. The board is viewed through a camera showing five rows at a time, starting at the bottom and following the Player up, so strip height can grow with difficulty.

### Find Yellow
Find Yellow places the Player and Yellow on a procedurally generated maze. The win and loss conditions are the same as Catch Blue, but *unlike* Catch Blue, the Player cannot see Yellow from the start. The Player must find Yellow by answering questions to move through the maze. Correct answers move the Player forward, incorrect answers allow Yellow to move farther away! The maze is larger than the screen and the camera follows the Player, which is what keeps Yellow hidden at the start.

## 3. Systems & Content

### Movement and turns
- Every character moves one square at a time within the board. Catch Blue, Run from Red, and Find Yellow move orthogonally (no diagonals). Race Green moves forward-only: up, up-left, or up-right, never sideways or back.
- A turn is one answered question. Exactly one side moves per turn: correct, the Player moves onto the clicked square; incorrect, the Player stays and the NPC moves.
- **Blue** flees greedily: any adjacent free square that increases its distance from the Player, ties broken at random, holds still when cornered.
- **Red** (planned) steps toward the Player on incorrect answers only, mirroring Blue, and catches by landing on the Player's square. **Green** (planned) advances one row on incorrect answers, choosing any of its forward squares; Medium and Hard may change the trigger. **Yellow** (planned) flees like Blue, unseen until found.

### Board and squares
- Board size is a setting: 5 x 5, 7 x 7, or 9 x 9. The board is drawn in a fixed 800 px region, so the window never changes size. Race Green and Find Yellow both use boards larger than the region and need a camera that follows the Player; the region becomes a viewport onto the board. Race Green's viewport shows five rows and starts at the bottom of the strips; Find Yellow's follows the Player through the maze and is what keeps Yellow hidden at the start. Not built yet.
- Each square holds one **subtopic** for the whole game, assigned at random and balanced across the selected topics at game start.
- Questions on a square rotate with no repeats until the pool is spent. A square whose pool runs dry is relabeled to a live one; pools restart only when all are dry.
- **Catch:** clicking Blue when adjacent asks a question from Blue's square. Correct wins; incorrect, Blue flees.
- **Moves:** the move limit is a setting (10 / 15 / 20 / 30). Every answered question costs one, right or wrong. The game is lost when moves reach zero, or sooner when the moves left are fewer than the distance to Blue.

### Characters
- `Character` base class (cell, shape, color) with `Player` and `Blue` subclasses; Red, Green, and Yellow join as siblings. Start cells are set per mode.
- Colors are from the Okabe-Ito colorblind-safe palette; sprites are planned once art arrives, with shapes as the fallback.
- The pixel theme takes its accent color from the mode: blue for Catch Blue, red for Run from Red, green for Race Green, yellow for Find Yellow.

### Questions and difficulty
- Multiple choice only; choices are shuffled at ask time. Stored as JSON, one file per topic, in a subject → topic → subtopic hierarchy. The board shows subtopics; the Topics menu selects topics.
- Bank: 2,603 Anatomy & Physiology questions across 21 topics, written from the course textbook and adapted from openly licensed banks (credits in `data/questions/ATTRIBUTION.md`). Other subjects are added the same way.
- Every question is graded 1 (recall), 2 (application), or 3 (analysis).
- **Difficulty presets** set board size, move limit, and which tiers are asked: easy 5 x 5, 15 moves, tiers 1 and 2; medium 5 x 5, 15 moves, distance-scaled; hard 7 x 7, 20 moves, distance-scaled. Custom edits any row. Distance-scaled asks tier 3 next to Blue, tier 2 two squares away, and tiers 1 and 2 beyond, falling back silently when a tier is thin. Each mode defines what "distance" means: Catch Blue and Find Yellow measure Player to NPC, Run from Red measures Player to Red, and Race Green measures the Player's rows to the top, so the hardest questions come on the final rows. In the maze, distance is the corridor path, not the straight line.

## 4. UX and UI

Menus 

In-Game

Accessibility
- Colorblind modes 
- Blind / low-vision

## 5. Production

Milestones

Unknowns
- Web app vs executable file, or just leave as .py 
- Race Green: whether the move limit applies at all (a 9-tall strip is decided within 15 questions), and the exact viewport width, since two 3-wide strips plus a gap are seven columns
- Later: Multiplayer
