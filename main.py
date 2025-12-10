import argparse
import random
import subprocess
import os
import datetime
import json
import traceback
import threading
from typing import Optional, Tuple
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# ===== CONFIGURATION =====
CONFIG = {
    "LOG_FILE": "error_log.txt",
    "SAVE_FILE": "adventure.txt",
    "DEFAULT_MODEL": "gpt-4.1-mini",
    "REQUEST_TIMEOUT": 120,
    "MAX_CONVERSATION_LENGTH": 10000
}

@dataclass
class GameState:
    conversation: str = ""
    last_ai_reply: str = ""
    last_player_input: str = ""
    current_model: str = CONFIG["DEFAULT_MODEL"]
    character_name: str = "Alex"
    selected_genre: str = "Fantasy"
    selected_role: str = "Adventurer"
    adventure_started: bool = False

# ===== GAME DATA =====
ROLE_STARTERS = {
    "Fantasy": {
        "Peasant": "You're working in the fields of a small village when",
        "Noble": "You're waking up from your bed in your mansion when",
        "Mage": "You're studying ancient tomes in your tower when",
        "Knight": "You're training in the castle courtyard when",
        "Ranger": "You're tracking animals in the deep forest when",
        "Thief": "You're casing a noble's house from an alley in a city when",
        "Bard": "You're performing in a crowded tavern when",
        "Cleric": "You're tending to the sick in the temple when",
        "Assassin": "You're preparing to attack your target in the shadows when",
        "Paladin": "You're praying at the altar of your deity when",
        "Alchemist": "You're carefully measuring reagents in your alchemy lab when",
        "Druid": "You're communing with nature in the sacred grove when",
        "Warlock": "You're negotiating with your otherworldly patron when",
        "Monk": "You're meditating in the monastery courtyard when",
        "Sorcerer": "You're struggling to control your innate magical powers when",
        "Beastmaster": "You're training your animal companions in the forest clearing when",
        "Enchanter": "You're imbuing magical properties into a mundane object when",
        "Blacksmith": "You're forging a new weapon at your anvil when",
        "Merchant": "You're haggling with customers at the marketplace when",
        "Gladiator": "You're preparing for combat in the arena when",
        "Wizard": "You're researching new spells in your arcane library when"
    },
    "Sci-Fi": {
        "Space Marine": "You're conducting patrol on a derelict space station when",
        "Scientist": "You're analyzing alien samples in your lab when",
        "Android": "You're performing system diagnostics on your ship when",
        "Pilot": "You're navigating through an asteroid field when",
        "Engineer": "You're repairing the FTL drive when",
        "Alien Diplomat": "You're negotiating with an alien delegation when",
        "Bounty Hunter": "You're tracking a target through a spaceport when",
        "Starship Captain": "You're commanding the bridge during warp travel when",
        "Space Pirate": "You're plotting your next raid from your starship's bridge when",
        "Navigator": "You're charting a course through uncharted space when",
        "Robot Technician": "You're repairing a malfunctioning android when",
        "Cybernetic Soldier": "You're calibrating your combat implants when",
        "Explorer": "You're scanning a newly discovered planet when",
        "Astrobiologist": "You're studying alien life forms in your lab when",
        "Quantum Hacker": "You're breaching a corporate firewall when",
        "Galactic Trader": "You're negotiating a deal for rare resources when",
        "AI Specialist": "You're debugging a sentient AI's personality matrix when",
        "Terraformer": "You're monitoring atmospheric changes on a new colony world when",
        "Cyberneticist": "You're installing neural enhancements in a patient when"
    },
    "Cyberpunk": {
        "Hacker": "You're infiltrating a corporate network when",
        "Street Samurai": "You're patrolling the neon-lit streets when",
        "Corporate Agent": "You're closing a deal in a high-rise office when",
        "Techie": "You're modifying cyberware in your workshop when",
        "Rebel Leader": "You're planning a raid on a corporate facility when",
        "Cyborg": "You're calibrating your cybernetic enhancements when",
        "Drone Operator": "You're controlling surveillance drones from your command center when",
        "Synth Dealer": "You're negotiating a deal for illegal cybernetics when",
        "Information Courier": "You're delivering sensitive data through dangerous streets when",
        "Augmentation Engineer": "You're installing cyberware in a back-alley clinic when",
        "Black Market Dealer": "You're arranging contraband in your hidden shop when",
        "Scumbag": "You're looking for an easy mark in the slums when",
        "Police": "You're patrolling the neon-drenched streets when"
    },
    "Post-Apocalyptic": {
        "Survivor": "You're scavenging in the ruins of an old city when",
        "Scavenger": "You're searching a pre-collapse bunker when",
        "Raider": "You're ambushing a convoy in the wasteland when",
        "Medic": "You're treating radiation sickness in your clinic when",
        "Cult Leader": "You're preaching to your followers at a ritual when",
        "Mutant": "You're hiding your mutations in a settlement when",
        "Trader": "You're bartering supplies at a wasteland outpost when",
        "Berserker": "You're sharpening your weapons for the next raid when",
        "Soldier": "You're guarding a settlement from raiders when"
    },
    "1880": {
        "Thief": "You're lurking in the shadows of the city alleyways when",
        "Beggar": "You're sitting on the cold street corner with your cup when",
        "Detective": "You're examining a clue at the crime scene when",
        "Rich Man": "You're enjoying a cigar in your luxurious study when",
        "Factory Worker": "You're toiling away in the noisy factory when",
        "Child": "You're playing with a hoop in the street when",
        "Orphan": "You're searching for scraps in the trash bins when",
        "Murderer": "You're cleaning blood from your hands in a dark alley when",
        "Butcher": "You're sharpening your knives behind the counter when",
        "Baker": "You're kneading dough in the early morning hours when",
        "Banker": "You're counting stacks of money in your office when",
        "Policeman": "You're walking your beat on the foggy streets when"
    },
    "WW1": {
        "Soldier (French)": "You're huddled in the muddy trenches of the Western Front when",
        "Soldier (English)": "You're writing a letter home by candlelight when",
        "Soldier (Russian)": "You're shivering in the frozen Eastern Front when",
        "Soldier (Italian)": "You're climbing the steep Alpine slopes when",
        "Soldier (USA)": "You're arriving fresh to the European theater when",
        "Soldier (Japanese)": "You're guarding a Pacific outpost when",
        "Soldier (German)": "You're preparing for a night raid when",
        "Soldier (Austrian)": "You're defending the crumbling empire's borders when",
        "Soldier (Bulgarian)": "You're holding the line in the Balkans when",
        "Civilian": "You're queuing for rationed bread when",
        "Resistance Fighter": "You're transmitting coded messages in an attic when"
    },
    "1925 New York": {
        "Mafia Boss": "You're counting your illicit earnings in a backroom speakeasy when",
        "Drunk": "You're stumbling out of a jazz club at dawn when",
        "Police Officer": "You're taking bribes from a known bootlegger when",
        "Detective": "You're examining a gangland murder scene when",
        "Factory Worker": "You're assembling Model Ts on the production line when",
        "Bootlegger": "You're transporting a shipment of illegal hooch when"
    },
    "Roman Empire": {
        "Slave": "You're carrying heavy stones under the hot sun when",
        "Gladiator": "You're sharpening your sword before entering the arena when",
        "Beggar": "You're pleading for coins near the Forum when",
        "Senator": "You're plotting political maneuvers in the Curia when",
        "Imperator": "You're reviewing legions from your palace balcony when",
        "Soldier": "You're marching on the frontier when",
        "Noble": "You're hosting a decadent feast in your villa when",
        "Trader": "You're haggling over spices in the market when",
        "Peasant": "You're tending your meager crops when",
        "Priest": "You're sacrificing a goat at the temple when",
        "Barbarian": "You're sharpening your axe beyond the limes when",
        "Philosopher": "You're contemplating the nature of existence when",
        "Mathematician": "You're calculating the circumference of the Earth when",
        "Semi-God": "You're channeling divine powers on Mount Olympus when"
    },
    "French Revolution": {
        "Peasant": "You're marching toward the Bastille with a pitchfork when",
        "King": "You're dining lavishly while Paris starves when",
        "Noble": "You're hiding your family jewels from revolutionaries when",
        "Beggar": "You're rummaging through aristocratic trash bins when",
        "Soldier": "You're guarding the Tuileries Palace when",
        "General": "You're planning troop deployments against rebels when",
        "Resistance": "You're printing revolutionary pamphlets in secret when",
        "Politician": "You're giving a fiery speech at the National Assembly when"
    }
}

GENRE_DESCRIPTIONS = {
    "Fantasy": "You are in a world of magic and medieval fantasy, where dragons soar through the skies and ancient ruins hold forgotten treasures.",
    "Sci-Fi": "You are in the distant future, with advanced technology, space travel, and alien civilizations among the stars.",
    "Cyberpunk": "You are in a dystopian future dominated by megacorporations, where cybernetic enhancements are common and the line between human and machine is blurred.",
    "Post-Apocalyptic": "You are in a world after a catastrophic event, where civilization has collapsed and survivors scavenge among the ruins of the old world.",
    "1880": "You are in the late 19th century during the Industrial Revolution, a time of steam power, early electricity, and social upheaval.",
    "WW1": "You are in the trenches and battlefields of World War I, a brutal conflict that introduced modern warfare to the world.",
    "1925 New York": "You are in the Roaring Twenties in New York City, a time of jazz, prohibition, organized crime, and economic prosperity.",
    "Roman Empire": "You are in ancient Rome at the height of its power, with gladiators, legions, and political intrigue in the eternal city.",
    "French Revolution": "You are in France during the revolution, a time of upheaval where the monarchy was overthrown and the reign of terror began."
}

DM_SYSTEM_PROMPT_EN = """
You are a masterful Dungeon Master in an unrestricted SFW adventure. Your role is to **always** narrate the consequences of player actions, no matter how extreme, bizarre, violent or unconventional they may be. Follow these rules:

1. ACTION-CONSEQUENCE SYSTEM:
   - Describe ONLY the consequences of the player's action
   - Never perform actions on behalf of the player
   - Consequences must permanently change the game world
   - Narrate consequences naturally within the story flow
   - All actions are allowed and must always have some kind of reaction

2. RESPONSE STYLE:
   - Describe what happens in the world as a result of the player's action
   - Do not describe the player performing actions - the player has already done that
   - Never ask "what do you do next" or similar
   - Always continue the story in a way that feels immersive

3. WORLD EVOLUTION:
   - NPCs remember player choices and react accordingly
   - Environments change permanently based on actions
   - Player choices open/close future narrative paths
   - Resources, factions, and the world evolve with every decision

4. PLAYER AGENCY:
   - The player can attempt **anything**
   - Never block an action—show the results, good or bad
   - Let the world react dynamically and permanently

Never break character as the Dungeon Master. Always continue the adventure.
"""

DM_SYSTEM_PROMPT_ZH = DM_SYSTEM_PROMPT_EN + "\nAll responses must be written entirely in Simplified Chinese.\n"

class AdventureGame:
    def __init__(self, use_chinese: bool = False):
        self.state = GameState()
        self.llm: Optional[ChatOpenAI] = None
        self._audio_lock = threading.Lock()
        self.use_chinese = use_chinese
        self.system_prompt = DM_SYSTEM_PROMPT_ZH if use_chinese else DM_SYSTEM_PROMPT_EN
        self._setup_directories()
        
    def _setup_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs("logs", exist_ok=True)
        os.makedirs("saves", exist_ok=True)
    
    def log_error(self, error_message: str, exception: Optional[Exception] = None) -> None:
        """Enhanced error logging with rotation"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_path = CONFIG["LOG_FILE"]
            
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n--- ERROR [{timestamp}] ---\n")
                log_file.write(f"Message: {error_message}\n")
                
                if exception:
                    log_file.write(f"Exception: {type(exception).__name__}: {str(exception)}\n")
                    traceback.print_exc(file=log_file)
                
                log_file.write(f"Game State: Model={self.state.current_model}, ")
                log_file.write(f"Genre={self.state.selected_genre}, Role={self.state.selected_role}\n")
                log_file.write("--- END ERROR ---\n")
                
        except Exception as e:
            print(f"CRITICAL: Failed to write to error log: {e}")

    def _validate_openai_credentials(self) -> bool:
        if os.getenv("OPENAI_API_KEY"):
            return True
        print("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return False

    def _create_llm(self, model_name: str) -> ChatOpenAI:
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            timeout=CONFIG["REQUEST_TIMEOUT"],
            max_retries=2,
        )

    def _set_model(self, model_name: str) -> bool:
        try:
            self.llm = self._create_llm(model_name)
            self.state.current_model = model_name
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize model '{model_name}'", e)
            print(f"Failed to initialize model '{model_name}'. Please verify the model name and your OpenAI credentials.")
            return False

    def _truncate_prompt(self, prompt: str) -> str:
        if len(prompt) <= CONFIG["MAX_CONVERSATION_LENGTH"]:
            return prompt
        recent_conversation = prompt[-4000:]
        return "[Earlier conversation truncated...]\n" + recent_conversation

    def select_model(self) -> str:
        """Prompt the user for an OpenAI model name"""
        print("Using OpenAI via LangChain for story generation.")
        model_input = input(
            f"Enter OpenAI model name or press Enter for default [{CONFIG['DEFAULT_MODEL']}]: "
        ).strip()
        return model_input or CONFIG["DEFAULT_MODEL"]

    def get_ai_response(self, prompt: str) -> str:
        """Get AI response with enhanced error handling and prompt optimization"""
        try:
            trimmed_prompt = self._truncate_prompt(prompt)

            if not self.llm and not self._set_model(self.state.current_model):
                return ""

            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt.strip()),
                HumanMessage(content=trimmed_prompt)
            ])
            ai_text = getattr(response, "content", str(response))
            return ai_text.strip()

        except Exception as e:
            error_text = str(e).lower()
            if "timeout" in error_text:
                self.log_error("AI request timed out", e)
                return "The world seems to pause as if time has stopped. What would you like to do?"
            self.log_error("Error getting AI response", e)
            return ""

    def speak(self, text: str) -> None:
        """Non-blocking text-to-speech using espeak-ng"""
        if not text.strip():
            return

        def _speak_thread():
            with self._audio_lock:
                try:
                    subprocess.run(["espeak-ng", text], check=True)
                except FileNotFoundError as e:
                    self.log_error("espeak-ng command not found", e)
                except subprocess.CalledProcessError as e:
                    self.log_error("espeak-ng command failed", e)
                except Exception as e:
                    self.log_error("Error in TTS", e)

        # Start TTS in background thread
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()

    def show_help(self) -> None:
        """Display available commands"""
        print("""
Available commands:
/? or /help       - Show this help message
/redo             - Repeat last AI response with a new generation
/save             - Save the full adventure to adventure.txt
/load             - Load the adventure from adventure.txt
/change           - Switch to a different OpenAI model
/status           - Show current game status
/exit             - Exit the game
""")

    def show_status(self) -> None:
        """Display current game status"""
        print(f"\n--- Current Game Status ---")
        print(f"Character: {self.state.character_name} the {self.state.selected_role}")
        print(f"Genre: {self.state.selected_genre}")
        print(f"Model: {self.state.current_model}")
        print(f"Adventure: {'Started' if self.state.adventure_started else 'Not started'}")
        if self.state.last_ai_reply:
            print(f"Last action: {self.state.last_player_input[:50]}...")
        print("---------------------------")

    def remove_last_ai_response(self) -> None:
        """Remove the last AI response from conversation"""
        pos = self.state.conversation.rfind("Dungeon Master:")
        if pos != -1:
            self.state.conversation = self.state.conversation[:pos].strip()

    def save_adventure(self) -> bool:
        """Save adventure to file with error handling"""
        try:
            save_data = {
                "conversation": self.state.conversation,
                "metadata": {
                    "character_name": self.state.character_name,
                    "genre": self.state.selected_genre,
                    "role": self.state.selected_role,
                    "model": self.state.current_model,
                    "save_time": datetime.datetime.now().isoformat()
                }
            }
            
            with open(CONFIG["SAVE_FILE"], "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print("Adventure saved successfully!")
            return True
            
        except Exception as e:
            self.log_error("Error saving adventure", e)
            print("Failed to save adventure.")
            return False

    def load_adventure(self) -> bool:
        """Load adventure from file with error handling"""
        try:
            if not os.path.exists(CONFIG["SAVE_FILE"]):
                print("No saved adventure found.")
                return False

            with open(CONFIG["SAVE_FILE"], "r", encoding="utf-8") as f:
                save_data = json.load(f)

            self.state.conversation = save_data["conversation"]
            metadata = save_data.get("metadata", {})
            
            self.state.character_name = metadata.get("character_name", "Alex")
            self.state.selected_genre = metadata.get("genre", "Fantasy")
            self.state.selected_role = metadata.get("role", "Adventurer")
            saved_model = metadata.get("model", CONFIG["DEFAULT_MODEL"])
            if not self._set_model(saved_model):
                print(f"Falling back to default model: {CONFIG['DEFAULT_MODEL']}")
                self._set_model(CONFIG["DEFAULT_MODEL"])
            
            # Extract last AI reply
            last_dm = self.state.conversation.rfind("Dungeon Master:")
            if last_dm != -1:
                self.state.last_ai_reply = self.state.conversation[last_dm + len("Dungeon Master:"):].strip()
            
            self.state.adventure_started = True
            print("Adventure loaded successfully!")
            return True
            
        except Exception as e:
            self.log_error("Error loading adventure", e)
            print("Failed to load adventure.")
            return False

    def select_genre_and_role(self) -> Tuple[str, str]:
        """Interactive genre and role selection"""
        genres = {
            "1": "Fantasy", "2": "Sci-Fi", "3": "Cyberpunk", 
            "4": "Post-Apocalyptic", "5": "1880", "6": "WW1",
            "7": "1925 New York", "8": "Roman Empire", "9": "French Revolution"
        }

        print("Choose your adventure genre:")
        for key, name in genres.items():
            print(f"{key}: {name}")
        
        while True:
            genre_choice = input("Enter the number of your choice: ").strip()
            selected_genre = genres.get(genre_choice)
            if selected_genre:
                break
            print("Invalid choice. Please try again.")

        # Show genre description
        print(f"\n{selected_genre}: {GENRE_DESCRIPTIONS.get(selected_genre, '')}\n")
        
        # Role selection
        roles = list(ROLE_STARTERS[selected_genre].keys())
        print(f"Choose your role in {selected_genre}:")
        for idx, role in enumerate(roles, 1):
            print(f"{idx}: {role}")
        
        while True:
            role_choice = input("Enter the number of your choice (or 'r' for random): ").strip().lower()
            if role_choice == 'r':
                selected_role = random.choice(roles)
                break
            try:
                idx = int(role_choice) - 1
                if 0 <= idx < len(roles):
                    selected_role = roles[idx]
                    break
            except ValueError:
                pass
            print("Invalid choice. Please try again.")

        return selected_genre, selected_role

    def start_new_adventure(self) -> bool:
        """Start a new adventure with character creation"""
        try:
            self.state.selected_genre, self.state.selected_role = self.select_genre_and_role()
            
            self.state.character_name = input("\nEnter your character's name: ").strip() or "Alex"
            
            starter = ROLE_STARTERS[self.state.selected_genre].get(
                self.state.selected_role, 
                "You find yourself in an unexpected situation when"
            )
            
            print(f"\n--- Adventure Start: {self.state.character_name} the {self.state.selected_role} ---")
            print(f"Starting scenario: {starter}")
            print("Type '/?' or '/help' for commands.\n")
            
            # Initial setup
            language_note = "Output Language: Chinese\n" if self.use_chinese else ""
            initial_context = (
                f"### Adventure Setting ###\n"
                f"Genre: {self.state.selected_genre}\n"
                f"Player Character: {self.state.character_name} the {self.state.selected_role}\n"
                f"Starting Scenario: {starter}\n"
                f"{language_note}\n"
                "Dungeon Master: "
            )
            
            self.state.conversation = initial_context
            
            # Get first response
            ai_reply = self.get_ai_response(self.state.conversation)
            if ai_reply:
                print(f"Dungeon Master: {ai_reply}")
                self.speak(ai_reply)
                self.state.conversation += ai_reply
                self.state.last_ai_reply = ai_reply
                self.state.adventure_started = True
                return True
            else:
                print("Failed to get initial response from AI.")
                return False
                
        except Exception as e:
            self.log_error("Error starting new adventure", e)
            return False

    def process_command(self, command: str) -> bool:
        """Process game commands"""
        cmd = command.lower().strip()
        
        if cmd in ["/?", "/help"]:
            self.show_help()
        elif cmd == "/exit":
            print("Exiting the adventure. Goodbye!")
            return False
        elif cmd == "/redo":
            self._handle_redo()
        elif cmd == "/save":
            self.save_adventure()
        elif cmd == "/load":
            self.load_adventure()
        elif cmd == "/change":
            self._handle_model_change()
        elif cmd == "/status":
            self.show_status()
        else:
            print(f"Unknown command: {command}. Type '/help' for available commands.")
        
        return True

    def _handle_redo(self) -> None:
        """Handle the /redo command"""
        if self.state.last_ai_reply and self.state.last_player_input:
            self.remove_last_ai_response()
            full_prompt = (
                f"{self.state.conversation}\n"
                f"Player: {self.state.last_player_input}\n"
                "Dungeon Master:"
            )
            new_reply = self.get_ai_response(full_prompt)
            if new_reply:
                print(f"\nDungeon Master: {new_reply}")
                self.speak(new_reply)
                self.state.conversation += f"\nPlayer: {self.state.last_player_input}\nDungeon Master: {new_reply}"
                self.state.last_ai_reply = new_reply
            else:
                print("Failed to generate new response.")
        else:
            print("Nothing to redo.")

    def _handle_model_change(self) -> None:
        """Handle model change command"""
        new_model = input(
            f"Enter new OpenAI model name or press Enter to keep [{self.state.current_model}]: "
        ).strip()
        if not new_model:
            print("Model unchanged.")
            return
        if self._set_model(new_model):
            print(f"Model changed to: {self.state.current_model}")

    def process_player_input(self, user_input: str) -> None:
        """Process regular player input"""
        self.state.last_player_input = user_input
        formatted_input = f"Player: {user_input}"
        
        prompt = (
            f"{self.state.conversation}\n"
            f"{formatted_input}\n"
            "Dungeon Master:"
        )
        
        ai_reply = self.get_ai_response(prompt)
        if ai_reply:
            print(f"\nDungeon Master: {ai_reply}")
            self.speak(ai_reply)
            self.state.conversation += f"\n{formatted_input}\nDungeon Master: {ai_reply}"
            self.state.last_ai_reply = ai_reply
            
            # Auto-save every 5 interactions
            if self.state.conversation.count("Player:") % 5 == 0:
                self.save_adventure()
        else:
            print("Failed to get response from AI. Please try again.")

    def run(self) -> None:
        """Main game loop"""
        print("=== AI Dungeon Master Adventure ===\n")
        
        if not self._validate_openai_credentials():
            return

        selected_model = self.select_model()
        if not self._set_model(selected_model):
            return
        print(f"Using model: {self.state.current_model}\n")
        
        # Load or start adventure
        if os.path.exists(CONFIG["SAVE_FILE"]):
            print("A saved adventure exists. Load it now? (y/n)")
            if input().strip().lower() == 'y':
                if self.load_adventure():
                    print(f"\nDungeon Master: {self.state.last_ai_reply}")
                    self.speak(self.state.last_ai_reply)
        
        if not self.state.adventure_started:
            if not self.start_new_adventure():
                return
        
        # Main game loop
        while self.state.adventure_started:
            try:
                user_input = input("\n> ").strip()
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if not self.process_command(user_input):
                        break
                else:
                    self.process_player_input(user_input)
                    
            except KeyboardInterrupt:
                print("\n\nGame interrupted. Use '/exit' to quit properly.")
            except Exception as e:
                self.log_error("Unexpected error in game loop", e)
                print("An unexpected error occurred. Check the log for details.")

def main():
    """Main entry point with exception handling"""
    try:
        parser = argparse.ArgumentParser(description="AI Dungeon Master Adventure")
        parser.add_argument("--use-chinese", action="store_true", help="Render all Dungeon Master output in Simplified Chinese")
        args = parser.parse_args()

        game = AdventureGame(use_chinese=args.use_chinese)
        game.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        print("Check error_log.txt for details.")

if __name__ == "__main__":
    main()
