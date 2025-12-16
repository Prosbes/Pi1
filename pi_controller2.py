import requests
import time
import pygame

# Mappningskonstanter för joysticken
# Vi antar att den vänstra/högra stickan (eller den enda stickan) 
# har Longitud (vänster/höger) på axel 0 och Latitud (framåt/bakåt) på axel 1.
AXIS_LONGITUDE = 0  # X-axel (Vänster/Höger)
AXIS_LATITUDE = 1   # Y-axel (Framåt/Bakåt)
DEADZONE = 0.1      # Ignorera små rörelser nära mitten (undviker "drift")
POLL_RATE = 0.05    # Hur ofta loopen ska köras (i sekunder, 20 gånger per sekund)

def initialize_joystick():
    """Initierar Pygame och letar efter en ansluten joystick."""
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("Fel: Ingen joystick hittades. Se till att den är ansluten.")
        return None

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Joystick hittad: {joystick.get_name()}. Redo för rörelsekontroll.")
    return joystick

def get_joystick_movement(joystick):
    """
    Läser axelvärden från joysticken och returnerar longitud och latitud.
    """
    # Pygame kräver att händelser hanteras för att uppdatera axeldata
    pygame.event.pump()
    
    d_long = 0
    d_la = 0
    send_vel = False

    try:
        long_val = joystick.get_axis(AXIS_LONGITUDE)
        la_val = joystick.get_axis(AXIS_LATITUDE)
        
        # 1. Kontrollera Longitud (X-axel)
        if abs(long_val) > DEADZONE:
            # Värdet avrundas till -1 (Vänster) eller 1 (Höger)
            d_long = round(long_val) 
            send_vel = True
        
        # 2. Kontrollera Latitud (Y-axel)
        if abs(la_val) > DEADZONE:
            # OBS: Många joysticks ger negativt värde när man trycker framåt.
            # Vi vänder tecknet för att 'Framåt' ska bli +1 i 'd_la'.
            d_la = round(-la_val) 
            send_vel = True

    except pygame.error as e:
        # Detta fångar fel om axelindex är ogiltigt (t.ex. om joystick saknar axel 1)
        print(f"Fel vid läsning av joystick-axel: {e}")
        d_long, d_la, send_vel = 0, 0, False

    return d_long, d_la, send_vel


if __name__ == "__main__":
    SERVER_URL = "http://127.0.0.1:5000/drone"
    
    drone_joystick = initialize_joystick()
    
    if drone_joystick is None:
        exit()
        
    print(f"Startar kontroll-loop. Skickar data till {SERVER_URL}")

    while True:
        d_long, d_la, send_vel = get_joystick_movement(drone_joystick)

        if send_vel:
            # Skickar Longitud och Latitud om spaken är utanför dödzonen
            with requests.Session() as session:
                movement_command = {'longitude': d_long,
                                    'latitude': d_la
                                    }
                try:
                    # Timeout är viktigt för att programmet inte ska frysa om servern inte svarar
                    session.post(SERVER_URL, json=movement_command, timeout=0.1)
                    # Du kan lägga till en print(f"Skickat: {movement_command}") här för debugging
                except requests.exceptions.RequestException as e:
                    print(f"Kunde inte ansluta/skicka till servern: {e}")
            
        time.sleep(POLL_RATE)