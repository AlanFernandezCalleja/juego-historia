import pygame
import sys
import pygame.mixer
import random # Needed for shuffling answers

# Inicialización de Pygame
pygame.init()
pygame.mixer.init()

# Tamaño de la pantalla
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Historia de Bolivia: El Juego")

# Cargar música de fondo
pygame.mixer.music.load("f.mp3")
pygame.mixer.music.play(-1)

# --- Colores ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
BRIGHT_GREEN = (0, 255, 0)
RED = (200, 0, 0)
BRIGHT_RED = (255, 0, 0)
BLUE = (0, 0, 200)
BRIGHT_BLUE = (0, 0, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)

# --- Fuentes ---
font_dialogue_text = pygame.font.SysFont("timesnewroman", 24)
font_button_text = pygame.font.SysFont("timesnewroman", 20)
font_ui = pygame.font.SysFont("timesnewroman", 30)

# --- Button Class ---
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None, arg=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action # A function or method to call when clicked
        self.arg = arg # An argument to pass to the action function

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.color
        if self.rect.collidepoint(mouse_pos):
            current_color = self.hover_color
        
        pygame.draw.rect(surface, current_color, self.rect)
        text_surf = font_button_text.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if self.rect.collidepoint(event.pos):
                    if self.action:
                        if self.arg is not None:
                            self.action(self.arg)
                        else:
                            self.action()
                    return True # Button was clicked
        return False # Button was not clicked

# --- Character Classes ---
class Personaje:
    def __init__(self, x, y, image_path, name=""):
        self.x = x
        self.y = y
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.name = name
        self.question_asked = False # Flag to track if this character's question has been answered correctly
        self.attempts = 0 # To count attempts for scoring

# --- Game State Variables ---
game_state = "exploring" # "exploring", "dialogue", "score_screen"
current_dialogue_target = None
dialogue_text = ""
speaker_image = None
dialogue_buttons = []

# --- Game Stats ---
player_lives = 3
player_score = 0

# --- Questions Data (Bolivian History Examples) ---
# Each entry: (question, correct_answer, [incorrect_answer1, incorrect_answer2, ...])
QUESTIONS = {
    "Juanito": {
        "question": "¿Quién fue el primer presidente de Bolivia?",
        "correct": "Simón Bolívar",
        "options": ["Antonio José de Sucre", "Andrés de Santa Cruz", "José Ballivián"]
    },
    "Carly": {
        "question": "¿En qué año se fundó la ciudad de La Paz?",
        "correct": "1548",
        "options": ["1825", "1781", "1492"]
    },
    "Carlos": {
        "question": "¿Cuál es el departamento más grande de Bolivia?",
        "correct": "Santa Cruz",
        "options": ["La Paz", "Cochabamba", "Beni"]
    },
    "Pedro": {
        "question": "¿Qué importante batalla se libró en 1824 que consolidó la independencia de Bolivia?",
        "correct": "Batalla de Ayacucho",
        "options": ["Batalla de Junín", "Batalla de Tumusla", "Batalla de Ingavi"]
    }
}

# --- Load Assets ---
personajes = [
    Personaje(100, 200, "a.png", "Juanito"),
    Personaje(300, 300, "b.png", "Carly"),
    Personaje(500, 400, "c.png", "Carlos"),
    Personaje(650, 450, "d.png", "Pedro"), # Pedro's image and name
]

# Personaje principal (player)
personaje_principal = Personaje(50, 50, "a.png", "Player")

# Load and scale background image to fill the entire screen
fondo = pygame.image.load("fondo.jpg").convert()
fondo = pygame.transform.scale(fondo, (width, height))

# Load image for the dialogue box
dialog_box_height = height // 4
imagen_dia = pygame.image.load("dia.png").convert_alpha()
imagen_dia = pygame.transform.scale(imagen_dia, (width, dialog_box_height))

# Images for speaker icons (assuming 'a.png' is generic, use specific for characters)
speaker_images = {
    "Juanito": pygame.image.load("a.png").convert_alpha(), # Assuming a.png is character A
    "Carly": pygame.image.load("b.png").convert_alpha(),
    "Carlos": pygame.image.load("c.png").convert_alpha(),
    "Pedro": pygame.image.load("d.png").convert_alpha(),
    "Player": pygame.image.load("a.png").convert_alpha(), # Placeholder for player icon if needed
}

# --- Dialogue System Functions ---
def start_dialogue(character):
    global game_state, current_dialogue_target, dialogue_text, speaker_image, dialogue_buttons
    
    game_state = "dialogue"
    current_dialogue_target = character
    speaker_image = speaker_images.get(character.name)
    dialogue_buttons = [] # Clear previous buttons

    if character.question_asked:
        dialogue_text = f"¡Ya me respondiste {character.name}! Gracias por tu ayuda."
        btn_ok = Button(width // 2 - 70, height - dialog_box_height + 80, 140, 40, "Ok", GREEN, BRIGHT_GREEN, end_dialogue)
        dialogue_buttons.append(btn_ok)
        return

    # Get the question for the current character
    q_data = QUESTIONS.get(character.name)
    if q_data:
        dialogue_text = q_data["question"]
        all_answers = q_data["options"] + [q_data["correct"]]
        random.shuffle(all_answers) # Shuffle to randomize button order

        button_width = 180
        button_height = 40
        start_x = (width - (2 * button_width + 20)) // 2 # Center two buttons
        start_y = height - dialog_box_height + 60

        for i, answer_text in enumerate(all_answers):
            x_pos = start_x + (i % 2) * (button_width + 20)
            y_pos = start_y + (i // 2) * (button_height + 10)

            # Determine if this is the correct answer
            is_correct = (answer_text == q_data["correct"])
            
            btn_color = BLUE if not is_correct else GREEN # Optional: correct answer button could be different color
            btn_hover_color = BRIGHT_BLUE if not is_correct else BRIGHT_GREEN

            btn = Button(x_pos, y_pos, button_width, button_height, answer_text, btn_color, btn_hover_color, check_answer, is_correct)
            dialogue_buttons.append(btn)
        
        current_dialogue_target.attempts = 0 # Reset attempts for this question

def check_answer(is_correct):
    global dialogue_text, dialogue_buttons, player_lives, player_score, game_state
    
    character = current_dialogue_target
    character.attempts += 1
    dialogue_buttons = [] # Clear buttons after an answer is chosen

    if is_correct:
        dialogue_text = "¡Correcto! ¡Excelente!"
        # Award points
        if character.attempts == 1:
            points_earned = 50
        elif character.attempts == 2:
            points_earned = 30
        else: # 3rd attempt or more (due to extra lives)
            points_earned = 10
        
        player_score += points_earned
        character.question_asked = True # Mark as answered

        btn_ok = Button(width // 2 - 70, height - dialog_box_height + 80, 140, 40, "Continuar", GREEN, BRIGHT_GREEN, end_dialogue)
        dialogue_buttons.append(btn_ok)
        
        # Check if all characters have been answered
        if all(p.question_asked for p in personajes):
            game_state = "score_screen"

    else:
        dialogue_text = "Incorrecto. Intenta de nuevo."
        player_lives -= 1
        
        if player_lives < 0: # If lives drop below zero, start deducting points instead
            player_score -= 30
            dialogue_text = "Incorrecto. ¡Sin vidas! -30 puntos. Intenta de nuevo."
        
        # Restore answer buttons to let player retry
        q_data = QUESTIONS.get(character.name)
        if q_data:
            all_answers = q_data["options"] + [q_data["correct"]]
            random.shuffle(all_answers)

            button_width = 180
            button_height = 40
            start_x = (width - (2 * button_width + 20)) // 2
            start_y = height - dialog_box_height + 60

            for i, answer_text in enumerate(all_answers):
                x_pos = start_x + (i % 2) * (button_width + 20)
                y_pos = start_y + (i // 2) * (button_height + 10)
                is_correct_btn = (answer_text == q_data["correct"])
                btn_color = BLUE if not is_correct_btn else GREEN
                btn_hover_color = BRIGHT_BLUE if not is_correct_btn else BRIGHT_GREEN

                btn = Button(x_pos, y_pos, button_width, button_height, answer_text, btn_color, btn_hover_color, check_answer, is_correct_btn)
                dialogue_buttons.append(btn)

def end_dialogue():
    global game_state, current_dialogue_target, dialogue_text, speaker_image, dialogue_buttons
    game_state = "exploring"
    current_dialogue_target = None
    dialogue_text = ""
    speaker_image = None
    dialogue_buttons = []

# --- Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                if game_state == "exploring" and current_dialogue_target:
                    start_dialogue(current_dialogue_target)
            
            if event.key == pygame.K_q:
                # Quitting dialogue / returning to exploring
                if game_state == "dialogue":
                    end_dialogue()
                elif game_state == "score_screen":
                    # You could add a 'play again' option here
                    pygame.quit()
                    sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "dialogue":
                for button in dialogue_buttons:
                    if button.handle_event(event):
                        break # Only handle one button click at a time

    # --- Player Movement (Continuous) ---
    if game_state == "exploring":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            personaje_principal.x -= 5
        if keys[pygame.K_RIGHT]:
            personaje_principal.x += 5
        if keys[pygame.K_UP]:
            personaje_principal.y -= 5
        if keys[pygame.K_DOWN]:
            personaje_principal.y += 5

    # --- Update Rect positions for accurate collision detection ---
    personaje_principal.rect.topleft = (personaje_principal.x, personaje_principal.y)
    for p in personajes:
        p.rect.topleft = (p.x, p.y)

    # --- Proximity Detection ---
    if game_state == "exploring":
        current_dialogue_target = None
        for personaje in personajes:
            distance = pygame.math.Vector2(personaje_principal.rect.center).distance_to(personaje.rect.center)
            if distance < 100:
                current_dialogue_target = personaje
                break

    # --- Drawing ---
    screen.blit(fondo, (0, 0))

    for personaje in personajes:
        screen.blit(personaje.image, (personaje.x, personaje.y))
    
    screen.blit(personaje_principal.image, (personaje_principal.x, personaje_principal.y))

    # --- Draw UI (Lives and Score) ---
    lives_text_surf = font_ui.render(f"Vidas: {max(0, player_lives)}", True, YELLOW) # Max(0, lives) to prevent negative display
    screen.blit(lives_text_surf, (10, 10))

    score_text_surf = font_ui.render(f"Puntos: {player_score}", True, YELLOW)
    screen.blit(score_text_surf, (width - score_text_surf.get_width() - 10, 10))

    # --- Draw Dialogue or Score Screen ---
    if game_state == "dialogue":
        dialog_box_y = height - dialog_box_height
        screen.blit(imagen_dia, (0, dialog_box_y))

        text_surface = font_dialogue_text.render(dialogue_text, True, BLACK)
        text_x = width // 2 - text_surface.get_width() // 2
        text_y = dialog_box_y + 10
        screen.blit(text_surface, (text_x, text_y))

        if speaker_image:
            speaker_image_resized = pygame.transform.scale(speaker_image, (70, 70))
            screen.blit(speaker_image_resized, (width - speaker_image_resized.get_width() - 10, dialog_box_y + 10))

        for button in dialogue_buttons:
            button.draw(screen)

    elif game_state == "score_screen":
        screen.fill(BLACK) # Clear screen for score display
        score_title_surf = font_ui.render("¡Felicidades! ¡Historia Completa!", True, WHITE)
        score_val_surf = font_ui.render(f"Puntuación Final: {player_score} puntos", True, YELLOW)
        
        title_rect = score_title_surf.get_rect(center=(width // 2, height // 2 - 50))
        score_rect = score_val_surf.get_rect(center=(width // 2, height // 2 + 20))

        screen.blit(score_title_surf, title_rect)
        screen.blit(score_val_surf, score_rect)

        # Optional: Add a button to quit or play again
        btn_quit_game = Button(width // 2 - 70, height - 100, 140, 50, "Salir (Q)", RED, BRIGHT_RED, pygame.quit)
        btn_quit_game.draw(screen)


    pygame.display.flip()
    pygame.time.Clock().tick(30)