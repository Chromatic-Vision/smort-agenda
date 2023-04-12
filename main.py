import io
import json
import os
from urllib.request import Request, urlopen

import pygame
import typing
import enum
import math
import datetime

import api
import logger

size = (0, 0)

# TODO: settings and colorschemes

pygame.init()
logger.reset_log()

zermelo = None

username = ''
password = ''
tenant = 'gymnasiumnovum'

week_nr = str(int(datetime.datetime.now().strftime('%Y%U')))
week = None
# print(week_nr)

config_file = "config.json"
custom_background = False
custom_background_url = ""

clean_ui = False
display_informations = True

background_image = None


class State(enum.IntEnum):
    username = enum.auto()
    password = enum.auto()
    login = enum.auto()  # logging into zermelo
    main = enum.auto()


state = State.username
state_login_fail = False

def save_config():
    logger.log('Saving config...')
    filename = config_file

    with open(filename, 'w') as file:
        config_json_data = {
            "config": {
                "custom_background": custom_background,
                "background_url": custom_background_url,
                "clean_ui": clean_ui,
                "display_informations": display_informations
            }
        }

        json.dump(config_json_data, file)

def load_config():

    global custom_background # TODO: fix this trash code
    global custom_background_url
    global clean_ui
    global background_image
    global display_informations

    filename = config_file
    logger.log(f"Loading config '{filename}'")

    if filename not in os.listdir('.'):
        logger.warn('No config, creating new...')

        with open(filename, 'w') as file:
            config_json_data = {
                "config": {
                    "custom_background": False,
                    "background_url": "",
                    "clean_ui": False,
                    "display_informations": True
                }
            }

            json.dump(config_json_data, file)
            return

    with open(filename, "r+") as file:
        try:
            config_json_data: dict = json.load(file)

            try:
                custom_background = config_json_data['config']['custom_background']
                custom_background_url = config_json_data['config']['background_url']
                clean_ui = config_json_data['config']['clean_ui']
                display_informations = config_json_data['config']['display_informations']

                # request background image
                if custom_background and custom_background_url != "":
                    try:

                        request_site = Request(custom_background_url, headers={"User-Agent": "Mozilla/5.0"})

                        background_file = io.BytesIO(urlopen(request_site).read())
                        background_image = pygame.image.load(background_file)
                    except Exception as le:
                        logger.error(le)

            except KeyError as ke:
                logger.warn("Broken config file detected! Resetting...")
                logger.error(ke)
                file.truncate()

                save_config()

        except json.decoder.JSONDecodeError as jde:
            logger.error(f'{filename} JSONDecodeError')
            logger.error(jde)
            logger.error(f'{filename}:')
            file.seek(0)
            logger.error("'" + str(file.read()) + "'")


try:
    with open('credentials.txt', 'r') as file:
        data = file.read()
        split = data.split('\n')
        if len(split) != 3:
            raise ValueError
        username = split[0]
        password = split[1]
        tenant = split[2]
        state = State.login
        zermelo = api.Api(username, password, tenant)

        load_config()

except FileNotFoundError:
    pass
except ValueError:
    pass


def loading_spinner(x: int, y: int):
    global screen, size, frame
    speed = .06

    s = size[1] // 10
    pygame.draw.rect(screen, (0, 0, 0), (x, y, s, s))

    # pygame.draw.lines(screen, (255, 255, 255), False, [
    #     (x + math.sin(frame * speed) * s / 2, y + math.cos(frame * speed) * s / 2),
    #     (x + math.sin(frame * speed + math.pi / 2) * s / 2, y + math.cos(frame * speed + math.pi / 2) * s / 2),
    #     (x + math.sin(frame * speed + math.pi) * s / 2, y + math.cos(frame * speed + math.pi) * s / 2)
    # ], size[1] // 30)

    circles = 7
    for i in range(circles):
        pygame.draw.circle(screen, (255, 255, 255),
                           (x + math.sin(frame * speed + i / circles * math.pi * ((frame + i / circles) * .01)) * s / 2,
                            y + math.cos(frame * speed + i / circles * math.pi * ((frame + i / circles) * .01)) * s / 2),
                           size[1] // 80)


def add_week(delta: int):
    global week_nr
    if delta not in [-1, 0, 1]:
        raise NotImplementedError('Bigger changes than 1')

    if delta == 0:
        return week_nr

    w = [week_nr[:4], week_nr[-2:]]

    if (int(w[1]) < 52 and delta == 1) or (int(w[1]) > 1 and delta == -1):
        w[1] = str(int(w[1]) + delta)
        if len(w[1]) == 1:
            w[1] = '0' + w[1]
        else:
            assert len(w[1]) == 2, f'Week not 1 or 2 number(s) but {len(w[1])}'
    else:
        w[0] = str(int(w[0]) + delta)
        if delta == -1:
            w[1] = '52'
        else:
            w[1] = '01'

    return ''.join(w)

def start_of_week():
    global week_nr

    start_day = datetime.datetime.strptime(week_nr[:4], '%Y')
    t = datetime.datetime.strptime(week_nr[:4] + ' ' + str(int(week_nr[-2:]) * 7 - start_day.isoweekday() + 2), '%Y %j')
    return t


pre_mouse_press = [False, False, False]
font = pygame.font.Font('fonts/ubuntu.ttf', 10)
big_font = pygame.font.Font('fonts/ubuntu.ttf', 20)


def resize():
    global size, font, big_font, dash_line

    font = pygame.font.Font('fonts/ubuntu.ttf', size[1] // 30)
    big_font = pygame.font.Font('fonts/ubuntu.ttf', size[1] // 20)

    dash_line = pygame.Surface((size[0], 1))

    lines = 7 * 3
    for i in range(lines):
        pygame.draw.rect(dash_line, (100, 100, 100),
                         (int((i / lines + .25/lines) * size[0]), 0,
                          int(.5 / lines * size[0]), 1))


screen = pygame.display.set_mode(size, pygame.RESIZABLE)
clock = pygame.time.Clock()
run = True
size = screen.get_size()  # different because (0, 0) makes it fit to the screen
dash_line = pygame.Surface((size[0], 1))
resize()
frame = 0

logger.log("Initialized smort-agenda")

while run:
    clock.tick(60)
    screen.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.WINDOWRESIZED:
            size = screen.get_size()
            resize()

        elif event.type == pygame.TEXTINPUT:  # TODO: TEXTEDITING event
            if state == State.username:
                username += event.text
            if state == State.password:
                password += event.text

        elif event.type == pygame.KEYDOWN:
            if state == State.username:
                if event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif event.key == pygame.K_RETURN:
                    state = State.password
            elif state == State.password:
                if event.key == pygame.K_BACKSPACE:
                    password = password[:-1]
                elif event.key == pygame.K_RETURN:
                    state = State.login
                    zermelo = api.Api(username, password, tenant)
            elif state == State.main:
                if event.key == pygame.K_RIGHT:
                    week_nr = add_week(1)

                elif event.key == pygame.K_LEFT:
                    week_nr = add_week(-1)

                elif event.key == pygame.K_r:
                    week_nr = str(int(datetime.datetime.now().strftime('%Y%U')))

    if zermelo is not None and state == State.main:

        zermelo.update()
        week = zermelo.get(week_nr)

        zermelo.get(add_week(-1))
        zermelo.get(add_week(1))

    if state != State.main:
        screen.blit(font.render(str(state)[6:] + "...", True, (255, 255, 255)), (0, 0))

    if state == State.username:
        screen.blit(big_font.render(username, True, (255, 255, 255)), (100, 100))

        if state_login_fail:
            s = font.render('Incorrect password and/or username!', True, (255, 0, 0))
            screen.blit(s, (size[0] - s.get_width(), 0))
    elif state == State.password:
        screen.blit(big_font.render(username, True, (255, 255, 255)), (100, 100))
        screen.blit(big_font.render('#' * len(password), True, (255, 255, 255)), (100, 100 + size[1] // 20))

        state_login_fail = False
    elif state == State.login:
        loading_spinner(size[1] // 10, size[1] // 10 + 10)
        pygame.draw.rect(screen, (255, 255, 255),
                         (0, size[1] // 5, round(zermelo.state / zermelo.max_state * size[0]), size[1] // 20))
        if zermelo.state == zermelo.max_state:
            state = State.main

            logger.log("Login successfull!")

            with open('credentials.txt', 'w') as file:
                file.write(username + '\n' + password + '\n' + tenant)  # TODO: prompt the user if they want to store
        if not zermelo.successfull:
            if not zermelo.credentials_correct:
                state = State.username
                state_login_fail = True
                username = ''
                password = ''

                logger.error("Incorrect password and/or username!")
            else:
                zermelo = api.Api(username, password, tenant)  # TODO: notify user
                logger.warn("Server crash??")

    elif state == State.main:

        cancelled_subjects = []

        if week is not None:
            # print(week, week.appointments, week.raw)
            height = int(size[1] / 23.983)
            width = size[0] // 7

            # TODO: maybe fill weekdays with (50, 50, 50)?
            if custom_background and background_image is not None:
                background_image = pygame.transform.smoothscale(background_image, size)
                screen.blit(background_image, (0, 0))
            else:
                for i in range(24):
                    screen.blit(dash_line, (0, i * height))
                for i in range(7):
                    pygame.draw.rect(screen, (100, 100, 100), (i * width, 0, 1, size[1]))

            y = 0
            x = 0


            for appointment in week.appointments:
                # print(appointment.start.isoweekday(), appointment.start.hour + appointment.start.minute / 60)

                x = width * (appointment.start.isoweekday() - 1)
                y = int(height * (appointment.start.hour + appointment.start.minute / 60))
                h = int(height * (appointment.end.hour + appointment.end.minute / 60) - y)

                # y = round(height * (23 + 59 / 60))

                if appointment.valid:
                    c = (30, 30, 30)
                else:
                    c = (100, 0, 0)
                if not clean_ui: pygame.draw.rect(screen, c, (x, y, width, h))

                str_subjects = ', '.join(appointment.subjects)
                str_teachers = ', '.join(appointment.teachers)
                str_locations = ', '.join(appointment.locations)

                if not appointment.optional:
                    s = font.render((str_subjects
                                     + (' - ' if str_teachers != '' else '') + str_teachers
                                     + (' - ' if str_locations != '' else '') + str_locations),
                                    True, (255, 255, 255))
                else:
                    s = font.render(str(len(appointment.options)), True, (150, 255, 150))

                if s.get_height() > h:
                    ratio = s.get_width() / s.get_height()
                    # print(ratio, s.get_width(), s.get_height() * ratio)
                    s = pygame.transform.smoothscale(s, (h * ratio, h))

                screen.blit(s, (x, y))

                if appointment.cancelled:
                    c = (255, 50, 50)
                    cancelled_subjects.append(appointment)
                elif appointment.optional:
                    c = (50, 255, 50)
                else:
                    c = (255, 255, 255)
                pygame.draw.rect(screen, c, (x, y, width, h), 1)

                y += height

        else:
            loading_spinner(size[1] // 10, size[1] // 10 + 50)

        if display_informations:
            screen.blit(font.render(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'), True, (255, 255, 255)), (0, 0)) # TODO: this will render over anything planned for 0 AM monday
            screen.blit(font.render(start_of_week().strftime('%d %B'), True, (255, 255, 255)), (0, 25))

            if len(cancelled_subjects) > 0:

                cy = 0

                for c in cancelled_subjects:
                    cy += 25

                ny = size[1] - cy - 40

                screen.blit(font.render("Uitgevallen: ", True, (255, 255, 255)), (0, ny))

                for cs in cancelled_subjects:
                    screen.blit(font.render(" " + ', '.join(cs.subjects) + " > " + datetime.datetime.strftime(cs.start, "%H:%M") + " ~ " + datetime.datetime.strftime(cs.end, "%H:%M") + (" - " + ', '.join(cs.locations if cs.locations is not None else "") + " (" + datetime.datetime.strftime(cs.start, "%d %B") + ")") , True, (255, 255, 255)), (0, ny + 25))
                    ny += 25



    # screen.blit(font.render('Hello, World', True, (255, 255, 255)), (0, 0))
    # screen.blit(big_font.render('Hello, World', True, (255, 255, 255)), (0, size[1] // 30))

    pygame.display.update()
    frame += 1

pygame.quit()