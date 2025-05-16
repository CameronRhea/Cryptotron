import pygame
import random
import string
import os
import sys
import pickle
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import string


pygame.init()

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

# setup fonts
TITLE_FONT = pygame.font.SysFont('Arial', 36)
MAIN_FONT = pygame.font.SysFont('Arial', 28)
LETTER_FONT = pygame.font.SysFont('Courier New', 28)
BUTTON_FONT = pygame.font.SysFont('Arial', 22)
SMALL_FONT = pygame.font.SysFont('Arial', 16)


class GameState:
    def __init__(self):
        self.data = self.load_data()
        self.quotes = self.load_quotes()
        self.quote_num = 1
        self.score = 0
        self.time_elapsed = 0
        self.hints_remaining = 3
        self.new_game()

    def load_data(self):
        with open('quotes.pkl', 'rb') as f:
            data = pickle.load(f)

        # data = [
        #     {
        #         'quote_cleaned' : 'here is my game',  # for demonstration
        #         'Author' : '-- Me'
        #     }
        # ]

        data_df = pd.DataFrame(data)

        return data_df
    
    def load_quotes(self):

        quotes = self.data['quote_cleaned'].tolist()

        return quotes
    
    def get_author(self, quote):
        author = self.data.loc[self.data['quote_cleaned'] == quote]['Author'].iloc[0]
        return author
    
    def new_game(self):
        self.plaintext = random.choice(self.quotes).upper()
        self.author = self.get_author(self.plaintext.lower()) 
                
        # substitution cipher
        self.substitution_map = self.generate_substitution_map()
        self.ciphertext = self.apply_substitution_cipher(self.plaintext, self.substitution_map)
        
        self.player_map = {char: '' for char in set(self.ciphertext) if char.isalpha()}
        self.selected_cipher_char = None
        self.message = f"Quote {self.quote_num}: Decrypt the substitution cipher"
        self.game_won = False
        self.time_elapsed = 0
    
    def apply_shift_cipher(self, text, shift):
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
        alphabet = list(string.ascii_uppercase)
        shuffled = list(string.ascii_uppercase)
        random.shuffle(shuffled)
        
        while sum(1 for a, b in zip(alphabet, shuffled) if a == b) > 21:
            random.shuffle(shuffled) # shuffle again if letters arent different enough
            
        return {a: b for a, b in zip(alphabet, shuffled)}
    
    def apply_substitution_cipher(self, text, sub_map):
        result = ""
        for char in text:
            if char.isalpha():
                result += sub_map[char]
            else:
                result += char
        return result
    
    def check_solution(self):
        decrypted = self.get_current_decryption()
        if decrypted == self.plaintext:
            hint_bonus = self.hints_remaining * 50
            self.score += 100 + hint_bonus
            self.game_won = True
            self.message = f"Correct! +{100 + hint_bonus} points. Time: {self.format_time(self.time_elapsed)}"
            return True
        return False
    
    def get_current_decryption(self):
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
        if self.hints_remaining <= 0:
            self.message = "No hints remaining!"
            return
        
        incorrect_chars = []
        for cipher_char in self.player_map:
            if self.player_map[cipher_char] == '':
                incorrect_chars.append(cipher_char)
            else:
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
            
        cipher_char = random.choice(incorrect_chars)
        
        for k, v in self.substitution_map.items():
            if v == cipher_char:
                plain_char = k
                break
        
        self.player_map[cipher_char] = plain_char
        self.hints_remaining -= 1
        self.message = f"Hint used: {cipher_char} → {plain_char}. {self.hints_remaining} hints remaining."
        
        self.check_solution()

    def analyze_frequency(self):
        cipher_text_letters = [char for char in self.ciphertext if char.isalpha()]
        letter_counts = Counter(cipher_text_letters)
        
        english_freq = {
            'A': 8.2, 'B': 1.5, 'C': 2.8, 'D': 4.3, 'E': 12.7, 'F': 2.2, 'G': 2.0,
            'H': 6.1, 'I': 7.0, 'J': 0.2, 'K': 0.8, 'L': 4.0, 'M': 2.4, 'N': 6.7,
            'O': 7.5, 'P': 1.9, 'Q': 0.1, 'R': 6.0, 'S': 6.3, 'T': 9.1, 'U': 2.8,
            'V': 1.0, 'W': 2.4, 'X': 0.2, 'Y': 2.0, 'Z': 0.1
        }
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Cipher Frequency Analysis', fontsize=16)
        
        cipher_letters = sorted(letter_counts.keys())
        cipher_freq = [letter_counts[letter] / len(cipher_text_letters) * 100 for letter in cipher_letters]
        
        ax1.bar(cipher_letters, cipher_freq, color='blue', alpha=0.7)
        ax1.set_title('Ciphertext Letter Frequency')
        ax1.set_xlabel('Letter')
        ax1.set_ylabel('Frequency (%)')
        ax1.set_ylim(0, 15)
        
        standard_letters = list(string.ascii_uppercase)
        standard_freq = [english_freq[letter] for letter in standard_letters]
        
        ax2.bar(standard_letters, standard_freq, color='green', alpha=0.7)
        ax2.set_title('Standard English Letter Frequency')
        ax2.set_xlabel('Letter')
        ax2.set_ylabel('Frequency (%)')
        ax2.set_ylim(0, 15)
        
        if len(cipher_letters) == 26:
            sorted_cipher_freq = [letter_counts[letter] / len(cipher_text_letters) * 100 
                                for letter in standard_letters]
            correlation = np.corrcoef(sorted_cipher_freq, standard_freq)[0, 1]
            plt.figtext(0.5, 0.01, f"Correlation: {correlation:.2f}", ha="center", fontsize=12)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig('freq_analysis.png')
        plt.close()
        
        self.message = "Frequency analysis completed and saved as 'freq_analysis.png'"


    def format_time(self, seconds):
        """Format seconds into mm:ss format"""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02}:{secs:02}"

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
            
        if self.selected:
            color = HIGHLIGHT_COLOR
        elif not self.is_cipher and player_map and self.letter in player_map.values():
            color = CORRECT_COLOR
        else:
            color = BOX_COLOR
        
        pygame.draw.rect(screen, color, self.rect, 0, 3)
        pygame.draw.rect(screen, DARK_COLOR, self.rect, 1, 3)
        
        if self.is_cipher or (player_map and player_map.get(self.letter, '')):
            letter_to_show = self.letter if self.is_cipher else player_map.get(self.letter, '')
            text_surf = LETTER_FONT.render(letter_to_show, True, TEXT_COLOR)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)
    
    def check_click(self, pos):
        return self.rect.collidepoint(pos) and self.letter.isalpha()

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = words[0]
    
    for word in words[1:]:
        test_line = current_line + ' ' + word
        width, _ = font.size(test_line)
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    
    lines.append(current_line)
    return lines

def main():

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cipher Decryption Game")
    
    game = GameState()
    
    hint_button = Button(WIDTH - 150, 20, 130, 40, "Use Hint", lambda: game.use_hint())
    new_game_button = Button(WIDTH - 150, 70, 130, 40, "New Quote", lambda: game.new_game())
    check_button = Button(WIDTH - 150, 120, 130, 40, "Check Solution", lambda: game.check_solution())
    next_level_button = Button(WIDTH//2 - 65, HEIGHT//2 + 120, 130, 40, "Next Quote", 
                              lambda: next_level(game))
    analyze_button = Button(WIDTH - 150, 170, 130, 40, "Frequency Analysis", lambda: game.analyze_frequency())
    
    alphabet_y = HEIGHT - 100  
    alphabet_buttons = []
    for i, letter in enumerate(string.ascii_uppercase):
        x = 50 + (i % 13) * 40
        y = alphabet_y + (i // 13) * 50
        alphabet_buttons.append(Button(x, y, 30, 40, letter, 
                                    lambda l=letter: select_plain_letter(game, l)))
    
    clock = pygame.time.Clock()
    running = True
    letter_boxes = []
    last_time = pygame.time.get_ticks()
    
    def select_cipher_letter(letter_box):
        game.selected_cipher_char = letter_box.letter
        
        for box in letter_boxes:
            if box.is_cipher:
                box.selected = (box.letter == game.selected_cipher_char)
    
    def select_plain_letter(game, letter):
        if game.selected_cipher_char:
            for cipher_char, plain_char in game.player_map.items():
                if plain_char == letter:
                    game.player_map[cipher_char] = ''
            
            game.player_map[game.selected_cipher_char] = letter
            game.check_solution()
    
    def next_level(game):
        game.quote_num += 1
        game.new_game()
        update_letter_boxes()
    
    def update_letter_boxes():
        nonlocal letter_boxes
        letter_boxes = []
        
        # constants
        max_width = WIDTH - 150
        box_width = 30 
        line_height = 100
        first_line_y = 250
        
        lines = []
        current_line = ""
        current_line_width = 0
        
        for char in game.ciphertext:
            char_width = box_width * 1.5 if char in "MWQ" else box_width
            
            if current_line_width + char_width > max_width and current_line:
                lines.append(current_line)
                current_line = char
                current_line_width = char_width
            else:
                current_line += char
                current_line_width += char_width
        
        if current_line:
            lines.append(current_line)
        
        for line_idx, line in enumerate(lines):
            line_width = len(line) * box_width
            start_x = (WIDTH - line_width) // 2
            
            cipher_y = first_line_y + line_idx * line_height
            plain_y = cipher_y - 50
            
            for i, char in enumerate(line):
                x = start_x + i * box_width
                letter_boxes.append(LetterBox(x, cipher_y, box_width, 40, char, is_cipher=True))
                
                if char.isalpha():
                    letter_boxes.append(LetterBox(x, plain_y, box_width, 40, char, is_cipher=False))
    
    update_letter_boxes()
    
    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0
        last_time = current_time
        
        if not game.game_won:
            game.time_elapsed += dt
        
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # check clicks
                hint_button.check_click(mouse_pos)
                new_game_button.check_click(mouse_pos)
                check_button.check_click(mouse_pos)
                analyze_button.check_click(mouse_pos)

                
                if game.game_won:
                    next_level_button.check_click(mouse_pos)
                
                for box in letter_boxes:
                    if box.is_cipher and box.check_click(mouse_pos):
                        select_cipher_letter(box)
                
                for button in alphabet_buttons:
                    button.check_click(mouse_pos)
        
        # check hover 
        hint_button.check_hover(mouse_pos)
        new_game_button.check_hover(mouse_pos)
        check_button.check_hover(mouse_pos)
        analyze_button.check_hover(mouse_pos)
        
        if game.game_won:
            next_level_button.check_hover(mouse_pos)
        
        for button in alphabet_buttons:
            button.check_hover(mouse_pos)
        
        screen.fill(BACKGROUND_COLOR)
        
        title_surf = TITLE_FONT.render("Cryptotron", True, TEXT_COLOR)
        screen.blit(title_surf, (20, 20))
        
        status_surf = MAIN_FONT.render(game.message, True, TEXT_COLOR)
        screen.blit(status_surf, (20, 70))
        
        score_surf = MAIN_FONT.render(f"Score: {game.score}", True, TEXT_COLOR)
        screen.blit(score_surf, (20, 110))
        
        minutes = int(game.time_elapsed) // 60
        seconds = int(game.time_elapsed) % 60
        time_surf = MAIN_FONT.render(f"Time: {minutes:02}:{seconds:02}", True, TEXT_COLOR)
        screen.blit(time_surf, (200, 110))
        
        hints_surf = MAIN_FONT.render(f"Hints: {game.hints_remaining}", True, TEXT_COLOR)
        screen.blit(hints_surf, (350, 110))
        

        max_line_idx = 0
        for box in letter_boxes:
            if box.is_cipher:
                line_idx = (box.rect.y - 180) // 60
                max_line_idx = max(max_line_idx, line_idx)

        
        for box in letter_boxes:
            box.draw(screen, game.player_map)
        
        base_y = 180 + (max_line_idx + 1) * 60 + 20
        decryption_surf = MAIN_FONT.render("Current plaintext:", True, TEXT_COLOR)
        screen.blit(decryption_surf, (50, base_y))
        
        current_text = game.get_current_decryption()
        wrapped_text = wrap_text(current_text, MAIN_FONT, WIDTH - 100)
        
        for i, line in enumerate(wrapped_text):
            text_surf = MAIN_FONT.render(line, True, HIGHLIGHT_COLOR)
            screen.blit(text_surf, (50, base_y + 40 + i * 30))
        
        instruction_y = base_y + 40 + len(wrapped_text) * 30 + 10
        
        if alphabet_y < instruction_y + 40:
            for i, button in enumerate(alphabet_buttons):
                button.rect.y = instruction_y + 50 + (i // 13) * 50
        
        if game.selected_cipher_char:
            instruction = f"Selected '{game.selected_cipher_char}' - choose a letter to replace it"
            instruction_surf = MAIN_FONT.render(instruction, True, HIGHLIGHT_COLOR)
            screen.blit(instruction_surf, (50, instruction_y))
        else:
            instruction = "Click on a cipher letter, then select a plaintext letter to replace it"
            instruction_surf = MAIN_FONT.render(instruction, True, TEXT_COLOR)
            screen.blit(instruction_surf, (50, instruction_y))
        
        # buttons
        hint_button.draw(screen)
        new_game_button.draw(screen)
        check_button.draw(screen)
        analyze_button.draw(screen)
        
        for button in alphabet_buttons:
            button.draw(screen)
        
        # win screen
        if game.game_won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            win_surf = TITLE_FONT.render(f"Cipher Solved!", True, CORRECT_COLOR)
            win_rect = win_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 150))
            screen.blit(win_surf, win_rect)
            
            time_surf = MAIN_FONT.render(f"Time: {game.format_time(game.time_elapsed)}", True, TEXT_COLOR)
            time_rect = time_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
            screen.blit(time_surf, time_rect)
            
            score_surf = MAIN_FONT.render(f"Score: {game.score}", True, TEXT_COLOR)
            score_rect = score_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 70))
            screen.blit(score_surf, score_rect)
            
            quote_lines = wrap_text(f'"{game.plaintext}"', MAIN_FONT, WIDTH - 200)
            for i, line in enumerate(quote_lines):
                quote_surf = MAIN_FONT.render(line, True, HIGHLIGHT_COLOR)
                quote_rect = quote_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 20 + i * 30))
                screen.blit(quote_surf, quote_rect)
            
            author_line = f"{game.author}"
            author_surf = MAIN_FONT.render(author_line, True, CORRECT_COLOR)
            author_rect = author_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 20 + len(quote_lines) * 30 + 30))
            screen.blit(author_surf, author_rect)
            
            # next quote
            next_level_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()