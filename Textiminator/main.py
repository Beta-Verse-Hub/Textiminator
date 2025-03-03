import threading
import keyboard
import time
import math
import random
import wave
import pyaudio



class VisionerBoss():

    def __init__(self):
        self.frame = 5
        self.death_frame = 0
        self.replay_delay = 20
        self.constant_replay_delay = 20
        self.health = 100
        self.phase = 0
        self.phase_delay = 20
        self.start_of_phase = False
        self.fight_started = False
        self.fight_just_started = False


class Hand():

    def __init__(self, x, y):
        self.pos = [x, y]
        with open("Bosses/Visioner/Hand.txt", "r") as hand:
            the_hand = hand.readlines()
        self.looks = the_hand

    def add_hand(self, Map):
        for y in range(len(self.looks)):
            for x in range(len(self.looks[y])):
                if not self.looks[y][x] in ["\n"," "]:
                    Map[y+self.pos[1]][x+self.pos[0]] = self.looks[y][x]

    def on_floor(self, Map):
        return Map[self.pos[1]+12][self.pos[0]] == "#"


class LandMines():

    def __init__(self, pos, bounce):
        self.pos = pos
        self.disport_frame = 0
        self.exploded = False
        self.bounce = 15


    def activate(self, player, Map):
        if self.pos == player.pos and not self.exploded:
            player.health -= 5
            player.jump(Map, leap=self.bounce)
            self.exploded = True
        if self.exploded and self.disport_frame < 6:
            self.disport_frame += 1
            with open(f"EnemyAssets/Landmine/Disport{self.disport_frame}.txt", "r") as f:
                lines = f.readlines()
            for y in range(len(lines)):
                for x in range(len(lines[y])-1):
                    if not lines[y][x] in [" ", "\n"]:
                        Map[y+self.pos[1]-3][x+self.pos[0]-4] = lines[y][x]


class XEnemy():

    def __init__(self, pos, shoot_delay, health):
        self.pos = pos
        self.shoot_delay = shoot_delay
        self.constant_shoot_delay = shoot_delay
        self.health = health


class VEnemy():

    def __init__(self, pos, health, fall_delay, one_time=False):
        self.pos = pos.copy()
        self.og_pos = pos.copy()
        self.health = health
        self.one_time = one_time
        self.fall_delay = fall_delay
        self.constant_fall_delay = fall_delay


    def fall(self, Map):
        try:
            self.pos[1] += 1
            if self.pos[1] >= len(Map) or Map[self.pos[1]][self.pos[0]] == "#":
                self.pos[1] -= 1
                return False, Map
            Map[self.pos[1]][self.pos[0]] = "v"
        except IndexError:
            return False, Map

        return True, Map


    def rise(self, Map):
        try:
            if self.pos[1] - 1 < 0 or Map[self.pos[1] - 1][self.pos[0]] == "#":
                return True, Map
            Map[self.pos[1]][self.pos[0]] = " "
            self.pos[1] -= 1
            Map[self.pos[1]][self.pos[0]] = "v"
        except IndexError:
            return True, Map
        return False, Map



class Bullet():

    def __init__(self, x, y, direction):
        self.pos = [x, y]
        self.direction = direction

    def move(self):
        self.pos[0] += self.direction


    def add_bullet(self, Map):
        if self.direction == 1:
            Map[self.pos[1]][self.pos[0]] = ">"
        elif self.direction == -1:
            Map[self.pos[1]][self.pos[0]] = "<"
        return Map

    def face_wall_or_bullet(self, Map):
        try:
            if Map[self.pos[1]][self.pos[0]+self.direction] == "#" or (Map[self.pos[1]][self.pos[0]+self.direction] == ">" and direction == -1) or (Map[self.pos[1]][self.pos[0]+self.direction] == "<" and direction == 1):
                return True
            return False
        except IndexError:
            return True


    def face_player(self, Map, player):
        try:
            if [self.pos[0]+self.direction, self.pos[1]] == player.pos or self.pos == player.pos:
                return True
            return False
        except IndexError:
            return True


    def face_enemy(self, Map):
        try:
            if Map[self.pos[1]][self.pos[0]+self.direction] == "x" or Map[self.pos[1]][self.pos[0]+self.direction] == "v":
                return True, Map[self.pos[1]][self.pos[0]+self.direction]
            return False, None
        except IndexError:
            return True, None


class Player():

    def __init__(self):
        self.pos = [1,3]
        self.speed = 1
        self.health = 20
        self.leap = 15
        self.dash_delay = 100
        self.constant_dash_delay = 100
        self.y_vel = 0
        self.gravity_acceleration = 1


    def move(self, distance, Map):
        direction = 1 if distance > 0 else -1

        for i in range(abs(distance)):
            new_pos = self.pos[0] + (i + 1) * direction
            try:
                if Map[self.pos[1]][new_pos] == "#":
                    self.pos[0] = new_pos - direction
                    return None
            except IndexError:
                return None

        self.pos[0] = new_pos


    def jump(self, Map, leap = "null"):
        if leap == "null": leap = self.leap
        if self.on_floor(Map):
            self.y_vel = -leap


    def gravity(self, Map, used_potions):
        for i in range(round(self.y_vel)):
            if not self.on_floor(Map):
                self.pos[1] += 1
                if Map[self.pos[1]][self.pos[0]] == "!":
                    self.health = 0
                elif Map[self.pos[1]][self.pos[0]] == "s":
                    used_potions.append([self.pos[0], self.pos[1]])
                    self.speed += 1
                elif Map[self.pos[1]][self.pos[0]] == "j":
                    used_potions.append([self.pos[0], self.pos[1]])
                    self.leap += 2
                elif Map[self.pos[1]][self.pos[0]] == "h":
                    used_potions.append([self.pos[0], self.pos[1]])
                    self.health += 10
                elif Map[self.pos[1]][self.pos[0]] == "d":
                    used_potions.append([self.pos[0], self.pos[1]])
                    self.constant_dash_delay -= 15
                    self.dash_delay -= 15

        for i in range(math.floor(self.gravity_acceleration)):
            if not self.on_floor(Map):
                self.gravity_acceleration += 0.1
            else:
                break


    def zero_acceleration_due_to_gravity(self):
        self.gravity_acceleration = 1


    def on_floor(self, Map):
        return Map[self.pos[1]+1][self.pos[0]] == "#" or Map[self.pos[1]+1][self.pos[0]] == "n"


    def on_ceiling(self, Map):
        return Map[self.pos[1]-1][self.pos[0]] == "#"


    def add_player(self, Map):
        if Map[self.pos[1]][self.pos[0]] == "!":
            self.health = 0
        Map[self.pos[1]][self.pos[0]] = "o"
        return Map



def cutscene():
    print("\n"*50, "@"*103, "\n", ("@"+" "*101+"@\n")*17, "@", " "*40, "HMM...", " "*55, "@", "\n", ("@"+" "*101+"@\n")*17, "@"*103, sep="")
    time.sleep(3)
    print("\n"*50, "@"*103, "\n", ("@"+" "*101+"@\n")*17, "@", " "*40, "I GUESS YOU ARE NOT THAT BORING", " "*30, "@", "\n", ("@"+" "*101+"@\n")*17, "@"*103, sep="")
    time.sleep(3)
    print("\n"*50, "@"*103, "\n", ("@"+" "*101+"@\n")*17, "@", " "*40, "I MUST EXPERIMENT YOU FURTHER", " "*32, "@", "\n", ("@"+" "*101+"@\n")*17, "@"*103, sep="")
    time.sleep(3)

    return "play"


def visioner_fight(Map, boss, player, level, v_enemies, bullets, hands):
    old_phase = boss.phase

    if player.pos[1] > 7 and not boss.fight_started:
        boss.fight_started = True
        boss.fight_just_started = True

    if boss.fight_started:
        level = f"15 0"
        if boss.fight_just_started:
            boss.phase = 1
            boss.fight_just_started = False

        # phase changing
        if boss.phase_delay <= 0 and boss.health > 0:
            boss.phase = random.randint(1, 3)
            boss.phase_delay = random.randint(10, 40)
        else:
            boss.phase_delay -= 1
    else:
        level = f"15"

    if old_phase != boss.phase:
        boss.start_of_phase = True

    if boss.start_of_phase:
        boss.start_of_phase = False

        if boss.phase == 1:
            flag = random.randint(0,1)
            if flag:
                for y in range(6, 31):
                    bullets.append(Bullet(100, y, -1))
            else:
                for y in range(6, 31):
                    bullets.append(Bullet(1, y, 1))

        elif boss.phase == 2:
            v_enemies = []

            for x in range(random.randint(0,2), 101, 3):
                v_enemies.append([VEnemy([x, 5], random.randint(3, 7), 1, True), [x, 5], True])

        elif boss.phase == 3:
            hands.append(Hand(random.randint(1,79), 6))
            hands[len(hands)-1].add_hand(Map)

        boss.phase = 0

    new_Map = get_map(f"Levels/Level {level}.txt")

    with open(f"Bosses/Visioner/BossAnimation{boss.frame}.txt" if boss.death_frame == 0 else f"Bosses/Visioner/BossDeath{boss.death_frame}.txt", "r") as f:
        lines = f.readlines()
    hit = False
    try:
        for y in range(len(lines)):
            for x in range(len(lines[y])-1):
                if Map[10+y][44+x] in ["\\","/",")","(","-"] and lines[y][x] in ["0","."] and not hit:
                    hit = True
                    boss.health -= 2
                elif Map[10+y][44+x] in ["<",">","v",":","!","1","0","?"] and lines[y][x] in ["0","."," ","\n"]:
                    pass
                else:
                    Map[10+y][44+x] = lines[y][x]
            Map[10+y][43+len(lines[y])] = " "
    except:
        pass

    # frame changing and replaying
    if boss.frame == 9:
        boss.frame = 1
        boss.replay_delay = boss.constant_replay_delay
    if boss.replay_delay <= 0:
        boss.frame += 1
    else:
        boss.replay_delay -= 1

    if boss.health <= 0:
        boss.death_frame += 1

    return level, v_enemies


def update_bullets(bullets, Map, x_enemies, v_enemies, player):
    bullets_to_remove = set()

    for i in range(len(bullets) - 1, -1, -1):
        bullet = bullets[i]

        if bullet.face_wall_or_bullet(Map):
            bullets_to_remove.add(i)
            continue

        is_facing_enemy, enemy_type = bullet.face_enemy(Map)
        if is_facing_enemy:
            if enemy_type == "x":
                for j in range(len(x_enemies)):
                    if (x_enemies[j][1][0] == bullet.pos[0] + bullet.direction and x_enemies[j][1][1] == bullet.pos[1] and x_enemies[j][0].health > 0):
                        x_enemies[j][0].health -= 1
                        bullets_to_remove.add(i)
                        break
            elif enemy_type == "v":
                for j in range(len(v_enemies)):
                    if (v_enemies[j][1][0] == bullet.pos[0] + bullet.direction and v_enemies[j][1][1] == bullet.pos[1] and v_enemies[j][0].health > 0):
                        v_enemies[j][0].health -= 1
                        bullets_to_remove.add(i)
                        break
            continue

        if bullet.face_player(Map, player):
            bullets_to_remove.add(i)
            player.health -= 1
            continue

        for j in range(i + 1, len(bullets)):
            bullet2 = bullets[j]

            if bullet.pos[0] == bullet2.pos[0] and bullet.pos[1] == bullet2.pos[1] and bullet.direction != bullet2.direction:
                bullets_to_remove.add(i)
                bullets_to_remove.add(j)
            elif bullet.pos[0] + bullet.direction == bullet2.pos[0] and bullet.pos[1] == bullet2.pos[1] and bullet.direction != bullet2.direction:
                bullets_to_remove.add(i)
                bullets_to_remove.add(j)

    for i in reversed(sorted(bullets_to_remove)):
        bullets.pop(i)

    for i in range(len(bullets) - 1, -1, -1):
        bullet = bullets[i]
        bullet.add_bullet(Map)
        bullet.move()


def get_map(file):
    with open(file, "r") as f:
        lines = f.readlines()
    ListMap = []
    for i in range(len(lines)):
        ListMap.append([])
        for j in range(len(lines[i])):
            ListMap[i].append(lines[i][j])
    return ListMap


def find_enemies(Map):
    x_enemies, v_enemies, landmines = [], [], []
    for y in range(len(Map)):
        for x in range(len(Map[y])):
            if Map[y][x] == "x":
                x_enemies.append([x, y])
                Map[y][x] = " "
            elif Map[y][x] == "v":
                v_enemies.append([x, y])
                Map[y][x] = " "
            elif Map[y][x] == "_":
                landmines.append([x, y])
                Map[y][x] = " "
    return x_enemies, v_enemies, landmines, Map


def print_map(Map, player, height, width, boss = None):
    central_part = player.pos
    strMap = ""

    # remove \n from Map
    for i in range(len(Map)):
        for j in range(len(Map[i])):
            Map[i][j] = Map[i][j].replace("\n", "")

    # add Map to strMap
    for y in range(height + 1):
        for x in range(width + 1):
            try:
                if y+central_part[1]-(height//2) > -1 and x+central_part[0]-(width//2) > -1:
                    strMap += Map[y+central_part[1]-(height//2)][x+central_part[0]-(width//2)]
                else:
                    strMap += " "
            except:
                strMap += " "
        strMap += "\n"

    # wrap it with "." and adding player stats
    strMap = strMap.splitlines()
    strMap = [f"@{line}@" for line in strMap]
    strMap[0] = "\n" * 50 + " HP       " + "I" * player.health + "\n DASH     " + "I" * (player.dash_delay // 5) + "\n"
    if boss != None:
        strMap[0] += " BOSS HP  " + "I" * boss.health + "\n"
    strMap[0] += "\n" + "@" * (width+3)
    strMap[-1] = "@" * (width+3)

    # print the strMap
    print("\n".join(strMap))


def game_loop(level):
    player = Player()
    bullets = []
    x_enemies, v_enemies, landmines, hands = [], [], [], []
    slash = []
    used_potions = []
    jump_button_pressed, left_shoot, right_shoot, left_slash, right_slash, flash_fall = False, False, False, False, False, False
    mainMap = get_map(f"Levels/Level {level}.txt")
    x_enemy_positions, v_enemy_positions, landmine_positions, Map = find_enemies(mainMap.copy())

    if level[0:2] == "15":
        boss1 = VisionerBoss()

    player.pos = [1,3]

    # ADDING ENEMIES
    for i in x_enemy_positions:
        x_enemies.append([XEnemy(i, random.randint(20, 35), 7), i])
    for i in v_enemy_positions:
        v_enemies.append([VEnemy(i, random.randint(3, 7), 1), i, True])
    for i in landmine_positions:
        landmines.append(LandMines(i, random.randint(5, 10)))

    # UPDATE LOOP
    while not keyboard.is_pressed("esc") and not player.health <= 0:
        Map = mainMap.copy()

        # REMOVING DEAD ENEMIES FROM THE MAP
        enemy_number = len(x_enemies)
        for i in x_enemies:
            if i[0].health <= 0:
                Map[i[1][1]][i[1][0]] = " "
                enemy_number -= 1
        for i in v_enemies:
            if i[0].health <= 0:
                Map[i[1][1]][i[1][0]] = " "
        for i in landmines:
            if i.exploded:
                Map[i.pos[1]][i.pos[0]] = " "

        # ACTIVATE EVERY LANDMINE
        for i in landmines:
            i.activate(player, Map)

        # JUMP SYSTEM
        if keyboard.is_pressed("up") and not jump_button_pressed and player.on_floor(Map):
            player.jump(Map)
            jump_button_pressed = True
        elif not keyboard.is_pressed("up"):
            jump_button_pressed = False

        # BOUNCING SYSTEM
        if Map[player.pos[1]+1][player.pos[0]] == "n":
            player.jump(Map)

        # Y VELOCITY SYSTEM

        if player.y_vel < 0:
            for i in range(abs(math.ceil(player.y_vel/4))):
                if not player.on_ceiling(Map):
                    player.pos[1] -= 1
                else:
                    player.y_vel = 0
                    break
            player.y_vel += abs(math.ceil(player.y_vel/4))
        elif player.y_vel > 0:
            player.gravity(Map, used_potions)
            if player.on_floor(Map):
                player.y_vel = 0

        if not player.on_floor(Map):
            player.y_vel += player.gravity_acceleration

        if player.on_floor(Map):
            player.zero_acceleration_due_to_gravity()

        # MOVEMENT SYSTEM
        if keyboard.is_pressed("left"):
            player.move(-3*(player.speed) if keyboard.is_pressed("s") else -(player.speed), Map)
        if keyboard.is_pressed("right"):
            player.move(3*(player.speed) if keyboard.is_pressed("s") else (player.speed), Map)

        # DASH SYSTEM
        if keyboard.is_pressed("e") and player.dash_delay >= player.constant_dash_delay:
            old_pos = player.pos[0]
            player.move(20,Map)
            new_pos = player.pos[0]
            for i in range(old_pos, new_pos):
                Map[player.pos[1]][i] = "-"
            player.dash_delay = 0
        if keyboard.is_pressed("q") and player.dash_delay >= player.constant_dash_delay:
            old_pos = player.pos[0]
            player.move(-20,Map)
            new_pos = player.pos[0]
            for i in range(new_pos, old_pos):
                Map[player.pos[1]][i] = "-"
            player.dash_delay = 0

        # SHOOTING SYSTEM
        if keyboard.is_pressed("a") and Map[player.pos[1]][player.pos[0]-1] != "#" and not left_shoot:
            bullets.append(Bullet(player.pos[0]-1, player.pos[1], -1))
            left_shoot = True
            sound_thread = threading.Thread(target=get_music)
            sound_thread.start()
        elif not keyboard.is_pressed("a"):
            left_shoot = False
        if keyboard.is_pressed("d") and Map[player.pos[1]][player.pos[0]+1] != "#" and not right_shoot:
            bullets.append(Bullet(player.pos[0]+1, player.pos[1], 1))
            right_shoot = True
            sound_thread = threading.Thread(target=get_music)
            sound_thread.start()
        elif not keyboard.is_pressed("d"):
            right_shoot = False

        # REMOVING USED POTIONS

        for i in used_potions:
            try:
                Map[i[1]][i[0]] = " "
            except IndexError:
                pass

        # POTION SYSTEM

        try:
            if Map[player.pos[1]][player.pos[0]] == "s":
                used_potions.append([player.pos[0], player.pos[1]])
                player.speed += 1
            elif Map[player.pos[1]][player.pos[0]] == "j":
                used_potions.append([player.pos[0], player.pos[1]])
                player.leap += 2
            elif Map[player.pos[1]][player.pos[0]] == "h":
                used_potions.append([player.pos[0], player.pos[1]])
                player.health += 10
            elif Map[player.pos[1]][player.pos[0]] == "d":
                used_potions.append([player.pos[0], player.pos[1]])
                player.constant_dash_delay -= 15
                player.dash_delay -= 15
        except:
            pass

        # FLASH FALL SYSTEM

        if keyboard.is_pressed("x") and not flash_fall:
            flash_fall = True
            while True:
                Map[player.pos[1]][player.pos[0]] = "|"
                if not Map[player.pos[1]+1][player.pos[0]] in ["#","n","!"]:
                    player.pos[1] += 1
                else:
                    break
        elif flash_fall:
            flash_fall = False

        # SLASHING SYSTEM

        if slash != []:
            Map[slash[0][0][1]+player.pos[1]][slash[0][0][0]+player.pos[0]] = slash[0][1]
            slash = slash[1:]

        if keyboard.is_pressed("c") and not right_slash:
            Map[player.pos[1]-1][player.pos[0]+2] = "\\"
            slash.append([[3, 0], ")"])
            slash.append([[2, 1], "/"])
            right_slash = True
        elif not keyboard.is_pressed("c"):
            right_slash = False
        if keyboard.is_pressed("z") and not left_slash:
            Map[player.pos[1]-1][player.pos[0]-2] = "/"
            slash.append([[-3, 0], "("])
            slash.append([[-2, 1], "\\"])
            left_slash = True
        elif not keyboard.is_pressed("z"):
            left_slash = False

        for i in x_enemies:
            if Map[i[1][1]][i[1][0]] == "(" or Map[i[1][1]][i[1][0]] == ")" or Map[i[1][1]][i[1][0]] == "/" or Map[i[1][1]][i[1][0]] == "\\" or Map[i[1][1]][i[1][0]] == "-":
                i[0].health -= 3
            elif Map[i[1][1]][i[1][0]] == "|":
                i[0].health -= 10

        # MAKE THE X ENEMIES SHOOT
        for i in range(len(x_enemies)-1, -1, -1):
            enemy = x_enemies[i][0]
            if enemy.shoot_delay > 0 and enemy.health > 0:
                enemy.shoot_delay -= 1
            elif enemy.health > 0:
                enemy.shoot_delay = enemy.constant_shoot_delay
                if Map[enemy.pos[1]][enemy.pos[0]-1] != "#" and enemy.health > 0:
                    bullets.append(Bullet(enemy.pos[0]-1, enemy.pos[1], -1))
                if Map[enemy.pos[1]][enemy.pos[0]+1] != "#" and enemy.health > 0:
                    bullets.append(Bullet(enemy.pos[0]+1, enemy.pos[1], 1))

        # MAKE V ENEMIES FALL AND RISE
        for i in range(len(v_enemies)-1, -1, -1):
            enemy = v_enemies[i][0]
            if enemy.health > 0 and enemy.fall_delay > 0:
                enemy.fall_delay -= 1
                for i in range(enemy.pos[1]-enemy.og_pos[1]):
                    try:
                        Map[enemy.og_pos[1]+i][enemy.pos[0]] = ":"
                    except IndexError:
                        pass
                Map[enemy.pos[1]][enemy.pos[0]] = "v"
            elif enemy.health > 0:
                enemy.fall_delay = enemy.constant_fall_delay
                if v_enemies[i][2]:
                    v_enemies[i][2], Map = enemy.fall(Map)
                else:
                    if enemy.one_time:
                        v_enemies.pop(i)
                        continue
                    v_enemies[i][2], Map = enemy.rise(Map)
                for i in range(enemy.pos[1]-enemy.og_pos[1]):
                    try:
                        Map[enemy.og_pos[1]+i][enemy.pos[0]] = ":"
                    except IndexError:
                        pass

        # HIT BY V ENEMY CHECK
        if Map[player.pos[1]][player.pos[0]] == "v":
            player.health -= 1

        # MAKE HAND PUNCH THE FLOOR
        for i in range(len(hands) - 1, -1, -1):
            if hands[i].on_floor(Map):
                hands.pop(i)
            else:
                hands[i].pos[1] += 1
                hands[i].add_hand(Map)

        # ADDING BULLET AND MOVING IT
        update_bullets(bullets, Map, x_enemies, v_enemies, player)

        # UPDATING DASH DELAY
        if player.dash_delay < player.constant_dash_delay:
            player.dash_delay += 10
        elif player.dash_delay > player.constant_dash_delay:
            player.dash_delay = player.constant_dash_delay

        # VISIONER FIGHT
        if level[0:2] == "15":
            level, v_enemies = visioner_fight(Map, boss1, player, level, v_enemies, bullets, hands)

        # WIN THE GAME
        if Map[player.pos[1]][player.pos[0]] == "%" and enemy_number == 0:
            return f"L{int(level)+1}"
        if level[0:2] == "15":
            if boss1.death_frame == 24:
                return cutscene()

        Map = player.add_player(Map)
        if level[0:2] == "15":
            print_map(Map, player, 36, 100, boss1)
        else:
            print_map(Map, player, 36, 100)

        if keyboard.is_pressed("r"):
            if level[0:2] == "15":
                return f"L15"
            return f"L{level}"
        elif keyboard.is_pressed("m"):
            return "play"
        time.sleep(0.05)
        mainMap = get_map(f"Levels/Level {level}.txt")

    if player.health <= 0:
        print("@"*103, "\n", ("@"+" "*101+"@\n")*17, "@", " "*46, "You Died", " "*47, "@", "\n", ("@"+" "*101+"@\n")*2, "@", " "*45, "R to Retry", " "*46, "@", "\n", "@", " "*45, "M for Menu", " "*46, "@", "\n", ("@"+" "*101+"@\n")*13, "@"*103, sep="")
        while not keyboard.is_pressed("esc"):
            if keyboard.is_pressed("r"):
                if  level[0:2] == "15":
                    return f"L15"
                return f"L{level}"
            elif keyboard.is_pressed("m"):
                return "play"


def main_menu(height, width):
    up_pressed = False
    down_pressed = False
    select = 0
    while not keyboard.is_pressed("esc"):

        Map = ""
        options = ["  PLAY", "  CONTROLS", "  CREDITS", "  EXIT"]

        if keyboard.is_pressed("up") and not up_pressed and select != 0:
            select -= 1
            up_pressed = True
        elif not keyboard.is_pressed("up"):
            up_pressed = False

        if keyboard.is_pressed("down") and not down_pressed and select != len(options)-1:
            select += 1
            down_pressed = True
        elif not keyboard.is_pressed("down"):
            down_pressed = False


        # UPDATE OPTIONS
        options[select] = "0" + options[select][1:]

        # MAKE MAP
        Map += (" "*(width+1)+"\n")*15
        Map += " "*44
        Map += "TEXTIMINATOR"
        Map += " "*45
        Map += "\n"
        Map += (" "*(width+1)+"\n")*3

        for i in options:
            Map += " "*44
            Map += i
            Map += " "*(57 - len(i))
            Map += "\n"

        Map += (" "*(width+1)+"\n")*15

        # wrap Map with "@"
        Map = Map.splitlines()
        Map = [f"@{line}@" for line in Map]
        first_line = "\n" * 50 + "@" * (width+3)
        last_line = "@" * (width+3)

        Map[0] = first_line
        Map[-1] = last_line

        if keyboard.is_pressed("enter"):
            break

        # print the Map
        print("\n".join(Map))
        time.sleep(0.03)

    if select == 0:
        return "play"
    elif select == 1:
        return "control"
    elif select == 2:
        return "credits"
    elif select == 3:
        return "exit"


def play_menu(height, width):
    levels = []
    right_pressed, left_pressed = False, False
    select = 0
    for i in range(15):
        levels.append(f"  {i+1}")
    while not keyboard.is_pressed("esc"):
        Map = "\n" * 50

        if keyboard.is_pressed("left") and not left_pressed and select != -1:
            select -= 1
            left_pressed = True
        elif not keyboard.is_pressed("left"):
            left_pressed = False

        if keyboard.is_pressed("right") and not right_pressed and select != len(levels)-1:
            select += 1
            right_pressed = True
        elif not keyboard.is_pressed("right"):
            right_pressed = False

        if keyboard.is_pressed("space"):
            break

        m = 0
        Map += "@" * (width+3) + "\n"
        for i in range(height):

            Map += "@"

            if i == 1:
                Map += f" {"0" if select == -1 else " "} BACK"
                Map += " " * (width-6)

            elif i == 5:
                Map += " " * ((width//2)-3)
                Map += "LEVELS"
                Map += " " * ((width//2)-2)

            elif i in [10, 20, 30]:
                Map += " " * 26
                for j in range(5):
                    Map += f"{"0"+levels[m][1:] if select == m else levels[m]}" + (" "*7 if len(levels[m]) == 3 else " "*6)
                    m += 1
                Map +=  " " * 25

            else:
                Map += " " * (width+1)

            Map += "@\n"
        Map += "@" * (width+3)

        print(Map)
        time.sleep(0.03)

    if select == -1:
        return "main"
    return f"L{select+1}"


def credits_menu(height, width):
    Map = "\n" * 50
    Map += "@"*(width+3) + "\n"
    Map += ("@" + (" "*(width+1)) + "@\n")*14
    Map += ("@" + (" "*42) + ("MUSIC:") + (" "*53) + "@\n") + ("@" + (" "*43) + ("Slok Dube") + (" "*49) + "@\n") + ("@" + (" "*43) + ("Vinod Dube") + (" "*48) + "@\n")
    Map += ("@" + (" "*(width+1)) + "@\n")*2
    Map += ("@" + (" "*42) + ("EVERTHING ELSE:") + (" "*44) + "@\n") + ("@" + (" "*43) + ("Baibhav Kumar Jha") + (" "*41) + "@\n")
    Map += ("@" + (" "*(width+1)) + "@\n")*15
    Map += "@"*(width+3)
    print(Map)

    while not keyboard.is_pressed("esc"):
        if keyboard.is_pressed("space"):
            return "main"

    return "exit"


def get_music():
    with wave.open("Musics and Sound Effects/Gunjutsu.wav", "rb") as wf:
        pa = pyaudio.PyAudio()

        stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        while len(data := wf.readframes(100)):
            stream.write(data)

        stream.close()

        pa.terminate()


if __name__ == "__main__":
    height, width = 36, 100
    menu = "main"

    while not keyboard.is_pressed("esc"):
        if menu == "main":
            menu = main_menu(height, width)
        elif menu == "play":
            menu = play_menu(height, width)
        elif menu == "credits":
            menu = credits_menu(height, width)
        elif menu[0] == "L":
            menu = game_loop(menu[1:])
        elif menu == "exit":
            break
