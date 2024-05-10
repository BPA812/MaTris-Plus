#!/usr/bin/env python
import pygame
from pygame import Rect, Surface
import random as r
import os
import kezmenu
from tetrominoes import list_of_tetrominoes
from tetrominoes import rotate
from scores import load_score, write_score
class GameOver(Exception):
    """XD"""
def get_sound(filename):
    return pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "resources", filename))
BC,BRC,BS,BW,MATRIS_OFFSET,MATRIX_WIDTH,MH,LEFT_MARGIN = (15, 15, 20),(140, 140, 140),30,10,20,10,22,340
WIDTH = MATRIX_WIDTH*BS + BW*2 + MATRIS_OFFSET*2 + LEFT_MARGIN
HEIGHT,TRICKY_CENTERX,VISIBLE_MH = (MH-2)*BS + BW*2 + MATRIS_OFFSET*2,WIDTH-(WIDTH-(MATRIS_OFFSET+BS*MATRIX_WIDTH+BW*2))/2, MH - 2
class Matris(object):
    def __init__(self):
        self.surface = screen.subsurface(Rect((MATRIS_OFFSET+BW, MATRIS_OFFSET+BW),
                                              (MATRIX_WIDTH * BS, (MH-2) * BS)))
        self.matrix = dict()
        for y in range(MH):
            for x in range(MATRIX_WIDTH):
                self.matrix[(y,x)] = None
        self.next_tm = r.choice(list_of_tetrominoes)
        self.set_tmes()
        self.tm_r,self.d_ = 0,0
        self.base_d_s = 0.4
        self.mk,self.mk_s = {'left': 0, 'right': 0},0.05
        self.mk_t = (-self.mk_s)*2
        self.level,self.score,self.lines,self.combo = 1,0,0,1
        self.hs,self.played_hsbeaten_sound,self.paused = load_score(),False,False
        self.levelup_sound,self.gameover_sound,self.linescleared_sound,self.hsbeaten_sound = get_sound("levelup.wav"),get_sound("gameover.wav"),get_sound("linecleared.wav"),get_sound("highscorebeaten.wav")
    def set_tmes(self):
        self.current_tm,self.next_tm = self.next_tm,r.choice(list_of_tetrominoes)
        self.surface_of_next_tm = self.construct_surface_of_next_tm()
        self.tm_p,self.tm_r,self.tm_block,self.shadow_block = (0,4) if len(self.current_tm.shape) == 2 else (0, 3),0,self.block(self.current_tm.color),self.block(self.current_tm.color, shadow=True)
    def hard_drop(self):
        amount = 0
        while self.request_movement('down'):
            amount += 1
        self.score += 10*amount
        self.lock_tm()
    def update(self, timepassed):
        self.needs_redraw = False
        pr = lambda key: event.type == pygame.KEYDOWN and event.key == key
        unpr = lambda key: event.type == pygame.KEYUP and event.key == key
        events = pygame.event.get()
        for event in events:
            if pr(pygame.K_p):
                self.surface.fill((0,0,0))
                self.needs_redraw = True
                self.paused = not self.paused
            elif event.type == pygame.QUIT:
                self.gameover(full_exit=True)
            elif pr(pygame.K_ESCAPE):
                self.gameover()
        if self.paused:
            return self.needs_redraw
        for event in events:
            if pr(pygame.K_SPACE):
                self.hard_drop()
            elif pr(pygame.K_UP) or pr(pygame.K_w):
                self.request_r()
            elif pr(pygame.K_LEFT) or pr(pygame.K_a):
                self.request_movement('left')
                self.mk['left'] = 1
            elif pr(pygame.K_RIGHT) or pr(pygame.K_d):
                self.request_movement('right')
                self.mk['right'] = 1
            elif unpr(pygame.K_LEFT) or unpr(pygame.K_a):
                self.mk['left'] = 0
                self.mk_t = (-self.mk_s)*2
            elif unpr(pygame.K_RIGHT) or unpr(pygame.K_d):
                self.mk['right'] = 0
                self.mk_t = (-self.mk_s)*2
        self.d_s = self.base_d_s ** (1 + self.level/10.)
        self.d_ += timepassed
        d_s = self.d_s*0.10 if any([pygame.key.get_pressed()[pygame.K_DOWN],pygame.key.get_pressed()[pygame.K_s]]) else self.d_s
        if self.d_ > d_s:
            if not self.request_movement('down'):
                self.lock_tm()
            self.d_ %= d_s
        if any(self.mk.values()):
            self.mk_t += timepassed
        if self.mk_t > self.mk_s:
            self.request_movement('right' if self.mk['right'] else 'left')
            self.mk_t %= self.mk_s
        return self.needs_redraw
    def draw_surface(self):
        with_tm = self.blend(matrix=self.place_shadow())
        for y in range(MH):
            for x in range(MATRIX_WIDTH):
                block_location = Rect(x*BS, (y*BS - 2*BS), BS, BS)
                if with_tm[(y,x)] is None:
                    self.surface.fill(BC, block_location)
                else:
                    if with_tm[(y,x)][0] == 'shadow':
                        self.surface.fill(BC, block_location)
                    self.surface.blit(with_tm[(y,x)][1], block_location)
    def gameover(self, full_exit=False):
        write_score(self.score)
        if full_exit:
            exit()
        else:
            raise GameOver("Sucker!")
    def place_shadow(self):
        posY, posX = self.tm_p
        while self.blend(p=(posY, posX)):
            posY += 1
        p = (posY-1, posX)
        return self.blend(p=p, shadow=True)
    def fits_in_matrix(self, shape, p):
        posY, posX = p
        for x in range(posX, posX+len(shape)):
            for y in range(posY, posY+len(shape)):
                if self.matrix.get((y, x), False) is False and shape[y-posY][x-posX]:
                    return False
        return p
    def request_r(self):
        r = (self.tm_r + 1) % 4
        shape = self.rotated(r)
        y, x = self.tm_p
        p = (self.fits_in_matrix(shape, (y, x)) or
                    self.fits_in_matrix(shape, (y, x+1)) or
                    self.fits_in_matrix(shape, (y, x-1)) or
                    self.fits_in_matrix(shape, (y, x+2)) or
                    self.fits_in_matrix(shape, (y, x-2)))
        if p and self.blend(shape, p):
            self.tm_r = r
            self.tm_p = p 
            self.needs_redraw = True
            return self.tm_r
        else:
            return False  
    def request_movement(self, direction):
        posY, posX = self.tm_p
        if direction == 'left' and self.blend(p=(posY, posX-1)):
            self.tm_p = (posY, posX-1)
            self.needs_redraw = True
            return self.tm_p
        elif direction == 'right' and self.blend(p=(posY, posX+1)):
            self.tm_p = (posY, posX+1)
            self.needs_redraw = True
            return self.tm_p
        elif direction == 'up' and self.blend(p=(posY-1, posX)):
            self.needs_redraw = True
            self.tm_p = (posY-1, posX)
            return self.tm_p
        elif direction == 'down' and self.blend(p=(posY+1, posX)):
            self.needs_redraw = True
            self.tm_p = (posY+1, posX)
            return self.tm_p
        else:
            return False
    def rotated(self, r=None):
        if r is None:
            r = self.tm_r
        return rotate(self.current_tm.shape, r)
    def block(self, color, shadow=False):
        colors = {'blue':   (105, 105, 255),
                  'yellow': (225, 242, 41),
                  'pink':   (242, 41, 195),
                  'green':  (22, 181, 64),
                  'red':    (204, 22, 22),
                  'orange': (245, 144, 12),
                  'cyan':   (10, 255, 226)}
        if shadow:
            end = [90]
        else:
            end = []
        border = Surface((BS, BS), pygame.SRCALPHA, 32)
        border.fill(list(map(lambda c: c*0.5, colors[color])) + end)
        BW = 2
        box = Surface((BS-BW*2, BS-BW*2), pygame.SRCALPHA, 32)
        boxarr = pygame.PixelArray(box)
        for x in range(len(boxarr)):
            for y in range(len(boxarr)):
                boxarr[x][y] = tuple(list(map(lambda c: min(255, int(c*r.uniform(0.8, 1.2))), colors[color])) + end) 
        del boxarr
        border.blit(box, Rect(BW, BW, 0, 0))
        return border
    def lock_tm(self):
        self.matrix = self.blend()
        lines_cleared = self.remove_lines()
        self.lines += lines_cleared
        if lines_cleared:
            if lines_cleared >= 4:
                self.linescleared_sound.play()
            self.score += 100 * (lines_cleared**2) * self.combo
            if not self.played_hsbeaten_sound and self.score > self.hs:
                if self.hs != 0:
                    self.hsbeaten_sound.play()
                self.played_hsbeaten_sound = True
        if self.lines >= self.level*10:
            self.levelup_sound.play()
            self.level += 1
        self.combo = self.combo + 1 if lines_cleared else 1
        self.set_tmes()
        if not self.blend():
            self.gameover_sound.play()
            self.gameover()   
        self.needs_redraw = True
    def remove_lines(self):
        lines = []
        for y in range(MH):
            line = (y, [])
            for x in range(MATRIX_WIDTH):
                if self.matrix[(y,x)]:
                    line[1].append(x)
            if len(line[1]) == MATRIX_WIDTH:
                lines.append(y)
        for line in sorted(lines):
            for x in range(MATRIX_WIDTH):
                self.matrix[(line,x)] = None
            for y in range(0, line+1)[::-1]:
                for x in range(MATRIX_WIDTH):
                    self.matrix[(y,x)] = self.matrix.get((y-1,x), None)
        return len(lines)
    def blend(self, shape=None, p=None, matrix=None, shadow=False):
        if shape is None:
            shape = self.rotated()
        if p is None:
            p = self.tm_p
        copy = dict(self.matrix if matrix is None else matrix)
        posY, posX = p
        for x in range(posX, posX+len(shape)):
            for y in range(posY, posY+len(shape)):
                if (copy.get((y, x), False) is False and shape[y-posY][x-posX]
                    or
                    copy.get((y,x)) and shape[y-posY][x-posX] and copy[(y,x)][0] != 'shadow'):
                    return False
                elif shape[y-posY][x-posX]:
                    copy[(y,x)] = ('shadow', self.shadow_block) if shadow else ('block', self.tm_block)
        return copy
    def construct_surface_of_next_tm(self):
        shape = self.next_tm.shape
        surf = Surface((len(shape)*BS, len(shape)*BS), pygame.SRCALPHA, 32)
        for y in range(len(shape)):
            for x in range(len(shape)):
                if shape[y][x]:
                    surf.blit(self.block(self.next_tm.color), (x*BS, y*BS))
        return surf
class Game(object):
    def main(self, screen):
        clock = pygame.time.Clock()
        self.matris = Matris()
        screen.blit(construct_nightmare(screen.get_size()), (0,0))
        matris_border = Surface((MATRIX_WIDTH*BS+BW*2, VISIBLE_MH*BS+BW*2))
        matris_border.fill(BRC)
        screen.blit(matris_border, (MATRIS_OFFSET,MATRIS_OFFSET))
        self.redraw()
        while True:
            try:
                timepassed = clock.tick(50)
                if self.matris.update((timepassed / 1000.) if not self.matris.paused else 0):
                    self.redraw()
            except GameOver:
                return
    def redraw(self):
        if not self.matris.paused:
            self.blit_next_tm(self.matris.surface_of_next_tm)
            self.blit_info()
            self.matris.draw_surface()
        pygame.display.flip()
    def blit_info(self):
        textcolor = (255, 255, 255)
        font = pygame.font.Font(None, 30)
        width = (WIDTH-(MATRIS_OFFSET+BS*MATRIX_WIDTH+BW*2)) - MATRIS_OFFSET*2
        def renderpair(text, val):
            text = font.render(text, True, textcolor)
            val = font.render(str(val), True, textcolor)
            surf = Surface((width, text.get_rect().height + BW*2), pygame.SRCALPHA, 32)
            surf.blit(text, text.get_rect(top=BW+10, left=BW+10))
            surf.blit(val, val.get_rect(top=BW+10, right=width-(BW+10)))
            return surf
        scoresurf = renderpair("Score", self.matris.score)
        levelsurf = renderpair("Level", self.matris.level)
        linessurf = renderpair("Lines", self.matris.lines)
        combosurf = renderpair("Combo", "x{}".format(self.matris.combo))
        height = 20 + (levelsurf.get_rect().height + 
                       scoresurf.get_rect().height +
                       linessurf.get_rect().height + 
                       combosurf.get_rect().height )
        area = Surface((width, height))
        area.fill(BRC)
        area.fill(BC, Rect(BW, BW, width-BW*2, height-BW*2))
        area.blit(levelsurf, (0,0))
        area.blit(scoresurf, (0, levelsurf.get_rect().height))
        area.blit(linessurf, (0, levelsurf.get_rect().height + scoresurf.get_rect().height))
        area.blit(combosurf, (0, levelsurf.get_rect().height + scoresurf.get_rect().height + linessurf.get_rect().height))
        screen.blit(area, area.get_rect(bottom=HEIGHT-MATRIS_OFFSET, centerx=TRICKY_CENTERX))
    def blit_next_tm(self, tm_surf):
        area = Surface((BS*5, BS*5))
        area.fill(BRC)
        area.fill(BC, Rect(BW, BW, BS*5-BW*2, BS*5-BW*2))
        areasize = area.get_size()[0]
        tm_surf_size = tm_surf.get_size()[0]
        center = areasize/2 - tm_surf_size/2
        area.blit(tm_surf, (center, center))
        screen.blit(area, area.get_rect(top=MATRIS_OFFSET, centerx=TRICKY_CENTERX))
class Menu(object):
    running = True
    def main(self, screen):
        clock = pygame.time.Clock()
        menu = kezmenu.KezMenu(
            ['Play!', lambda: Game().main(screen)],
            ['Quit', lambda: setattr(self, 'running', False)],
        )
        menu.p = (50, 50)
        menu.enableEffect('enlarge-font-on-focus', font=None, size=60, enlarge_factor=1.2, enlarge_time=0.3)
        menu.color,menu.focus_color = (255,255,255),(40, 200, 40)
        nightmare,hssurf = construct_nightmare(screen.get_size()),self.construct_hssurf()
        timepassed = clock.tick(30) / 1000.
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    exit()
            menu.update(events, timepassed)
            timepassed = clock.tick(30) / 1000.
            if timepassed > 1:
                hssurf = self.construct_hssurf()
            screen.blit(nightmare, (0,0))
            screen.blit(hssurf, hssurf.get_rect(right=WIDTH-50, bottom=HEIGHT-50))
            menu.draw(screen)
            pygame.display.flip()
    def construct_hssurf(self):
        font = pygame.font.Font(None, 50)
        hs = load_score()
        text = "hs: {}".format(hs)
        return font.render(text, True, (255,255,255))
def construct_nightmare(size):
    surf = Surface(size)
    boxsize,bordersize = 8,1
    vals = '1235'
    arr = pygame.PixelArray(surf)
    for x in range(0, len(arr), boxsize):
        for y in range(0, len(arr[x]), boxsize):
            color = int(''.join([r.choice(vals) + r.choice(vals) for _ in range(3)]), 16)
            for LX in range(x, x+(boxsize - bordersize)):
                for LY in range(y, y+(boxsize - bordersize)):
                    if LX < len(arr) and LY < len(arr[x]):
                        arr[LX][LY] = color
    del arr
    return surf
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MaTris")
    Menu().main(screen)