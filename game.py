import pygame
import random
import string
import os
import sys
import pickle
import pandas as pd
import numpy as np
import re


# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1800, 1000
BACKGROUND_COLOR = (30, 30, 50)
TEXT_COLOR = (240, 240, 240)
HIGHLIGHT_COLOR = (100, 200, 100)
CORRECT_COLOR = (50, 200, 50)
WRONG_COLOR = (200, 50, 50)
HINT_COLOR = (200, 200, 50)
BOX_COLOR = (60, 60, 80)
DARK_COLOR = (20, 20, 30)
BUTTON_COLOR = (80, 80, 120)
BUTTON_HOVER_COLOR = (100, 100, 150)

# Font setup
TITLE_FONT = pygame.font.SysFont('Arial', 36)
MAIN_FONT = pygame.font.SysFont('Arial', 28)
LETTER_FONT = pygame.font.SysFont('Courier New', 28)
BUTTON_FONT = pygame.font.SysFont('Arial', 22)
SMALL_FONT = pygame.font.SysFont('Arial', 16)

# Game state
class GameState:
    def __init__(self):
        self.quotes = self.load_quotes()
        self.level = 1
        self.score = 0
        self.time_remaining = 300  # 5 minutes
        self.hints_remaining = 3
        self.new_game()
    
    def load_quotes(self):

        with open('quotes.pkl', 'rb') as f:
            data = pickle.load(f)
        quotes = list(data['quote_cleaned'])

        return quotes
    
    def new_game(self):
        """Set up a new game with a random quote and cipher"""
        self.plaintext = random.choice(self.quotes).upper()
        
        # Decide on cipher type (50% chance for each)
        self.is_shift_cipher = random.choice([True, False])
        
        if self.is_shift_cipher:
            # Create a shift cipher
            self.shift_value = random.randint(1, 25)
            self.ciphertext = self.apply_shift_cipher(self.plaintext, self.shift_value)
            self.cipher_type_name = "Shift Cipher"
        else:
            # Create a substitution cipher
            self.substitution_map = self.generate_substitution_map()
            self.ciphertext = self.apply_substitution_cipher(self.plaintext, self.substitution_map)
            self.cipher_type_name = "Substitution Cipher"
        
        # Initialize the player's guesses
        self.player_map = {char: '' for char in set(self.ciphertext) if char.isalpha()}
        self.selected_cipher_char = None
        self.message = f"Level {self.level}: Decrypt the {self.cipher_type_name}"
        self.game_won = False
    
    def apply_shift_cipher(self, text, shift):
        """Apply a Caesar/shift cipher to the text"""
        result = ""
        for char in text:
            if char.isalpha():
                ascii_offset = ord('A')
                shifted = (ord(char) - ascii_offset + shift) % 26 + ascii_offset
                result += chr(shifted)
            else:
                result += char
        return result
    
    def generate_substitution_map(self):
        """Generate a random substitution map for all letters"""
        alphabet = list(string.ascii_uppercase)
        shuffled = list(string.ascii_uppercase)
        random.shuffle(shuffled)
            
        return {a: b for a, b in zip(alphabet, shuffled)}
    
    def apply_substitution_cipher(self, text, sub_map):
        """Apply a substitution cipher to the text"""
        result = ""
        for char in text:
            if char.isalpha():
                result += sub_map[char]
            else:
                result += char
        return result
    
    def check_solution(self):
        """Check if the player's solution is correct"""
        decrypted = self.get_current_decryption()
        if decrypted == self.plaintext:
            self.score += 100 + (self.time_remaining // 10) + (50 if self.is_shift_cipher else 100)
            self.game_won = True
            self.message = f"Correct! +{100 + (self.time_remaining // 10) + (50 if self.is_shift_cipher else 100)} points"
            return True
        return False
    
    def get_current_decryption(self):
        """Get the current decryption based on player's guesses"""
        result = ""
        for char in self.ciphertext:
            if char.isalpha():
                if self.player_map[char]:
                    result += self.player_map[char]
                else:
                    result += "_"
            else:
                result += char
        return result
    
    def use_hint(self):
        """Provide a hint by revealing a correct letter"""
        if self.hints_remaining <= 0:
            self.message = "No hints remaining!"
            return
        
        # Find unfilled or incorrect mappings
        incorrect_chars = []
        for cipher_char in self.player_map:
            if self.player_map[cipher_char] == '':
                incorrect_chars.append(cipher_char)
            elif self.is_shift_cipher:
                plain_char = chr((ord(cipher_char) - ord('A') - self.shift_value) % 26 + ord('A'))
                if self.player_map[cipher_char] != plain_char:
                    incorrect_chars.append(cipher_char)
            else:
                # For substitution cipher, find the key for the value
                correct_plain_char = None
                for k, v in self.substitution_map.items():
                    if v == cipher_char:
                        correct_plain_char = k
                        break
                
                if self.player_map[cipher_char] != correct_plain_char:
                    incorrect_chars.append(cipher_char)
        
        if not incorrect_chars:
            self.message = "No more letters to hint!"
            return
            
        # Choose a random letter to reveal
        cipher_char = random.choice(incorrect_chars)
        
        # Find the correct mapping
        if self.is_shift_cipher:
            plain_char = chr((ord(cipher_char) - ord('A') - self.shift_value) % 26 + ord('A'))
        else:
            # For substitution cipher, find the key for the value
            for k, v in self.substitution_map.items():
                if v == cipher_char:
                    plain_char = k
                    break
        
        self.player_map[cipher_char] = plain_char
        self.hints_remaining -= 1
        self.message = f"Hint used: {cipher_char} → {plain_char}. {self.hints_remaining} hints remaining."
        
        # Check if the solution is correct after adding the hint
        self.check_solution()

# Game UI Elements
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
    
    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, 0, 5)
        pygame.draw.rect(screen, DARK_COLOR, self.rect, 2, 5)
        
        text_surf = BUTTON_FONT.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
    
    def check_click(self, pos):
        if self.rect.collidepoint(pos) and self.action:
            self.action()
            return True
        return False

class LetterBox:
    def __init__(self, x, y, width, height, letter, is_cipher=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.letter = letter
        self.is_cipher = is_cipher
        self.selected = False
    
    def draw(self, screen, player_map=None):
        if not self.letter.isalpha():
            return
            
        # Draw the box
        if self.selected:
            color = HIGHLIGHT_COLOR
        elif not self.is_cipher and player_map and self.letter in player_map.values():
            color = CORRECT_COLOR
        else:
            color = BOX_COLOR
        
        pygame.draw.rect(screen, color, self.rect, 0, 3)
        pygame.draw.rect(screen, DARK_COLOR, self.rect, 1, 3)
        
        # Draw the letter
        if self.is_cipher or (player_map and player_map.get(self.letter, '')):
            letter_to_show = self.letter if self.is_cipher else player_map.get(self.letter, '')
            text_surf = LETTER_FONT.render(letter_to_show, True, TEXT_COLOR)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)
    
    def check_click(self, pos):
        return self.rect.collidepoint(pos) and self.letter.isalpha()

# Main Game Function
def main():
    # Create game window
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cipher Decryption Game")
    
    # Initialize game state
    game = GameState()
    
    # Create UI elements
    hint_button = Button(WIDTH - 150, 20, 130, 40, "Use Hint", lambda: game.use_hint())
    new_game_button = Button(WIDTH - 150, 70, 130, 40, "New Quote", lambda: game.new_game())
    check_button = Button(WIDTH - 150, 120, 130, 40, "Check Solution", lambda: game.check_solution())
    next_level_button = Button(WIDTH//2 - 65, HEIGHT//2 + 50, 130, 40, "Next Level", 
                              lambda: next_level(game))
    
    # Define the alphabet position at the bottom of the screen 
    # Fixed position - no longer depends on instruction_y
    alphabet_y = HEIGHT - 100  
    alphabet_buttons = []
    for i, letter in enumerate(string.ascii_uppercase):
        x = 50 + (i % 13) * 40
        y = alphabet_y + (i // 13) * 50
        alphabet_buttons.append(Button(x, y, 30, 40, letter, 
                                    lambda l=letter: select_plain_letter(game, l)))
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    letter_boxes = []
    last_time = pygame.time.get_ticks()
    
    def select_cipher_letter(letter_box):
        """Select a cipher letter to replace"""
        game.selected_cipher_char = letter_box.letter
        
        # Unselect all other boxes
        for box in letter_boxes:
            if box.is_cipher:
                box.selected = (box.letter == game.selected_cipher_char)
    
    def select_plain_letter(game, letter):
        """Assign a plain letter to the selected cipher letter"""
        if game.selected_cipher_char:
            # Check if this plain letter is already assigned
            for cipher_char, plain_char in game.player_map.items():
                if plain_char == letter:
                    game.player_map[cipher_char] = ''
            
            game.player_map[game.selected_cipher_char] = letter
            game.check_solution()
    
    def next_level(game):
        """Advance to the next level"""
        game.level += 1
        game.new_game()
        game.time_remaining = 300  # Reset timer
        game.hints_remaining = 3   # Reset hints
        update_letter_boxes()
    
    def update_letter_boxes():
        """Update the letter boxes based on the current ciphertext"""
        nonlocal letter_boxes
        letter_boxes = []
        
        # Constants for layout
        max_width = WIDTH - 150
        box_width = 30  # Fixed width for each box
        line_height = 100  # Height between lines
        first_line_y = 250  # Y position of the first line
        
        # Split text into lines
        lines = []
        current_line = ""
        current_line_width = 0
        
        for char in game.ciphertext:
            # Add a bit more space for wide characters
            char_width = box_width * 1.5 if char in "MWQ" else box_width
            
            if current_line_width + char_width > max_width and current_line:
                # Start a new line if this would exceed max width
                lines.append(current_line)
                current_line = char
                current_line_width = char_width
            else:
                current_line += char
                current_line_width += char_width
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        # Create letter boxes for each line
        for line_idx, line in enumerate(lines):
            # Calculate start position to center this line
            line_width = len(line) * box_width
            start_x = (WIDTH - line_width) // 2
            
            # Y positions for this line
            cipher_y = first_line_y + line_idx * line_height
            plain_y = cipher_y - 50
            
            # Create letter boxes for this line
            for i, char in enumerate(line):
                x = start_x + i * box_width
                letter_boxes.append(LetterBox(x, cipher_y, box_width, 40, char, is_cipher=True))
                
                # Create plain letter boxes above
                if char.isalpha():
                    letter_boxes.append(LetterBox(x, plain_y, box_width, 40, char, is_cipher=False))
    
    # Initial letter box setup
    update_letter_boxes()
    
    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0  # Convert to seconds
        last_time = current_time
        
        # Reduce time if game is active
        if not game.game_won and game.time_remaining > 0:
            game.time_remaining -= dt
        
        # Time's up
        if game.time_remaining <= 0 and not game.game_won:
            game.time_remaining = 0
            game.message = "Time's up! Game over."
        
        # Handle events
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check button clicks
                hint_button.check_click(mouse_pos)
                new_game_button.check_click(mouse_pos)
                check_button.check_click(mouse_pos)
                
                if game.game_won:
                    next_level_button.check_click(mouse_pos)
                
                # Check for cipher letter selection
                for box in letter_boxes:
                    if box.is_cipher and box.check_click(mouse_pos):
                        select_cipher_letter(box)
                
                # Check alphabet button clicks
                for button in alphabet_buttons:
                    button.check_click(mouse_pos)
        
        # Update hover states
        hint_button.check_hover(mouse_pos)
        new_game_button.check_hover(mouse_pos)
        check_button.check_hover(mouse_pos)
        
        if game.game_won:
            next_level_button.check_hover(mouse_pos)
        
        for button in alphabet_buttons:
            button.check_hover(mouse_pos)
        
        # Draw everything
        screen.fill(BACKGROUND_COLOR)
        
        # Draw UI elements
        title_surf = TITLE_FONT.render("Cipher Decryption Game", True, TEXT_COLOR)
        screen.blit(title_surf, (20, 20))
        
        # Draw game status
        status_surf = MAIN_FONT.render(game.message, True, TEXT_COLOR)
        screen.blit(status_surf, (20, 70))
        
        # Draw score and level
        score_surf = MAIN_FONT.render(f"Score: {game.score}", True, TEXT_COLOR)
        screen.blit(score_surf, (20, 110))
        
        # Draw remaining time
        minutes = int(game.time_remaining) // 60
        seconds = int(game.time_remaining) % 60
        time_color = WRONG_COLOR if game.time_remaining < 60 else TEXT_COLOR
        time_surf = MAIN_FONT.render(f"Time: {minutes:02}:{seconds:02}", True, time_color)
        screen.blit(time_surf, (200, 110))
        
        # Draw hints remaining
        hints_surf = MAIN_FONT.render(f"Hints: {game.hints_remaining}", True, TEXT_COLOR)
        screen.blit(hints_surf, (350, 110))
        
        # Draw cipher type
        type_surf = MAIN_FONT.render(f"Type: {game.cipher_type_name}", True, TEXT_COLOR)
        screen.blit(type_surf, (500, 110))
        
        # Determine how many lines we have from the letter boxes
        max_line_idx = 0
        for box in letter_boxes:
            if box.is_cipher:
                # Calculate line index from y position
                line_idx = (box.rect.y - 180) // 60
                max_line_idx = max(max_line_idx, line_idx)
        
        # Draw letter boxes
        # cipher_label = MAIN_FONT.render("Cipher text:", True, TEXT_COLOR)
        # screen.blit(cipher_label, (50, 180))
        
        # plain_label = MAIN_FONT.render("Your decryption:", True, TEXT_COLOR)
        # screen.blit(plain_label, (50, 130))
        
        for box in letter_boxes:
            box.draw(screen, game.player_map)
        
        # Draw current decrypted text status - position below all lines
        base_y = 180 + (max_line_idx + 1) * 60 + 20
        decryption_surf = MAIN_FONT.render("Plaintext:", True, TEXT_COLOR)
        screen.blit(decryption_surf, (50, base_y))
        
        # Draw the actual decrypted text - wrap it if needed
        current_text = game.get_current_decryption()
        wrapped_text = []
        
        # Simple text wrapping
        line = ""
        for word in current_text.split():
            test_line = line + " " + word if line else word
            if MAIN_FONT.size(test_line)[0] > WIDTH - 100:
                wrapped_text.append(line)
                line = word
            else:
                line = test_line
        
        if line:
            wrapped_text.append(line)
        
        for i, line in enumerate(wrapped_text):
            text_surf = MAIN_FONT.render(line, True, HIGHLIGHT_COLOR)
            screen.blit(text_surf, (50, base_y + 40 + i * 30))
        
        # Draw instruction - after drawing decryption text
        instruction_y = base_y + 40 + len(wrapped_text) * 30 + 10
        
        # Check if alphabet buttons might overlap with instructions
        # If so, dynamically adjust their position
        if alphabet_y < instruction_y + 40:  # If alphabet would overlap instructions
            # Redraw alphabet buttons at a position below instructions
            for i, button in enumerate(alphabet_buttons):
                button.rect.y = instruction_y + 50 + (i // 13) * 50  # Move below instructions
        
        if game.selected_cipher_char:
            instruction = f"Selected '{game.selected_cipher_char}' - choose a letter to replace it"
            instruction_surf = MAIN_FONT.render(instruction, True, HIGHLIGHT_COLOR)
            screen.blit(instruction_surf, (50, instruction_y))
        else:
            instruction = "Click on a cipher letter, then select a plaintext letter to replace it"
            instruction_surf = MAIN_FONT.render(instruction, True, TEXT_COLOR)
            screen.blit(instruction_surf, (50, instruction_y))
        
        # Draw buttons
        hint_button.draw(screen)
        new_game_button.draw(screen)
        check_button.draw(screen)
        
        # Draw alphabet selection
        for button in alphabet_buttons:
            button.draw(screen)
        
        # Draw win screen
        if game.game_won:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            # Draw win message
            win_surf = TITLE_FONT.render(f"Great job! Level {game.level} completed!", True, CORRECT_COLOR)
            win_rect = win_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            screen.blit(win_surf, win_rect)
            
            score_surf = MAIN_FONT.render(f"Score: {game.score}", True, TEXT_COLOR)
            score_rect = score_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(score_surf, score_rect)
            
            # Draw next level button
            next_level_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()