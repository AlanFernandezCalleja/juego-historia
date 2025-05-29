import pygame
import sys
import pygame.mixer
import random
import math
import json # New: Import json for score management

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
ORANGE = (255, 165, 0)
TRANSPARENT_BLACK = (0, 0, 0, 180) # For overlays

# Fireworks colors
FIREWORK_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255),
    (0, 255, 255), (255, 128, 0), (128, 0, 255), (0, 128, 255), (255, 255, 255)
]


# --- Fuentes ---
font_dialogue_text = pygame.font.SysFont("timesnewroman", 24)
font_button_text = pygame.font.SysFont("timesnewroman", 20)
font_ui = pygame.font.SysFont("timesnewroman", 30)
font_timer = pygame.font.SysFont("timesnewroman", 40, bold=True)
font_title = pygame.font.SysFont("timesnewroman", 48, bold=True)
font_instructions = pygame.font.SysFont("timesnewroman", 30)
font_level_message = pygame.font.SysFont("timesnewroman", 26, bold=True)
font_input = pygame.font.SysFont("timesnewroman", 36) # New: for name input


# --- Button Class ---
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None, arg=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.arg = arg

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
                    return True
        return False

# --- Character and Object Classes ---
# --- Character and Object Classes ---
class Personaje(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, name="", scale_factor=3):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()
        # Scale based on provided scale_factor
        self.image = pygame.transform.scale(self.original_image, (int(70 * scale_factor), int(70 * scale_factor)))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.x = x
        self.y = y
        self.name = name
        self.question_asked = False
        self.attempts = 0 # For trivia
        
        # For Level 3 dragging
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def update(self):
        # Update rect for normal movement or fixed position
        self.rect.topleft = (self.x, self.y)

    def start_drag(self, mouse_pos):
        self.is_dragging = True
        self.drag_offset_x = self.x - mouse_pos[0]
        self.drag_offset_y = self.y - mouse_pos[1]

    def stop_drag(self):
        self.is_dragging = False

    def do_drag(self, mouse_pos):
        if self.is_dragging:
            self.x = mouse_pos[0] + self.drag_offset_x
            self.y = mouse_pos[1] + self.drag_offset_y  # <-- THIS LINE WAS THE ERROR
            self.rect.topleft = (self.x, self.y) # Update rect instantly for dragging


class HiddenObject(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (20, 20)) 
        self.rect = self.image.get_rect(center=(x, y))
        self.found = False


class PuzzlePiece(pygame.sprite.Sprite):
    def __init__(self, image_surface, correct_pos, current_pos):
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(topleft=current_pos)
        self.correct_pos = correct_pos # (x, y) coordinates of its correct top-left
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def start_drag(self, mouse_pos):
        self.is_dragging = True
        self.drag_offset_x = self.rect.x - mouse_pos[0]
        self.drag_offset_y = self.rect.y - mouse_pos[1]

    def stop_drag(self):
        self.is_dragging = False

    def do_drag(self, mouse_pos):
        if self.is_dragging:
            self.rect.x = mouse_pos[0] + self.drag_offset_x
            self.rect.y = mouse_pos[1] + self.drag_offset_y

    def snap_to_grid(self, grid_slots, tolerance=20):
        # Find the closest slot that the piece is near
        min_dist = float('inf')
        closest_slot_rect = None
        for slot_rect in grid_slots:
            dist = pygame.math.Vector2(self.rect.center).distance_to(slot_rect.center)
            if dist < min_dist:
                min_dist = dist
                closest_slot_rect = slot_rect
        
        if closest_slot_rect and min_dist < tolerance: # If within tolerance, snap
            self.rect.topleft = closest_slot_rect.topleft

# --- Fireworks Particle System ---
class Particle:
    def __init__(self, x, y, color, size, velocity):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.velocity = velocity # (vx, vy)
        self.alpha = 255 # For fading effect
        self.lifetime = random.randint(30, 60) # frames

    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.velocity = (self.velocity[0] * 0.98, self.velocity[1] * 0.98 + 0.2) # Gravity effect
        self.lifetime -= 1
        self.alpha = max(0, self.alpha - 5) # Fade out

    def draw(self, surface):
        if self.lifetime > 0:
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (self.color[0], self.color[1], self.color[2], self.alpha), (self.size, self.size), self.size)
            surface.blit(s, (self.x - self.size, self.y - self.size))

class Firework:
    def __init__(self, x, y, color, num_particles=50):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            velocity = (speed * math.cos(angle), speed * math.sin(angle))
            size = random.randint(2, 4)
            self.particles.append(Particle(self.x, self.y, self.color, size, velocity))
        self.exploded = True # Indicates it's an explosion, not a rocket ascending

    def update(self):
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.lifetime > 0] # Remove dead particles

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)

# --- Game State Variables ---
game_state = "instructions_level1"
current_dialogue_target = None
dialogue_text = ""
speaker_image = None
dialogue_buttons = []

# --- Game Stats ---
player_lives = 10 
player_score = 0
player_name = "" # New: for player's name input
all_time_scores = [] # New: list to hold loaded/saved scores

# Level 2 (Object Hunt)
object_hunt_timer_initial = 30
object_hunt_timer_current = object_hunt_timer_initial
object_hunt_start_time = 0
hidden_objects = pygame.sprite.Group()
level2_completed = False 

# Level 3 (Chronological Ordering)
CHRONOLOGICAL_ORDER_NAMES = ["Juanito", "Carly", "Pedro", "Carlos"] 
LEVEL3_SLOT_Y_POSITIONS = [120, 220, 320, 420] 
LEVEL3_SLOT_X = width // 2 - (70 * 1) // 2 
level3_attempts = 3
draggable_characters = pygame.sprite.Group()
current_dragging_char = None 
level3_message = ""
level3_completed = False 

# Level 4 (Puzzle)
puzzle_pieces = pygame.sprite.Group()
puzzle_rows = 3
puzzle_cols = 3
puzzle_timer_initial = 40 # Changed to 40 seconds
puzzle_timer_current = puzzle_timer_initial
puzzle_start_time = 0
current_dragging_puzzle_piece = None 
puzzle_grid_slots = [] 
puzzle_message = ""
level4_completed = False 

# Fireworks specific
fireworks = [] 
firework_timer = 0 

# --- Questions Data (Bolivian History Examples) ---
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
        "question": "Actualmente, ¿Cuántos departamentos tiene Bolivia?",
        "correct": "9",
        "options": ["7", "8", "10"]
    },
    "Pedro": {
        "question": "¿Qué importante batalla se libró en 1824 que consolidó la independencia de Bolivia?",
        "correct": "Batalla de Ayacucho",
        "options": ["Batalla de Junín", "Batalla de Tumusla", "Batalla de Ingavi"]
    }
}

# --- Load Assets ---
personajes_group = pygame.sprite.Group() 

juanito = Personaje(150, 150, "a.png", "Juanito", scale_factor=1.5) 
carly = Personaje(450, 250, "b.png", "Carly", scale_factor=1.5) 
carlos = Personaje(600, 100, "c.png", "Carlos", scale_factor=1.5) 
pedro = Personaje(200, 400, "d.png", "Pedro", scale_factor=1.5) 
personajes_group.add(juanito, carly, carlos, pedro)

personaje_principal = Personaje(50, 50, "a.png", "Player", scale_factor=1) 
all_characters = pygame.sprite.Group(personaje_principal, *personajes_group) 

try:
    fondo = pygame.image.load("fondo.jpg").convert()
except pygame.error:
    print("Error: Could not load Overworld.png. Please ensure the file exists.")
    sys.exit()
fondo = pygame.transform.scale(fondo, (width, height))

try:
    fondoB = pygame.image.load("fondoB.jfif").convert()
except pygame.error:
    print("Error: Could not load fondoB.jpg. Please ensure the file exists and is a .jpg or .png.")
    print("If your file is fondoBq.jfif, consider converting it to .jpg or .png for better compatibility.")
    sys.exit()

fondoB_scaled = pygame.transform.scale(fondoB, (width, height)) 

dialog_box_height = height // 3
imagen_dia = pygame.image.load("dia.png").convert_alpha()
imagen_dia = pygame.transform.scale(imagen_dia, (width, dialog_box_height))

speaker_images = {
    "Juanito": pygame.image.load("a.png").convert_alpha(),
    "Carly": pygame.image.load("b.png").convert_alpha(),
    "Carlos": pygame.image.load("c.png").convert_alpha(),
    "Pedro": pygame.image.load("d.png").convert_alpha(),
    "Player": pygame.image.load("a.png").convert_alpha(),
}
for name, img_surf in speaker_images.items():
    speaker_images[name] = pygame.transform.scale(img_surf, (70, 70))


# --- Utility Functions ---
def create_puzzle_pieces(source_image_surface, rows, cols):
    pieces = pygame.sprite.Group()
    puzzle_display_width = 500
    puzzle_display_height = int(puzzle_display_width * (source_image_surface.get_height() / source_image_surface.get_width()))
    
    puzzle_source_scaled = pygame.transform.scale(source_image_surface, (puzzle_display_width, puzzle_display_height))

    piece_width = puzzle_source_scaled.get_width() // cols
    piece_height = puzzle_source_scaled.get_height() // rows

    puzzle_target_x = (width - puzzle_source_scaled.get_width()) // 2
    puzzle_target_y = (height - puzzle_source_scaled.get_height()) // 2

    global puzzle_grid_slots 
    puzzle_grid_slots = []

    for row in range(rows):
        for col in range(cols):
            x_in_image = col * piece_width
            y_in_image = row * piece_height
            
            piece_image = puzzle_source_scaled.subsurface(pygame.Rect(x_in_image, y_in_image, piece_width, piece_height))
            
            correct_screen_x = puzzle_target_x + x_in_image
            correct_screen_y = puzzle_target_y + y_in_image
            correct_pos = (correct_screen_x, correct_screen_y)

            puzzle_grid_slots.append(pygame.Rect(correct_pos[0], correct_pos[1], piece_width, piece_height))
            
            pieces.add(PuzzlePiece(piece_image, correct_pos, (0,0))) 

    center_x = width // 2
    center_y = height // 2
    
    initial_positions = []
    grid_spacing_x = piece_width + 20 
    grid_spacing_y = piece_height + 20 

    total_grid_width = cols * grid_spacing_x - 20 
    total_grid_height = rows * grid_spacing_y - 20 

    grid_start_x = center_x - total_grid_width // 2
    grid_start_y = center_y - total_grid_height // 2


    for r in range(rows):
        for c in range(cols):
            x_pos = grid_start_x + c * grid_spacing_x
            y_pos = grid_start_y + r * grid_spacing_y
            initial_positions.append((x_pos, y_pos))

    random.shuffle(initial_positions) 

    for i, piece in enumerate(pieces):
        piece.rect.topleft = initial_positions[i]

    return pieces

def load_scores():
    """Loads scores from scores.json file."""
    try:
        with open('scores.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return [] # Return empty list if file doesn't exist
    except json.JSONDecodeError:
        print("Error: scores.json is corrupted. Starting with empty scores.")
        return []

def save_scores(scores):
    """Saves scores to scores.json file."""
    with open('scores.json', 'w') as f:
        json.dump(scores, f, indent=4)

def get_player_rank(scores, current_player_score):
    """Compares current player's score to existing scores and returns their rank."""
    # Sort scores in descending order
    sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)
    
    # Find player's rank
    rank = 1
    found_player = False
    for i, entry in enumerate(sorted_scores):
        if entry['score'] > current_player_score:
            rank += 1
        elif not found_player and entry['score'] == current_player_score and entry['name'] == player_name:
            found_player = True # Mark that we found the current player's exact entry
            return rank # If current player's entry is found, return their rank
        elif not found_player and entry['score'] <= current_player_score:
             # If current player's score is equal or higher than current entry, this is their rank
            return rank

    return rank # If player's score is highest or if list is empty

def reset_game():
    global game_state, player_lives, player_score, current_dialogue_target, dialogue_text, speaker_image, dialogue_buttons
    global object_hunt_timer_current, object_hunt_start_time, hidden_objects, level2_completed
    global level3_attempts, draggable_characters, current_dragging_char, level3_message, level3_completed
    global puzzle_pieces, puzzle_timer_current, puzzle_start_time, current_dragging_puzzle_piece, puzzle_message, level4_completed
    global player_name, fireworks, firework_timer # Reset player name and fireworks

    game_state = "instructions_level1"
    player_lives = 10 
    player_score = 0 
    player_name = ""
    
    current_dialogue_target = None
    dialogue_text = ""
    speaker_image = None
    dialogue_buttons = []

    for p in personajes_group:
        p.question_asked = False
        p.attempts = 0

    object_hunt_timer_current = object_hunt_timer_initial
    object_hunt_start_time = 0
    hidden_objects.empty()
    level2_completed = False

    level3_attempts = 3
    draggable_characters.empty()
    current_dragging_char = None
    level3_message = ""
    level3_completed = False

    puzzle_pieces.empty()
    puzzle_timer_current = puzzle_timer_initial
    puzzle_start_time = 0
    current_dragging_puzzle_piece = None
    puzzle_message = ""
    level4_completed = False

    fireworks = []
    firework_timer = 0


# --- Game State Transition Functions ---
def start_level1():
    global game_state
    game_state = "exploring"

def start_level2_instructions():
    global game_state, level2_completed
    if level2_completed:
        start_level3_instructions()
        return
    game_state = "instructions_level2"

def start_object_hunt_game():
    global hidden_objects, object_hunt_start_time, game_state, object_hunt_timer_current, level2_completed
    if level2_completed:
        start_level3_instructions()
        return

    hidden_objects = pygame.sprite.Group()
    object_images = ["g.png", "h.png", "i.png", "j.png"]
    for img_path in object_images:
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        obj = HiddenObject(x, y, img_path)
        hidden_objects.add(obj)
    
    object_hunt_start_time = pygame.time.get_ticks()
    object_hunt_timer_current = object_hunt_timer_initial
    game_state = "object_hunt"

def start_level3_instructions():
    global game_state, level3_completed
    if level3_completed:
        start_level4_instructions()
        return
    game_state = "instructions_level3"

def start_level3_ordering():
    global game_state, draggable_characters, level3_attempts, level3_message, current_dragging_char, level3_completed
    if level3_completed:
        start_level4_instructions()
        return

    game_state = "level3_ordering"
    level3_attempts = 3 
    level3_message = "Haz clic para arrastrar y suelta con otro clic."
    current_dragging_char = None 

    draggable_characters.empty() 

    initial_x = 100
    initial_y_offset = 100
    char_spacing = (70 * 1) + 30 

    characters_to_order = [
        Personaje(0, 0, "a.png", "Juanito", scale_factor=1), 
        Personaje(0, 0, "b.png", "Carly", scale_factor=1), 
        Personaje(0, 0, "c.png", "Carlos", scale_factor=1), 
        Personaje(0, 0, "d.png", "Pedro", scale_factor=1)  
    ]
    random.shuffle(characters_to_order) 

    for i, char in enumerate(characters_to_order):
        char.x = initial_x
        char.y = initial_y_offset + i * char_spacing
        char.rect.topleft = (char.x, char.y) 
        draggable_characters.add(char)


def check_level3_order():
    global player_score, level3_attempts, game_state, level3_message, level3_completed, player_lives 

    sorted_chars = sorted(draggable_characters.sprites(), key=lambda char: char.y)
    current_order_names = [char.name for char in sorted_chars]

    if current_order_names == CHRONOLOGICAL_ORDER_NAMES:
        player_score += 200
        level3_message = "¡Orden Correcto! ¡Ganaste 200 puntos!"
        level3_completed = True 
        pygame.time.set_timer(pygame.USEREVENT + 2, 1500) 
    else:
        level3_attempts -= 1
        player_lives -= 2 # Deduct 2 lives for incorrect order
        level3_message = f"¡Orden Incorrecto! -2 Vidas. Intentos restantes: {level3_attempts}"
        if player_lives <= 0: # Check if lives ran out
            player_lives = 0 # Ensure it doesn't go negative
            level3_message = "¡Perdiste el nivel! Se acabaron las vidas. Reiniciando..."
            level3_completed = True # Level 3 considered "done" even if failed
            pygame.time.set_timer(pygame.USEREVENT + 3, 2000) # New: Reset game after 2 seconds
        elif level3_attempts <= 0:
            level3_message = "¡Perdiste el nivel! Se acabaron los intentos."
            level3_completed = True 
            pygame.time.set_timer(pygame.USEREVENT + 2, 1500) 
        
def start_level4_instructions():
    global game_state, level4_completed
    if level4_completed: 
        game_state = "name_input" # Changed to name input
        return
    game_state = "instructions_level4"

def start_puzzle_game():
    global game_state, puzzle_pieces, puzzle_start_time, puzzle_timer_current, puzzle_message, current_dragging_puzzle_piece, level4_completed
    if level4_completed: 
        game_state = "name_input" # Changed to name input
        return
    
    game_state = "level4_puzzle"
    puzzle_message = "Arma el rompecabezas. Haz clic para arrastrar y suelta con otro clic."
    current_dragging_puzzle_piece = None 

    puzzle_pieces = create_puzzle_pieces(fondoB, puzzle_rows, puzzle_cols) 
    puzzle_start_time = pygame.time.get_ticks()
    puzzle_timer_current = puzzle_timer_initial

def check_puzzle_completion():
    global player_score, game_state, puzzle_message, level4_completed

    all_correct = True
    for piece in puzzle_pieces:
        if not (abs(piece.rect.x - piece.correct_pos[0]) < 15 and abs(piece.rect.y - piece.correct_pos[1]) < 15):
            all_correct = False
            break
    
    if all_correct:
        player_score += 300 
        puzzle_message = "¡Rompecabezas Resuelto! ¡Ganaste 300 puntos!"
        level4_completed = True 
        pygame.time.set_timer(pygame.USEREVENT + 1, 1500) 
    else:
        pass


# --- Dialogue System Functions ---
def start_dialogue(character):
    global game_state, current_dialogue_target, dialogue_text, speaker_image, dialogue_buttons
    
    if character is None:
        return

    game_state = "dialogue"
    current_dialogue_target = character 
    speaker_image = speaker_images.get(character.name)
    dialogue_buttons = []

    if character.question_asked:
        dialogue_text = f"¡Ya me respondiste {character.name}! Gracias por tu ayuda."
        btn_ok = Button(width // 2 - 70, height - 60, 140, 40, "Ok", GREEN, BRIGHT_GREEN, end_dialogue)
        dialogue_buttons.append(btn_ok)
        return

    q_data = QUESTIONS.get(character.name)
    if q_data:
        dialogue_text = q_data["question"]
        all_answers = q_data["options"] + [q_data["correct"]]
        random.shuffle(all_answers)

        button_width = 180
        button_height = 40
        start_y_buttons = height - dialog_box_height + 80
        
        x_pos1 = (width / 2) - button_width - 10 
        x_pos2 = (width / 2) + 10 

        button_positions = []
        for i in range(len(all_answers)):
            if i % 2 == 0:
                button_positions.append((x_pos1, start_y_buttons + (i // 2) * (button_height + 10)))
            else:
                button_positions.append((x_pos2, start_y_buttons + (i // 2) * (button_height + 10)))

        for i, answer_text in enumerate(all_answers):
            x_pos, y_pos = button_positions[i]
            btn = Button(x_pos, y_pos, button_width, button_height, answer_text, BLUE, BRIGHT_BLUE, check_answer, (answer_text == q_data["correct"]))
            dialogue_buttons.append(btn)
        
        current_dialogue_target.attempts = 0

def check_answer(is_correct):
    global dialogue_text, dialogue_buttons, player_lives, player_score, game_state, level2_completed
    
    character = current_dialogue_target
    character.attempts += 1
    dialogue_buttons = []

    if is_correct:
        dialogue_text = "¡Correcto! ¡Excelente!"
        if character.attempts == 1:
            points_earned = 50
        elif character.attempts == 2:
            points_earned = 30
        else:
            points_earned = 10
        
        player_score += points_earned
        character.question_asked = True

        btn_ok = Button(width // 2 - 70, height - 60, 140, 40, "Continuar", GREEN, BRIGHT_GREEN, end_dialogue)
        dialogue_buttons.append(btn_ok)
        
        if all(p.question_asked for p in personajes_group):
            dialogue_text = "¡Has completado el Nivel 1! Preparando el siguiente..."
            dialogue_buttons = [] 
            level2_completed = False 
            pygame.time.set_timer(pygame.USEREVENT + 2, 1500) 

    else:
        dialogue_text = "Incorrecto. Intenta de nuevo."
        player_lives -= 1 
        player_score -= 30 
        
        if player_lives <= 0: 
            player_lives = 0
            dialogue_text = "¡Incorrecto! No te quedan vidas. Game Over."
            btn_ok = Button(width // 2 - 70, height - 60, 140, 40, "Reiniciar", RED, BRIGHT_RED, reset_game)
            dialogue_buttons.append(btn_ok)
        else:
            q_data = QUESTIONS.get(character.name)
            if q_data:
                all_answers = q_data["options"] + [q_data["correct"]]
                random.shuffle(all_answers)

                button_width = 180
                button_height = 40
                start_y_buttons = height - dialog_box_height + 80
                
                x_pos1 = (width / 2) - button_width - 10 
                x_pos2 = (width / 2) + 10 

                button_positions = []
                for i in range(len(all_answers)):
                    if i % 2 == 0:
                        button_positions.append((x_pos1, start_y_buttons + (i // 2) * (button_height + 10)))
                    else:
                        button_positions.append((x_pos2, start_y_buttons + (i // 2) * (button_height + 10)))

                for i, answer_text in enumerate(all_answers):
                    x_pos, y_pos = button_positions[i]
                    btn = Button(x_pos, y_pos, button_width, button_height, answer_text, BLUE, BRIGHT_BLUE, check_answer, (answer_text == q_data["correct"]))
                    dialogue_buttons.append(btn)

def end_dialogue():
    global game_state, current_dialogue_target, dialogue_text, speaker_image, dialogue_buttons
    game_state = "exploring"
    current_dialogue_target = None 
    dialogue_text = ""
    speaker_image = None
    dialogue_buttons = []

# --- Main Game Loop ---
running = True
# Load scores at the start of the game
all_time_scores = load_scores()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if event.type == pygame.USEREVENT + 1: # Transition to name input from game end (puzzle complete/timer out)
            game_state = "name_input"
            pygame.time.set_timer(pygame.USEREVENT + 1, 0) # Stop the timer

        if event.type == pygame.USEREVENT + 2: # Level completion transitions
            if game_state == "dialogue" and all(p.question_asked for p in personajes_group):
                start_level2_instructions()
            elif game_state == "object_hunt" and (not hidden_objects or object_hunt_timer_current <= 0): 
                start_level3_instructions()
            elif game_state == "level3_ordering" and level3_completed:
                start_level4_instructions() 
            pygame.time.set_timer(pygame.USEREVENT + 2, 0) 
        
        if event.type == pygame.USEREVENT + 3: # Reset game due to lives depleted
            reset_game()
            pygame.time.set_timer(pygame.USEREVENT + 3, 0) # Stop the timer


        if event.type == pygame.KEYDOWN:
            if game_state == "instructions_level1":
                if event.key == pygame.K_SPACE:
                    start_level1()
            elif game_state == "exploring":
                if event.key == pygame.K_a:
                    if current_dialogue_target and game_state != "dialogue":
                        start_dialogue(current_dialogue_target)
            elif game_state == "instructions_level2":
                if event.key == pygame.K_SPACE:
                    start_object_hunt_game()
            elif game_state == "instructions_level3":
                if event.key == pygame.K_SPACE:
                    start_level3_ordering()
            elif game_state == "level3_ordering":
                if event.key == pygame.K_v: 
                    if not current_dragging_char: 
                        check_level3_order()
            elif game_state == "instructions_level4":
                if event.key == pygame.K_SPACE:
                    start_puzzle_game()
            elif game_state == "name_input":
                if event.key == pygame.K_RETURN:
                    if player_name.strip(): # Only proceed if name is not empty
                        all_time_scores.append({"name": player_name, "score": player_score})
                        save_scores(all_time_scores)
                        game_state = "final_scoreboard"
                    else:
                        # Optionally, show a message that name cannot be empty
                        pass 
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    if len(player_name) < 15: # Limit name length
                        player_name += event.unicode


            if event.key == pygame.K_q:
                running = False 

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if event.button == 1: 
                if game_state == "dialogue":
                    for button in dialogue_buttons:
                        if button.handle_event(event):
                            break
                elif game_state == "object_hunt":
                    for obj in hidden_objects:
                        if obj.rect.collidepoint(mouse_x, mouse_y) and not obj.found:
                            obj.found = True
                            player_score += 25
                            hidden_objects.remove(obj)
                            if not hidden_objects: 
                                level2_completed = True 
                                pygame.time.set_timer(pygame.USEREVENT + 2, 1500) 
                                break 

                elif game_state == "level3_ordering":
                    if current_dragging_char is None: 
                        for char in draggable_characters:
                            if char.rect.collidepoint(mouse_x, mouse_y):
                                current_dragging_char = char
                                char.start_drag((mouse_x, mouse_y))
                                break
                    else: 
                        current_dragging_char.stop_drag()
                        current_dragging_char = None

                elif game_state == "level4_puzzle":
                    if current_dragging_puzzle_piece is None: 
                        for piece in puzzle_pieces:
                            if piece.rect.collidepoint(mouse_x, mouse_y):
                                current_dragging_puzzle_piece = piece
                                piece.start_drag((mouse_x, mouse_y))
                                break
                    else: 
                        current_dragging_puzzle_piece.stop_drag()
                        current_dragging_puzzle_piece.snap_to_grid(puzzle_grid_slots) 
                        current_dragging_puzzle_piece = None
                        check_puzzle_completion() 
                elif game_state == "final_scoreboard":
                    # Handle buttons on scoreboard
                    for button in [btn_quit_game, btn_restart_game]:
                        if button.rect.collidepoint(mouse_x, mouse_y):
                            button.handle_event(event)


    # --- Game Logic ---
    if game_state == "exploring":
        keys = pygame.key.get_pressed()
        move_speed = 8
        if keys[pygame.K_LEFT]:
            personaje_principal.x -= move_speed
        if keys[pygame.K_RIGHT]:
            personaje_principal.x += move_speed
        if keys[pygame.K_UP]:
            personaje_principal.y -= move_speed
        if keys[pygame.K_DOWN]:
            personaje_principal.y += move_speed

        personaje_principal.x = max(0, min(personaje_principal.x, width - personaje_principal.image.get_width()))
        personaje_principal.y = max(0, min(personaje_principal.y, height - personaje_principal.image.get_height()))

        for p in all_characters:
            p.update()

        current_dialogue_target = None 
        PROXIMITY_DISTANCE = 120 
        for personaje in personajes_group:
            distance = pygame.math.Vector2(personaje_principal.rect.center).distance_to(personaje.rect.center)
            if distance < PROXIMITY_DISTANCE:
                current_dialogue_target = personaje
                break 

    elif game_state == "level3_ordering":
        if current_dragging_char:
            current_dragging_char.do_drag(pygame.mouse.get_pos())
            
    elif game_state == "object_hunt":
        time_elapsed_ms = pygame.time.get_ticks() - object_hunt_start_time
        time_remaining_seconds = max(0, object_hunt_timer_initial - (time_elapsed_ms // 1000))
        object_hunt_timer_current = time_remaining_seconds

        if time_remaining_seconds <= 0 and not level2_completed: 
            level2_completed = True 
            pygame.time.set_timer(pygame.USEREVENT + 2, 1500) 
    
    elif game_state == "level4_puzzle":
        time_elapsed_ms = pygame.time.get_ticks() - puzzle_start_time
        time_remaining_seconds = max(0, puzzle_timer_initial - (time_elapsed_ms // 1000))
        puzzle_timer_current = time_remaining_seconds

        if current_dragging_puzzle_piece:
            current_dragging_puzzle_piece.do_drag(pygame.mouse.get_pos())

        if time_remaining_seconds <= 0 and not level4_completed: 
            puzzle_message = "¡Tiempo agotado! Rompecabezas no completado."
            player_score -= 200 
            level4_completed = True 
            pygame.time.set_timer(pygame.USEREVENT + 1, 1500) # Transition to name input


    elif game_state == "final_scoreboard":
        # Update fireworks
        firework_timer += 1
        if firework_timer % 30 == 0: 
            x = random.randint(100, width - 100)
            y = random.randint(100, height - 100)
            color = random.choice(FIREWORK_COLORS)
            fireworks.append(Firework(x, y, color))
        
        for fw in fireworks:
            fw.update()
        fireworks = [fw for fw in fireworks if fw.particles] 


    # --- Drawing ---
    screen.fill(BLACK) 

    if game_state == "instructions_level1":
        title_surf = font_title.render("¡Bienvenido al Trivia de Bolivia!", True, WHITE)
        instructions_line1 = font_instructions.render("Este es un trivia. Debes responder las preguntas", True, WHITE)
        instructions_line2 = font_instructions.render("de todos los personajes.", True, WHITE)
        instructions_line3 = font_instructions.render("Presiona 'A' para interactuar con ellos.", True, WHITE)
        start_prompt = font_instructions.render("Presiona ESPACIO para empezar", True, YELLOW)

        title_rect = title_surf.get_rect(center=(width // 2, height // 2 - 150))
        line1_rect = instructions_line1.get_rect(center=(width // 2, height // 2 - 50))
        line2_rect = instructions_line2.get_rect(center=(width // 2, height // 2 - 20))
        line3_rect = instructions_line3.get_rect(center=(width // 2, height // 2 + 10))
        start_rect = start_prompt.get_rect(center=(width // 2, height // 2 + 100))

        screen.blit(title_surf, title_rect)
        screen.blit(instructions_line1, line1_rect)
        screen.blit(instructions_line2, line2_rect)
        screen.blit(instructions_line3, line3_rect)
        screen.blit(start_prompt, start_rect)

    elif game_state == "instructions_level2":
        screen.blit(fondoB_scaled, (0, 0)) 
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        screen.blit(overlay, (0, 0))

        title_surf = font_title.render("¡Llegaste al Nivel 2!", True, WHITE)
        instructions_line1 = font_instructions.render("Ahora debes encontrar todos los objetos perdidos.", True, WHITE)
        instructions_line2 = font_instructions.render(f"¡El tiempo corre! Tienes {object_hunt_timer_initial} segundos.", True, WHITE)
        instructions_line3 = font_instructions.render(f"Tus puntos y vidas se mantienen: Puntos {player_score}, Vidas {max(0, player_lives)}", True, YELLOW)
        start_prompt = font_instructions.render("Presiona ESPACIO para empezar", True, BRIGHT_GREEN)

        title_rect = title_surf.get_rect(center=(width // 2, height // 2 - 150))
        line1_rect = instructions_line1.get_rect(center=(width // 2, height // 2 - 50))
        line2_rect = instructions_line2.get_rect(center=(width // 2, height // 2 - 20))
        line3_rect = instructions_line3.get_rect(center=(width // 2, height // 2 + 30))
        start_rect = start_prompt.get_rect(center=(width // 2, height // 2 + 120))

        screen.blit(title_surf, title_rect)
        screen.blit(instructions_line1, line1_rect)
        screen.blit(instructions_line2, line2_rect)
        screen.blit(instructions_line3, line3_rect)
        screen.blit(start_prompt, start_rect)

    elif game_state == "instructions_level3":
        screen.blit(fondoB_scaled, (0, 0)) 
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        screen.blit(overlay, (0, 0))

        title_surf = font_title.render("¡Llegaste al Nivel 3!", True, WHITE)
        instructions_line1 = font_instructions.render("Ahora debes ordenar los personajes cronológicamente.", True, WHITE)
        instructions_line2 = font_instructions.render("Haz clic sobre un personaje para arrastrarlo.", True, WHITE)
        instructions_line3 = font_instructions.render("Haz clic de nuevo para soltarlo.", True, WHITE)
        instructions_line4 = font_instructions.render("Cuando creas que están correctos, presiona 'V' para verificar.", True, WHITE)
        instructions_line5 = font_instructions.render(f"Tienes {level3_attempts} intentos. ¡Mucha suerte!", True, YELLOW)
        start_prompt = font_instructions.render("Presiona ESPACIO para empezar", True, BRIGHT_GREEN)

        title_rect = title_surf.get_rect(center=(width // 2, height // 2 - 150))
        line1_rect = instructions_line1.get_rect(center=(width // 2, height // 2 - 50))
        line2_rect = instructions_line2.get_rect(center=(width // 2, height // 2 - 20))
        line3_rect = instructions_line3.get_rect(center=(width // 2, height // 2 + 10))
        line4_rect = instructions_line4.get_rect(center=(width // 2, height // 2 + 40))
        line5_rect = instructions_line5.get_rect(center=(width // 2, height // 2 + 70))
        start_rect = start_prompt.get_rect(center=(width // 2, height // 2 + 140))

        screen.blit(title_surf, title_rect)
        screen.blit(instructions_line1, line1_rect)
        screen.blit(instructions_line2, line2_rect)
        screen.blit(instructions_line3, line3_rect)
        screen.blit(instructions_line4, line4_rect)
        screen.blit(instructions_line5, line5_rect)
        screen.blit(start_prompt, start_rect)

    elif game_state == "instructions_level4":
        screen.blit(fondoB_scaled, (0, 0)) 
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill(TRANSPARENT_BLACK)
        screen.blit(overlay, (0, 0))

        title_surf = font_title.render("¡Llegaste al Nivel 4!", True, WHITE)
        instructions_line1 = font_instructions.render("Ahora debes armar un rompecabezas.", True, WHITE)
        instructions_line2 = font_instructions.render("Haz clic sobre una pieza para arrastrarla.", True, WHITE)
        instructions_line3 = font_instructions.render("Haz clic de nuevo para soltarla.", True, WHITE)
        instructions_line4 = font_instructions.render(f"Tienes {puzzle_timer_initial} segundos para completarlo.", True, YELLOW)
        instructions_line5 = font_instructions.render("Si lo logras, ¡ganarás 300 puntos extra!", True, YELLOW)
        start_prompt = font_instructions.render("Presiona ESPACIO para empezar", True, BRIGHT_GREEN)

        title_rect = title_surf.get_rect(center=(width // 2, height // 2 - 150))
        line1_rect = instructions_line1.get_rect(center=(width // 2, height // 2 - 50))
        line2_rect = instructions_line2.get_rect(center=(width // 2, height // 2 - 20))
        line3_rect = instructions_line3.get_rect(center=(width // 2, height // 2 + 10))
        line4_rect = instructions_line4.get_rect(center=(width // 2, height // 2 + 40))
        line5_rect = instructions_line5.get_rect(center=(width // 2, height // 2 + 70))
        start_rect = start_prompt.get_rect(center=(width // 2, height // 2 + 140))

        screen.blit(title_surf, title_rect)
        screen.blit(instructions_line1, line1_rect)
        screen.blit(instructions_line2, line2_rect)
        screen.blit(instructions_line3, line3_rect)
        screen.blit(instructions_line4, line4_rect)
        screen.blit(instructions_line5, line5_rect)
        screen.blit(start_prompt, start_rect)


    elif game_state == "exploring" or game_state == "dialogue":
        screen.blit(fondo, (0, 0)) 
        all_characters.draw(screen) 

        lives_text_surf = font_ui.render(f"Vidas: {max(0, player_lives)}", True, YELLOW)
        screen.blit(lives_text_surf, (10, 10))

        score_text_surf = font_ui.render(f"Puntos: {player_score}", True, YELLOW)
        screen.blit(score_text_surf, (width - score_text_surf.get_width() - 10, 10))

        if game_state == "dialogue":
            dialog_box_y = height - dialog_box_height
            screen.blit(imagen_dia, (0, dialog_box_y))

            text_surface = font_dialogue_text.render(dialogue_text, True, BLACK)
            text_x = width // 2 - text_surface.get_width() // 2
            text_y = dialog_box_y + 20
            screen.blit(text_surface, (text_x, text_y))

            if speaker_image:
                screen.blit(speaker_images[current_dialogue_target.name], (width - speaker_images[current_dialogue_target.name].get_width() - 10, dialog_box_y + 10))

            for button in dialogue_buttons:
                button.draw(screen)

    elif game_state == "object_hunt":
        screen.blit(fondoB_scaled, (0, 0)) 
        screen.blit(personaje_principal.image, personaje_principal.rect) 
        hidden_objects.draw(screen) 

        timer_text_surf = font_timer.render(f"Tiempo: {object_hunt_timer_current}", True, YELLOW)
        screen.blit(timer_text_surf, (width // 2 - timer_text_surf.get_width() // 2, 20))
        
        score_text_surf = font_ui.render(f"Puntos: {player_score}", True, YELLOW)
        screen.blit(score_text_surf, (width - score_text_surf.get_width() - 10, 10))

    elif game_state == "level3_ordering":
        screen.blit(fondoB_scaled, (0, 0)) 

        for i, y_pos in enumerate(LEVEL3_SLOT_Y_POSITIONS):
            slot_rect = pygame.Rect(LEVEL3_SLOT_X, y_pos, 70 * 1, 70 * 1) 
            pygame.draw.rect(screen, DARK_GRAY, slot_rect, 2) 
            num_surf = font_instructions.render(str(i + 1), True, WHITE)
            num_rect = num_surf.get_rect(center=(LEVEL3_SLOT_X + (70*1)//2, y_pos - 20))
            screen.blit(num_surf, num_rect)

        draggable_characters.draw(screen) 

        message_surf = font_level_message.render(level3_message, True, ORANGE)
        message_rect = message_surf.get_rect(center=(width // 2, height - 50))
        screen.blit(message_surf, message_rect)

        lives_text_surf = font_ui.render(f"Vidas: {max(0, player_lives)}", True, YELLOW)
        screen.blit(lives_text_surf, (10, 10))
        score_text_surf = font_ui.render(f"Puntos: {player_score}", True, YELLOW)
        screen.blit(score_text_surf, (width - score_text_surf.get_width() - 10, 10))
        attempts_text_surf = font_ui.render(f"Intentos: {level3_attempts}", True, YELLOW)
        screen.blit(attempts_text_surf, (10, 50))

    elif game_state == "level4_puzzle":
        screen.blit(fondoB_scaled, (0,0))
        
        if puzzle_grid_slots: 
            puzzle_bg_rect = pygame.Rect(puzzle_grid_slots[0].topleft, 
                                        (puzzle_grid_slots[-1].right - puzzle_grid_slots[0].left, 
                                        puzzle_grid_slots[-1].bottom - puzzle_grid_slots[0].top))
            pygame.draw.rect(screen, WHITE, puzzle_bg_rect)

        for slot_rect in puzzle_grid_slots:
            pygame.draw.rect(screen, DARK_GRAY, slot_rect, 2) 

        puzzle_pieces.draw(screen) 

        timer_text_surf = font_timer.render(f"Tiempo: {puzzle_timer_current}", True, BLACK) 
        screen.blit(timer_text_surf, (width // 2 - timer_text_surf.get_width() // 2, 20))

        message_surf = font_level_message.render(puzzle_message, True, ORANGE)
        message_rect = message_surf.get_rect(center=(width // 2, height - 50))
        screen.blit(message_surf, message_rect)

        lives_text_surf = font_ui.render(f"Vidas: {max(0, player_lives)}", True, BLACK)
        screen.blit(lives_text_surf, (10, 10))
        score_text_surf = font_ui.render(f"Puntos: {player_score}", True, BLACK)
        screen.blit(score_text_surf, (width - score_text_surf.get_width() - 10, 10))
    
    elif game_state == "name_input":
        screen.fill(BLACK)
        prompt_surf = font_title.render("¡Juego Terminado!", True, WHITE)
        prompt_rect = prompt_surf.get_rect(center=(width // 2, height // 2 - 100))
        screen.blit(prompt_surf, prompt_rect)

        name_prompt = font_input.render("Ingresa tu nombre:", True, WHITE)
        name_prompt_rect = name_prompt.get_rect(center=(width // 2, height // 2 - 20))
        screen.blit(name_prompt, name_prompt_rect)

        # Draw the input box
        input_box = pygame.Rect(width // 2 - 150, height // 2 + 30, 300, 50)
        pygame.draw.rect(screen, LIGHT_GRAY, input_box)
        pygame.draw.rect(screen, WHITE, input_box, 3) # Border

        name_surf = font_input.render(player_name, True, BLACK)
        name_rect = name_surf.get_rect(midleft=(input_box.x + 10, input_box.centery))
        screen.blit(name_surf, name_rect)

        # Indicate input with cursor
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_pos = name_rect.topright[0] if player_name else input_box.x + 10
            pygame.draw.line(screen, BLACK, (cursor_pos, input_box.centery - 15), (cursor_pos, input_box.centery + 15), 2)
        
        enter_prompt = font_instructions.render("Presiona ENTER para continuar", True, YELLOW)
        enter_rect = enter_prompt.get_rect(center=(width // 2, height // 2 + 120))
        screen.blit(enter_prompt, enter_rect)


    elif game_state == "final_scoreboard":
        screen.fill(BLACK) 
        for fw in fireworks:
            fw.draw(screen)

        overlay_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay_surf.fill(TRANSPARENT_BLACK) 
        screen.blit(overlay_surf, (0, 0))

        score_title_surf = font_title.render("¡Resultados Finales!", True, WHITE)
        score_val_surf = font_ui.render(f"Tu Puntuación: {player_score} puntos", True, YELLOW)
        
        title_rect = score_title_surf.get_rect(center=(width // 2, 50))
        score_rect = score_val_surf.get_rect(center=(width // 2, 100))

        screen.blit(score_title_surf, title_rect)
        screen.blit(score_val_surf, score_rect)

        # Display ranking
        display_scores = sorted(all_time_scores, key=lambda x: x['score'], reverse=True)[:10] # Top 10 scores
        
        scoreboard_y_start = 150
        screen.blit(font_ui.render("--- Mejores Puntuaciones ---", True, WHITE), (width // 2 - 150, scoreboard_y_start))
        
        for i, entry in enumerate(display_scores):
            score_line = f"{i+1}. {entry['name']}: {entry['score']}"
            score_line_surf = font_ui.render(score_line, True, WHITE)
            screen.blit(score_line_surf, (width // 2 - score_line_surf.get_width() // 2, scoreboard_y_start + 40 + i * 30))

        # Show player's rank
        current_rank = get_player_rank(all_time_scores, player_score)
        rank_message_surf = font_ui.render(f"¡Quedaste en el puesto: #{current_rank}!", True, BRIGHT_GREEN)
        screen.blit(rank_message_surf, (width // 2 - rank_message_surf.get_width() // 2, scoreboard_y_start + 40 + len(display_scores) * 30 + 30))


        btn_quit_game = Button(width // 2 - 70, height - 100, 140, 50, "Salir (Q)", RED, BRIGHT_RED, sys.exit)
        btn_quit_game.draw(screen)

        btn_restart_game = Button(width // 2 - 70, height - 40, 140, 50, "Reiniciar", BLUE, BRIGHT_BLUE, reset_game)
        btn_restart_game.draw(screen)


    pygame.display.flip()
    pygame.time.Clock().tick(30)

pygame.quit()
sys.exit()