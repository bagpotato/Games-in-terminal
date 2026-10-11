#!/usr/bin/env python3
import math
import os
import random
import shutil
import sys
import time
from collections import deque
from contextlib import contextmanager

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty


# ---------- terminal ----------

def color(t, c):
    return f"\x1b[{c}m{t}\x1b[0m"


def draw(lineas):
    sys.stdout.write("\x1b[H" + "".join(l + "\x1b[K\n" for l in lineas) + "\x1b[J")
    sys.stdout.flush()


def clear():
    sys.stdout.write("\x1b[2J\x1b[H")


def caja(filas, ancho):
    return ["┌" + "─" * ancho + "┐"] + ["│" + f + "│" for f in filas] + ["└" + "─" * ancho + "┘"]


TECLAS_WIN = {"H": "up", "P": "down", "K": "left", "M": "right"}
TECLAS_ANSI = {b"[A": "up", b"[B": "down", b"[C": "right", b"[D": "left",
               b"OA": "up", b"OB": "down", b"OC": "right", b"OD": "left"}
ESPECIALES = {"\r": "enter", "\n": "enter", " ": "space", "\x1b": "esc",
              "\x7f": "backspace", "\x08": "backspace"}


def normalizar(ch):
    if ch == "\x03":
        raise KeyboardInterrupt
    return ESPECIALES.get(ch, ch.lower())


def key(timeout=None):
    """Devuelve una tecla, o None si pasa el timeout."""
    limite = None if timeout is None else time.monotonic() + timeout
    if os.name == "nt":
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    return TECLAS_WIN.get(msvcrt.getwch(), "")
                return normalizar(ch)
            if limite is not None and time.monotonic() >= limite:
                return None
            time.sleep(0.005)
    fd = sys.stdin.fileno()
    espera = None if limite is None else max(0, limite - time.monotonic())
    if not select.select([fd], [], [], espera)[0]:
        return None
    datos = os.read(fd, 1)
    if datos == b"\x1b" and select.select([fd], [], [], 0.02)[0]:
        return TECLAS_ANSI.get(os.read(fd, 2), "")
    return normalizar(datos.decode("utf-8", "ignore"))


def poll(dt):
    """Espera dt segundos y devuelve las teclas pulsadas en ese tiempo."""
    limite = time.monotonic() + dt
    teclas = []
    while True:
        r = limite - time.monotonic()
        if r <= 0:
            return teclas
        k = key(r)
        if k:
            teclas.append(k)


def final(msg):
    sys.stdout.write(f" {color(msg, '1;97')}\n Pulsa una tecla para volver al menú\n")
    sys.stdout.flush()
    while key(0.4) is not None:
        pass
    key()


@contextmanager
def terminal():
    if os.name == "nt":
        os.system("")
    else:
        fd = sys.stdin.fileno()
        viejo = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J")
    try:
        yield
    finally:
        sys.stdout.write("\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        if os.name != "nt":
            termios.tcsetattr(fd, termios.TCSADRAIN, viejo)


DIRS = {"up": (0, -1), "w": (0, -1), "down": (0, 1), "s": (0, 1),
        "left": (-1, 0), "a": (-1, 0), "right": (1, 0), "d": (1, 0)}


def es_letra(k):
    return len(k) == 1 and k.isascii() and k.isalpha()


# ---------- Snake ----------

def snake():
    W, H = 24, 16
    cuerpo = deque([(W // 2, H // 2), (W // 2 - 1, H // 2), (W // 2 - 2, H // 2)])
    d = ult = (1, 0)
    puntos = 0

    def nueva_comida():
        libres = [(x, y) for x in range(W) for y in range(H) if (x, y) not in cuerpo]
        return random.choice(libres) if libres else None

    comida = nueva_comida()
    while True:
        filas = []
        for y in range(H):
            f = ""
            for x in range(W):
                if (x, y) == cuerpo[0]:
                    f += color("██", 92)
                elif (x, y) in cuerpo:
                    f += color("██", 32)
                elif (x, y) == comida:
                    f += color("██", 91)
                else:
                    f += "  "
            filas.append(f)
        draw(caja(filas, W * 2) + [f" Puntos: {puntos}   flechas/WASD · q salir"])

        for k in poll(max(0.05, 0.15 - puntos * 0.003)):
            if k in ("q", "esc"):
                return
            n = DIRS.get(k)
            if n and (n[0] + ult[0], n[1] + ult[1]) != (0, 0):
                d = n

        ult = d
        cabeza = (cuerpo[0][0] + d[0], cuerpo[0][1] + d[1])
        come = cabeza == comida
        if not come:
            cuerpo.pop()
        if not (0 <= cabeza[0] < W and 0 <= cabeza[1] < H) or cabeza in cuerpo:
            return final(f"Game over · puntos: {puntos}")
        cuerpo.appendleft(cabeza)
        if come:
            puntos += 1
            comida = nueva_comida()
            if comida is None:
                return final(f"¡Tablero completo! · puntos: {puntos}")


# ---------- Wordle ----------

PALABRAS = """
ahora album altar amigo ancho andar antes apoyo arena arroz aviso ayuda banco barco besar
bingo blusa bolsa bravo brazo broma bruja bueno burro cabra calor campo canto carne carta
causa cerca chico cielo cifra clase claro clima cobre comer corto coser cruce cuero curso
danza datos dedos deseo disco dolor dudas dulce enero error falda farol fecha feliz fiera
fruta fuego fuera gafas ganar gente globo golpe gordo grado grano gripe grito grupo guapo
gusto habla hacer hasta hielo hogar hotel huevo humor igual joven juego jugar justo labio
largo lejos lento letra libre limon lista lleno local lucha lunar lunes madre magia mango
marco marzo mejor menos mente miedo mismo monte moral mundo museo nacer nadar negro nieve
noche norte notas nuevo obras orden padre pagar pared parte pasar pecho pelea perro piano
plato plaza pluma pobre poder polvo poner prado prisa punto queso rabia radio regla reina
resto ritmo rival rueda ruido sabio sacar salir salsa salud santo serio siglo silla sobre
suelo tabla tarde techo tecla tenis tener tigre tinta tomar tonto torre trago traje trato
tribu trigo turno vacas valle vapor verde viaje vigor virus visto vivir vocal volar votar
zorro
""".split()

COLORES_WORDLE = {2: "42;30", 1: "43;30", 0: "100;97"}


def evaluar(intento, secreta):
    """2 = verde, 1 = amarillo, 0 = gris (con letras repetidas bien contadas)."""
    res = [0] * len(secreta)
    resto = list(secreta)
    for i, (a, b) in enumerate(zip(intento, secreta)):
        if a == b:
            res[i] = 2
            resto[i] = None
    for i, a in enumerate(intento):
        if res[i] == 0 and a in resto:
            res[i] = 1
            resto[resto.index(a)] = None
    return res


def wordle():
    secreta = random.choice(PALABRAS)
    intentos = []
    actual = ""
    msg = ""
    while True:
        filas = ["", "  WORDLE", ""]
        for i in range(6):
            if i < len(intentos):
                p, r = intentos[i]
                celdas = [color(f" {l.upper()} ", COLORES_WORDLE[x]) for l, x in zip(p, r)]
            elif i == len(intentos):
                celdas = [f" {actual[j].upper()} " if j < len(actual) else " _ " for j in range(5)]
            else:
                celdas = [color(" · ", 90)] * 5
            filas.append("  " + " ".join(celdas))
        filas += ["", f"  {msg}", "", "  letras · Enter probar · Backspace borrar · Esc salir"]
        draw(filas)

        if intentos and intentos[-1][0] == secreta:
            return final("¡Correcto!")
        if len(intentos) == 6:
            return final(f"Perdiste. La palabra era: {secreta.upper()}")

        k = key()
        msg = ""
        if k == "esc":
            return
        if k == "backspace":
            actual = actual[:-1]
        elif k == "enter":
            if len(actual) == 5:
                intentos.append((actual, evaluar(actual, secreta)))
                actual = ""
            else:
                msg = "Faltan letras"
        elif es_letra(k) and len(actual) < 5:
            actual += k


# ---------- Tetris ----------

FORMAS = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}
COLORES_TETRIS = {"I": 96, "O": 93, "T": 95, "S": 92, "Z": 91, "J": 94, "L": 33}


def rotar(m):
    return [list(f) for f in zip(*m[::-1])]


def tetris():
    W, H = 10, 20
    tablero = [[None] * W for _ in range(H)]

    def choca(m, x, y):
        for j, fila in enumerate(m):
            for i, v in enumerate(fila):
                if v:
                    xx, yy = x + i, y + j
                    if xx < 0 or xx >= W or yy >= H or tablero[yy][xx]:
                        return True
        return False

    def spawn(n):
        m = FORMAS[n]
        return n, m, W // 2 - len(m[0]) // 2, 0

    n, m, x, y = spawn(random.choice(list(FORMAS)))
    sig = random.choice(list(FORMAS))
    puntos = lineas = 0
    caida = 0.0
    DT = 0.04

    while True:
        nivel = lineas // 10 + 1
        vista = [f[:] for f in tablero]
        for j, fila in enumerate(m):
            for i, v in enumerate(fila):
                if v:
                    vista[y + j][x + i] = n
        filas = ["".join(color("██", COLORES_TETRIS[c]) if c else color(" ·", 90) for c in f) for f in vista]
        panel = ["", " TETRIS", "", f" Puntos: {puntos}", f" Líneas: {lineas}", f" Nivel:  {nivel}", "", " Siguiente:"]
        panel += [" " + "".join(color("██", COLORES_TETRIS[sig]) if v else "  " for v in f) for f in FORMAS[sig]]
        panel += ["", " ←→ mover · ↑ rotar", " ↓ bajar · espacio caer", " q salir"]
        izq = caja(filas, W * 2)
        draw([l + "  " + (panel[i] if i < len(panel) else "") for i, l in enumerate(izq)])

        teclas = poll(DT)
        caida += DT
        for k in teclas:
            if k in ("q", "esc"):
                return
            if k in ("left", "a") and not choca(m, x - 1, y):
                x -= 1
            elif k in ("right", "d") and not choca(m, x + 1, y):
                x += 1
            elif k in ("down", "s") and not choca(m, x, y + 1):
                y += 1
            elif k in ("up", "w"):
                r = rotar(m)
                for dx in (0, -1, 1, -2, 2):
                    if not choca(r, x + dx, y):
                        m, x = r, x + dx
                        break
            elif k == "space":
                while not choca(m, x, y + 1):
                    y += 1
                caida = 99

        if caida >= max(0.08, 0.6 - 0.05 * (nivel - 1)):
            caida = 0
            if not choca(m, x, y + 1):
                y += 1
                continue
            for j, fila in enumerate(m):
                for i, v in enumerate(fila):
                    if v:
                        tablero[y + j][x + i] = n
            pendientes = [f for f in tablero if None in f]
            borradas = H - len(pendientes)
            tablero = [[None] * W for _ in range(borradas)] + pendientes
            lineas += borradas
            puntos += (0, 100, 300, 500, 800)[borradas] * nivel
            n, m, x, y = spawn(sig)
            sig = random.choice(list(FORMAS))
            if choca(m, x, y):
                return final(f"Game over · puntos: {puntos}")


# ---------- Roguelike ----------

RW, RH = 60, 20


def generar_mapa():
    mapa = [["#"] * RW for _ in range(RH)]
    salas = []
    for _ in range(200):
        w, h = random.randint(4, 10), random.randint(3, 5)
        x, y = random.randint(1, RW - w - 1), random.randint(1, RH - h - 1)
        if any(x <= a + c + 1 and a <= x + w + 1 and y <= b + e + 1 and b <= y + h + 1 for a, b, c, e in salas):
            continue
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                mapa[yy][xx] = "."
        if salas:
            a, b, c, e = salas[-1]
            x1, y1, x2, y2 = a + c // 2, b + e // 2, x + w // 2, y + h // 2
            for xx in range(min(x1, x2), max(x1, x2) + 1):
                mapa[y1][xx] = "."
            for yy in range(min(y1, y2), max(y1, y2) + 1):
                mapa[yy][x2] = "."
        salas.append((x, y, w, h))
        if len(salas) == 7:
            break
    return mapa, salas


def sgn(v):
    return (v > 0) - (v < 0)


def roguelike():
    PROF_MAX, HP_MAX = 5, 20

    def nivel(prof):
        mapa, salas = generar_mapa()
        ocupado = set()

        def celda(s):
            while True:
                p = (random.randint(s[0], s[0] + s[2] - 1), random.randint(s[1], s[1] + s[3] - 1))
                if p not in ocupado:
                    ocupado.add(p)
                    return p

        jug = celda(salas[0])
        escalera = celda(salas[-1])
        pociones = {celda(random.choice(salas)) for _ in range(2)}
        enemigos = [{"p": celda(s), "hp": 2 + prof}
                    for s in salas[1:] for _ in range(random.randint(0, 1 + prof // 3))]
        return mapa, jug, escalera, pociones, enemigos

    prof, hp, kills, msg = 1, HP_MAX, 0, "Llega a la profundidad 5 bajando por las escaleras (>)"
    mapa, jug, escalera, pociones, enemigos = nivel(prof)

    while True:
        pos = {e["p"] for e in enemigos}
        filas = []
        for y in range(RH):
            f = ""
            for x in range(RW):
                p = (x, y)
                if p == jug:
                    f += color("@", "1;93")
                elif p in pos:
                    f += color("g", 91)
                elif p == escalera:
                    f += color(">", 96)
                elif p in pociones:
                    f += color("!", 95)
                elif mapa[y][x] == "#":
                    f += color("#", 37)
                else:
                    f += color(".", 90)
            filas.append(f)
        draw([f" Profundidad {prof}/{PROF_MAX}   HP {hp}/{HP_MAX}   Kills {kills}"] + filas
             + [f" {msg}", " flechas/WASD mover y atacar · espacio esperar · q salir"])

        k = key()
        if k in ("q", "esc"):
            return
        mv = DIRS.get(k)
        if not mv and k != "space":
            continue
        msg = ""
        if mv:
            destino = (jug[0] + mv[0], jug[1] + mv[1])
            enemigo = next((e for e in enemigos if e["p"] == destino), None)
            if enemigo:
                dmg = random.randint(1, 3)
                enemigo["hp"] -= dmg
                if enemigo["hp"] <= 0:
                    enemigos.remove(enemigo)
                    kills += 1
                    msg = "Matas a un goblin."
                else:
                    msg = f"Golpeas al goblin ({dmg})."
            elif mapa[destino[1]][destino[0]] == ".":
                jug = destino
                if jug in pociones:
                    pociones.discard(jug)
                    hp = min(HP_MAX, hp + 8)
                    msg = "Poción: +8 HP."
                if jug == escalera:
                    if prof == PROF_MAX:
                        return final(f"¡Has escapado! Kills: {kills}")
                    prof += 1
                    mapa, jug, escalera, pociones, enemigos = nivel(prof)
                    msg = f"Bajas a la profundidad {prof}."
                    continue
            else:
                continue

        ocupadas = {e["p"] for e in enemigos} | {jug}
        for e in enemigos:
            ex, ey = e["p"]
            dx, dy = jug[0] - ex, jug[1] - ey
            dist = abs(dx) + abs(dy)
            if dist == 1:
                dmg = random.randint(0, 2)
                hp -= dmg
                msg += f" Un goblin te golpea ({dmg})."
            elif dist <= 10:
                pasos = [(sgn(dx), 0), (0, sgn(dy))] if abs(dx) >= abs(dy) else [(0, sgn(dy)), (sgn(dx), 0)]
                for sx, sy in pasos:
                    q = (ex + sx, ey + sy)
                    if mapa[q[1]][q[0]] == "." and q not in ocupadas:
                        ocupadas.discard(e["p"])
                        ocupadas.add(q)
                        e["p"] = q
                        break
        if hp <= 0:
            return final(f"Has muerto en la profundidad {prof}. Kills: {kills}")


# ---------- Game of Life ----------

def siguiente_generacion(g):
    H, W = len(g), len(g[0])
    nueva = []
    for y in range(H):
        fila = []
        for x in range(W):
            n = sum(g[(y + j) % H][(x + i) % W] for j in (-1, 0, 1) for i in (-1, 0, 1)) - g[y][x]
            fila.append(n == 3 or (g[y][x] and n == 2))
        nueva.append(fila)
    return nueva


def vida():
    W, H = 40, 20

    def azar():
        return [[random.random() < 0.28 for _ in range(W)] for _ in range(H)]

    g = azar()
    gen = 0
    pausa = False
    while True:
        filas = ["".join(color("██", 92) if c else "  " for c in f) for f in g]
        draw(caja(filas, W * 2) + [f" Gen {gen} · vivas {sum(map(sum, g))}" + (" · PAUSA" if pausa else ""),
                                   " espacio pausa · r nueva · q salir"])
        for k in poll(0.12):
            if k in ("q", "esc"):
                return
            if k == "space":
                pausa = not pausa
            elif k == "r":
                g, gen = azar(), 0
        if not pausa:
            g = siguiente_generacion(g)
            gen += 1


# ---------- Ahorcado ----------

PALABRAS_AHORCADO = """
ordenador teclado pantalla servidor router firewall switch cableado hardware software
programacion algoritmo variable funcion archivo carpeta impresora contrasena direccion
protocolo mantenimiento sistema usuario dominio paquete conexion navegador montana
biblioteca elefante guitarra chocolate aventura mariposa telefono escalera ventana
""".split()


def horca(e):
    c = "O" if e > 0 else " "
    t = "|" if e > 1 else " "
    b1 = "/" if e > 2 else " "
    b2 = "\\" if e > 3 else " "
    p1 = "/" if e > 4 else " "
    p2 = "\\" if e > 5 else " "
    return ["  +---+", "  |   |", f"  {c}   |", f" {b1}{t}{b2}  |", f" {p1} {p2}  |", "=========="]


def ahorcado():
    palabra = random.choice(PALABRAS_AHORCADO)
    usadas = []
    fallos = 0
    while True:
        oculta = " ".join(l if l in usadas else "_" for l in palabra)
        draw([""] + ["  " + l for l in horca(fallos)]
             + ["", "  " + oculta, "", f"  Fallos: {fallos}/6", f"  Usadas: {' '.join(usadas)}", "",
                "  letras para jugar · Esc salir"])
        if all(l in usadas for l in palabra):
            return final("¡Ganaste!")
        if fallos >= 6:
            return final(f"Perdiste. La palabra era: {palabra}")
        k = key()
        if k == "esc":
            return
        if es_letra(k) and k not in usadas:
            usadas.append(k)
            if k not in palabra:
                fallos += 1


# ---------- Buscaminas ----------

NUMEROS = {1: 94, 2: 32, 3: 91, 4: 34, 5: 31, 6: 36, 7: 90, 8: 37}


def buscaminas():
    W, H, M = 12, 10, 15
    minas, vistas, marcas = set(), set(), set()
    cx = cy = 0
    estado = "jugando"

    def vecinos(x, y):
        return [(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)
                if (i or j) and 0 <= x + i < W and 0 <= y + j < H]

    def revelar(x, y):
        pila = [(x, y)]
        while pila:
            p = pila.pop()
            if p in vistas or p in marcas:
                continue
            vistas.add(p)
            if not any(v in minas for v in vecinos(*p)):
                pila.extend(vecinos(*p))

    while True:
        filas = []
        for y in range(H):
            f = ""
            for x in range(W):
                p = (x, y)
                if estado == "perdido" and p in minas:
                    s = color(" *", 91)
                elif p in marcas:
                    s = color(" F", "1;91")
                elif p in vistas:
                    n = sum(v in minas for v in vecinos(x, y))
                    s = color(f" {n}", NUMEROS[n]) if n else "  "
                else:
                    s = color("▒▒", 90)
                f += f"\x1b[7m{s}\x1b[0m" if p == (cx, cy) else s
            filas.append(f)
        draw(caja(filas, W * 2) + [f" Minas: {M - len(marcas)}",
                                   " flechas mover · espacio revelar · f bandera · q salir"])
        if estado != "jugando":
            return final("¡Has ganado!" if estado == "ganado" else "¡BOOM! Has pisado una mina")

        k = key()
        if k in ("q", "esc"):
            return
        if k in DIRS:
            dx, dy = DIRS[k]
            cx, cy = max(0, min(W - 1, cx + dx)), max(0, min(H - 1, cy + dy))
        elif k == "f" and (cx, cy) not in vistas:
            marcas ^= {(cx, cy)}
        elif k in ("space", "enter") and (cx, cy) not in marcas:
            if not minas:
                prohibidas = set(vecinos(cx, cy)) | {(cx, cy)}
                libres = [(x, y) for x in range(W) for y in range(H) if (x, y) not in prohibidas]
                minas = set(random.sample(libres, M))
            if (cx, cy) in minas:
                estado = "perdido"
            else:
                revelar(cx, cy)
                if len(vistas) == W * H - M:
                    estado = "ganado"


# ---------- Pong ----------

def pong():
    W, H, PH = 50, 18, 5
    PX, AX = 2, W - 3
    py = ay = (H - PH) / 2
    error_ia = 0.0
    jp = ap = 0

    def saque():
        return W / 2, H / 2, random.choice((-1.0, 1.0)), random.choice((-0.5, 0.5))

    bx, by, vx, vy = saque()
    while True:
        g = [[" "] * W for _ in range(H)]
        for y in range(H):
            g[y][W // 2] = color(":", 90)
        for j in range(PH):
            g[int(py) + j][PX] = color("█", 96)
            g[int(ay) + j][AX] = color("█", 91)
        g[max(0, min(H - 1, round(by)))][max(0, min(W - 1, round(bx)))] = color("O", "1;93")
        draw([f" Tú {jp}  -  {ap} IA   (primero a 7)"] + caja(["".join(f) for f in g], W)
             + [" ↑↓/WS mover · q salir"])

        for k in poll(0.05):
            if k in ("q", "esc"):
                return
            if k in ("up", "w"):
                py = max(0, py - 2)
            elif k in ("down", "s"):
                py = min(H - PH, py + 2)

        objetivo = by + error_ia if vx > 0 else H / 2
        ay = max(0, min(H - PH, ay + max(-0.6, min(0.6, objetivo - (ay + PH / 2)))))

        nx, ny = bx + vx, by + vy
        if ny < 0 or ny > H - 1:
            vy = -vy
            ny = max(0, min(H - 1, ny))
        fila = round(ny)

        if vx < 0 and bx > PX + 1 and nx <= PX + 1 and int(py) <= fila <= int(py) + PH - 1:
            vx = min(2.0, -vx * 1.06)
            vy = max(-1, min(1, (fila - (int(py) + (PH - 1) / 2)) / (PH / 2) * 0.9 + random.uniform(-0.1, 0.1)))
            nx = PX + 1
            error_ia = random.uniform(-2, 2)
        elif vx > 0 and bx < AX - 1 and nx >= AX - 1 and int(ay) <= fila <= int(ay) + PH - 1:
            vx = max(-2.0, -vx * 1.06)
            vy = max(-1, min(1, (fila - (int(ay) + (PH - 1) / 2)) / (PH / 2) * 0.9 + random.uniform(-0.1, 0.1)))
            nx = AX - 1

        bx, by = nx, ny
        if bx < 0 or bx > W - 1:
            if bx < 0:
                ap += 1
            else:
                jp += 1
            if 7 in (jp, ap):
                return final("¡Ganas!" if jp == 7 else "Gana la IA")
            poll(0.7)
            bx, by, vx, vy = saque()


# ---------- Chill ----------

DIGITOS = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    ":": [" ", "█", " ", "█", " "],
}
RELOJ_ANCHO = 54
FANTASMA = [" .---. ", "( o o )", "|     |", "'^'^'^'"]
PALETA = [(120, 160, 255), (180, 120, 255), (120, 230, 200), (255, 150, 200), (255, 220, 140)]


def sprite_circulo(r):
    return [(dx, dy, "o") for dy in range(-r - 1, r + 2) for dx in range(-2 * r - 2, 2 * r + 3)
            if abs(((dx / 2) ** 2 + dy ** 2) ** 0.5 - r) <= 0.45]


def brillo(p):
    """Fade in / fade out suave según el progreso p (0..1) de vida."""
    b = min(1.0, min(p, 1 - p) * 3)
    return b * b * (3 - 2 * b)


def geometria_reloj(cols, alto):
    grande = cols >= RELOJ_ANCHO + 2 and alto >= 7
    ancho, a = (RELOJ_ANCHO, 5) if grande else (8, 1)
    return grande, (cols - ancho) // 2, (alto - a) // 2, ancho, a


def nueva_entidad(cols, alto, caja, otros=(), edad=0.0):
    fantasma = random.random() < 0.45
    if fantasma:
        cel = [(i - 3, j - 1, c) for j, f in enumerate(FANTASMA) for i, c in enumerate(f) if c != " "]
        rgb = (205, 215, 255)
    else:
        cel = sprite_circulo(random.randint(2, 4))
        rgb = random.choice(PALETA)
    x0, x1 = min(c[0] for c in cel), max(c[0] for c in cel)
    y0, y1 = min(c[1] for c in cel), max(c[1] for c in cel)
    if cols - 4 - x1 < 3 - x0 or alto - 1 - y1 < -y0:
        return None
    for _ in range(30):
        x = random.randint(3 - x0, cols - 4 - x1)
        y = random.randint(-y0, alto - 1 - y1)
        zonas = [caja] + [(o["x"] + o["x0"] - 3, o["y"] + o["y0"], o["x"] + o["x1"] + 3, o["y"] + o["y1"])
                          for o in otros]
        if all(x + x1 + 3 < z[0] or x + x0 - 3 > z[2] or y + y1 < z[1] or y + y0 > z[3] for z in zonas):
            dur = random.uniform(4, 8)
            return {"cel": cel, "x": x, "y": y, "rgb": rgb, "fantasma": fantasma, "dur": dur,
                    "t0": time.monotonic() - edad, "fase": random.uniform(0, 6.28),
                    "x0": x0, "x1": x1, "y0": y0, "y1": y1}
    return None


def escena(cols, alto, ents, ahora, txt):
    celdas = {}
    for e in ents:
        t = ahora - e["t0"]
        b = brillo(t / e["dur"])
        if b < 0.03:
            continue
        rgb = tuple(int(v * b) for v in e["rgb"])
        off = round(2 * math.sin(t * 0.9 + e["fase"])) if e["fantasma"] else 0
        for dx, dy, ch in e["cel"]:
            x, y = e["x"] + dx + off, e["y"] + dy
            if 0 <= x < cols - 1 and 0 <= y < alto:
                celdas[(x, y)] = (ch, rgb)

    grande, x0, y0, _, _ = geometria_reloj(cols, alto)
    if grande:
        reloj = ["  ".join("".join(ch * 2 for ch in DIGITOS[c][r]) for c in txt) for r in range(5)]
    else:
        reloj = [txt]
    for j, f in enumerate(reloj):
        for i, ch in enumerate(f):
            if ch != " ":
                celdas[(x0 + i, y0 + j)] = (ch, (225, 232, 245))

    lineas = []
    for y in range(alto):
        fila = []
        for x in range(cols - 1):
            c = celdas.get((x, y))
            fila.append(f"\x1b[38;2;{c[1][0]};{c[1][1]};{c[1][2]}m{c[0]}" if c else " ")
        lineas.append("".join(fila) + "\x1b[0m")
    return lineas


def chill():
    ents = []
    primera = True
    while True:
        cols, filas = shutil.get_terminal_size((80, 24))
        alto = filas - 2
        ahora = time.monotonic()
        _, x0, y0, ancho, a = geometria_reloj(cols, alto)
        caja = (x0 - 4, y0 - 1, x0 + ancho + 4, y0 + a)
        ents = [e for e in ents if ahora - e["t0"] < e["dur"]]
        if primera:
            for _ in range(6):
                e = nueva_entidad(cols, alto, caja, ents, random.uniform(0, 3))
                if e:
                    ents.append(e)
            primera = False
        elif len(ents) < 9 and random.random() < 0.12:
            e = nueva_entidad(cols, alto, caja, ents)
            if e:
                ents.append(e)
        draw(escena(cols, alto, ents, ahora, time.strftime("%H:%M:%S")) + [color(" q / Esc para volver", 90)])
        for k in poll(0.08):
            if k in ("q", "esc"):
                return


# ---------- menú ----------

JUEGOS = [("Snake", snake), ("Wordle", wordle), ("Tetris", tetris), ("Roguelike", roguelike),
          ("Game of Life", vida), ("Ahorcado", ahorcado), ("Buscaminas", buscaminas), ("Pong", pong),
          ("Chill", chill)]


def menu():
    sel = 0
    while True:
        filas = ["", color("  JUEGOS DE TERMINAL", "1;96"), ""]
        for i, (nombre, _) in enumerate(JUEGOS):
            linea = f"  {i + 1}. {nombre}"
            filas.append(color("> " + linea.strip(), "1;93") if i == sel else "  " + linea.strip())
        filas += ["", "  ↑↓ + Enter, o pulsa el número · q salir"]
        draw(filas)

        k = key()
        if k in ("q", "esc"):
            return
        if k in ("up", "w"):
            sel = (sel - 1) % len(JUEGOS)
        elif k in ("down", "s"):
            sel = (sel + 1) % len(JUEGOS)
        elif k.isdecimal() and 1 <= int(k) <= len(JUEGOS):
            sel = int(k) - 1
            k = "enter"
        if k == "enter":
            clear()
            JUEGOS[sel][1]()
            clear()


if __name__ == "__main__":
    try:
        with terminal():
            menu()
    except KeyboardInterrupt:
        pass