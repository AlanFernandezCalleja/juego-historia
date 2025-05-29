import pygame
import sys
import pygame.mixer

# Inicialización de Pygame
pygame.init()
pygame.mixer.init()

# Tamaño de la pantalla
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Proyecto de lectricidad y electromagnetismo")
# Cargar música de fondo
pygame.mixer.music.load("f.mp3")

# Reproducir música en bucle
pygame.mixer.music.play(-1)  # El argumento -1 indica reproducción en bucle

# Clase para el personaje
class Personaje:
    def __init__(self, x, y, image_path):
        self.x = x
        self.y = y
        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()
class Personaje4(Personaje):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path)
        self.hola_dicho = False  # Variable para controlar si ya dijo "Hola, soy Pedro"
        self.divisor_voltaje_calculado = False  # Variable para controlar si se calculó el divisor de voltaje
        self.divisor_corriente_calculado = False  # Variable para controlar si se calculó el divisor de corriente
        self.resistencias = []
# Lista de personajes
personajes = [
    Personaje(100, 200, "a.png"),  # Personaje secundario a.png
    Personaje(300, 300, "b.png"),  # Personaje secundario b.png
    Personaje(500, 400, "c.png"),  # Personaje secundario c.png
    Personaje(700, 500, "d.png"),  # Personaje secundario d.png
    
]

# Personaje principal
personaje_principal = Personaje(50, 50, "a.png")
personaje4 = Personaje4(700, 500, "d.png")
# Cargar imagen de fondo
fondo = pygame.image.load("fondo.jpg")

# Cargar imagen del día
imagen_dia = pygame.image.load("dia.png")
imagen_dia = pygame.transform.scale(imagen_dia, (width, height // 3))  # Tercio inferior de la pantalla

# Fuentes para el texto
font_grande = pygame.font.SysFont("timesnewroman", 36)
font_pequeno = pygame.font.SysFont("timesnewroman", 24)

# Imágenes para colocar en la esquina inferior derecha
imagen_a = pygame.image.load("a.png")
imagen_b = pygame.image.load("b.png")
imagen_c = pygame.image.load("c.png")
imagen_d = pygame.image.load("d.png")

# Variables para controlar la visibilidad de la imagen y el texto del día
mostrar_dia = False
primer_apretar_a = True  # Variable para controlar la primera vez que se aprieta 'a'
primer_apretar_b = True  # Variable para controlar la primera vez que se aprieta 'b'
texto_dia = ""
imagen_esquina = None

# Funciones para calcular la ley de Ohm
def calcular_voltaje(corriente, resistencia):
    return corriente * resistencia

def calcular_corriente(voltaje, resistencia):
    return voltaje / resistencia

def calcular_resistencia(voltaje, corriente):
    return voltaje / corriente
# Constantes de resistividad para diferentes materiales
RESISTIVIDAD_MATERIALES = {
    "Cobre": 1.68e-8,
    "Aluminio": 2.82e-8,
    "Oro": 2.44e-8,
    "Plata": 1.59e-8,
    "Hierro": 9.71e-8,
    "Plomo": 2.05e-7,
    "Zinc": 5.90e-7,
    "Silicio": 6e2,
    "Germanio": 4e2,
    "Vidrio": 1e12,
    "Teflón": 2e22,
}

# Bucle principal del juego
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                if primer_apretar_a:
                    mostrar_dia = True
                    texto_dia = "Hola soy Juanito y hago ley de Ohm."
                    imagen_esquina = imagen_a
                    primer_apretar_a = False
                else:
                    mostrar_dia = not mostrar_dia
                    if mostrar_dia:
                        texto_dia = "¿Qué quieres calcular? Presiona V para voltaje, I para corriente y R para resistencia."

            if event.key == pygame.K_b:
                if primer_apretar_b:
                    mostrar_dia = True
                    texto_dia = "Hola soy Carly. Puedo calcular la resistividad de un objeto."
                    imagen_esquina = imagen_b
                    primer_apretar_b = False
                else:
                    mostrar_dia = not mostrar_dia
                    if mostrar_dia:
                        # Pedir el material
                        material = input("Introduce el material (Cobre, Aluminio, Oro, Plata, Hierro, Plomo, Zinc, Silicio, Germanio, Vidrio, Teflón): ").capitalize()

                        # Verificar si el material está en la lista y asignar su resistividad
                        if material in RESISTIVIDAD_MATERIALES:
                            p = RESISTIVIDAD_MATERIALES[material]

                            # Pedir valores de longitud y área
                            longitud = float(input("Introduce la longitud del objeto: "))
                            area = float(input("Introduce el área transversal del objeto: "))

                            # Calcular resistividad
                            resistividad = p * (longitud / area)

                            texto_dia = f"La resistividad del objeto es: {resistividad:.2e} ohmios·metro."
                        else:
                            texto_dia = "Material no reconocido."
                            
            if event.key == pygame.K_d:
                if not personaje4.hola_dicho:
                    mostrar_dia = True
                    texto_dia = "Hola, soy Pedro. Puedo calcular el divisor de voltaje y el divisor de corriente."
                    personaje4.hola_dicho = True
                    imagen_esquina = imagen_d
                else:
                    mostrar_dia = not mostrar_dia
                    if mostrar_dia:
                        texto_dia = "Presiona B para calcular el divisor de voltaje o Y para calcular el divisor de corriente."

            if event.key == pygame.K_b and personaje4.hola_dicho and not personaje4.divisor_voltaje_calculado:
                num_resistencias = int(input("Ingrese el número de resistencias en el divisor de voltaje: "))
                personaje4.resistencias = [float(input(f"Ingrese el valor de la resistencia {i + 1}: ")) for i in range(num_resistencias)]
                voltaje_entrada = float(input("Ingrese el voltaje de entrada: "))
                resistencia_calculada = int(input("Ingrese el número de la resistencia para hallar su voltaje: ")) - 1

                suma_resistencias = sum(personaje4.resistencias)
                voltaje_resistencia = (personaje4.resistencias[resistencia_calculada] / suma_resistencias) * voltaje_entrada
                texto_dia = f"El voltaje en la resistencia {resistencia_calculada + 1} es de: {voltaje_resistencia:.2f} voltios."
                personaje4.divisor_voltaje_calculado = True

            if event.key == pygame.K_y and personaje4.hola_dicho and not personaje4.divisor_corriente_calculado:
                num_resistencias = int(input("Ingrese el número de resistencias en paralelo: "))
                personaje4.resistencias = [float(input(f"Ingrese el valor de la resistencia {i + 1}: ")) for i in range(num_resistencias)]
                corriente_total = float(input("Ingrese la corriente total: "))
                resistencia_calculada = int(input("Ingrese el número de la resistencia para calcular su corriente: ")) - 1

                suma_resistencias = sum(1 / r for r in personaje4.resistencias)
                corriente_resistencia = (1 / personaje4.resistencias[resistencia_calculada] / suma_resistencias) * corriente_total
                texto_dia = f"La corriente en la resistencia {resistencia_calculada + 1} es de: {corriente_resistencia:.2f} amperios."
                personaje4.divisor_corriente_calculado = True

            if event.key == pygame.K_q:
                mostrar_dia = False
                primer_apretar_a = True
                primer_apretar_b = True
                texto_dia = ""
                imagen_esquina = None

            if mostrar_dia and event.key in [pygame.K_v, pygame.K_i, pygame.K_r]:
                tipo_calculo = ""
                if event.key == pygame.K_v:
                    tipo_calculo = "V"
                elif event.key == pygame.K_i:
                    tipo_calculo = "I"
                elif event.key == pygame.K_r:
                    tipo_calculo = "R"
                
                pygame.event.clear()  # Limpiar eventos para evitar que se acumulen al esperar la entrada del usuario

                if tipo_calculo == "V":
                    corriente = float(input("Ingrese la corriente (I): "))
                    resistencia = float(input("Ingrese la resistencia (R): "))
                    resultado = calcular_voltaje(corriente, resistencia)
                    texto_dia = f"V = R * I\nEl voltaje es de: {resultado} voltios."
                elif tipo_calculo == "I":
                    voltaje = float(input("Ingrese el voltaje (V): "))
                    resistencia = float(input("Ingrese la resistencia (R): "))
                    resultado = calcular_corriente(voltaje, resistencia)
                    texto_dia = f"I = V / R\nLa corriente es de: {resultado} amperios."
                elif tipo_calculo == "R":
                    voltaje = float(input("Ingrese el voltaje (V): "))
                    corriente = float(input("Ingrese la corriente (I): "))
                    resultado = calcular_resistencia(voltaje, corriente)
                    texto_dia = f"R = V / I\nLa resistencia es de: {resultado} ohmios."

                imagen_esquina = None

    # Lógica del juego
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        personaje_principal.x -= 5
    if keys[pygame.K_RIGHT]:
        personaje_principal.x += 5
    if keys[pygame.K_UP]:
        personaje_principal.y -= 5
    if keys[pygame.K_DOWN]:
        personaje_principal.y += 5

    # Dibujar fondo
    screen.blit(fondo, (0, 0))

    # Dibujar personajes
    for personaje in personajes:
        screen.blit(personaje.image, (personaje.x, personaje.y))
    
    # Dibujar personaje principal
    screen.blit(personaje_principal.image, (personaje_principal.x, personaje_principal.y))

    # Verificar interacción con personajes
    for personaje in personajes:
        distancia = pygame.math.Vector2(personaje_principal.rect.center).distance_to(personaje.rect.center)
        if distancia < 100:
            if mostrar_dia:
                # Dibujar imagen del día en el tercio inferior
                screen.blit(imagen_dia, (0, height * 2 // 3))
                # Dibujar texto del día más abajo
                if "Juanito" in texto_dia:
                    # Si es el primer diálogo de Juanito, usar una fuente más pequeña
                    texto = font_pequeno.render(texto_dia, True, (0, 0, 0))
                else:
                    texto = font_grande.render(texto_dia, True, (0, 0, 0))
                screen.blit(texto, (width // 2 - texto.get_width() // 2, height * 5 // 6))
                # Dibujar imagen en la esquina inferior derecha
                if imagen_esquina is not None:
                    screen.blit(imagen_esquina, (width - imagen_esquina.get_width(), height - imagen_esquina.get_height()))

    # Actualizar la pantalla
    pygame.display.flip()

    # Controlar la velocidad del bucle
    pygame.time.Clock().tick(30)
