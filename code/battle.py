from settings import *
from sprites import MonsterSprite, MonsterNameSprite, MonsterLevelSprite, MonsterStatsSprite, MonsterOutlineSprite
from groups import BattleSprites

class Battle:
    # main
    def __init__(self, player_monsters, opponent_monsters, monster_frames, bg_surf, fonts):
        # general
        self.display_surf = pygame.display.get_surface()
        self.bg_surf = bg_surf
        self.monster_frames = monster_frames
        self.fonts = fonts
        self.monster_data = {'player': player_monsters, 'opponent': opponent_monsters}
        
        # groups
        self.battle_sprites = BattleSprites()
        self.player_sprites = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()
        
        # control
        self.current_monster = None
        self.selection_mode = None
        self.selection_side = 'player'
        self.indexes = {
            'general': 0,
            'monster': 0,
            'attacks': 0,
            'switch': 0,
            'target': 0
        }
        
        self.setup()
        
    def setup(self):
        for entity, monster in self.monster_data.items():
            for index, monster in {k:v for k, v in monster.items() if k <= 2}.items():
                self.create_monster(monster, index, index, entity)
                
    def create_monster(self, monster, index, pos_index, entity):
        frames = self.monster_frames['monsters'][monster.name]
        outline_frames = self.monster_frames['outlines'][monster.name]
        if entity == 'player':
            pos = list(BATTLE_POSITIONS['left'].values())[pos_index]
            groups = (self.battle_sprites, self.player_sprites)
            frames = {state: [pygame.transform.flip(frame, True, False) for frame in frames] for state, frames in frames.items()}
            outline_frames = {state: [pygame.transform.flip(frame, True, False) for frame in frames] for state, frames in outline_frames.items()}
        else:
            pos = list(BATTLE_POSITIONS['right'].values())[pos_index]
            groups = (self.battle_sprites, self.opponent_sprites)
        
        monster_sprite = MonsterSprite(pos, frames, groups, monster, index, pos_index, entity)
        MonsterOutlineSprite(monster_sprite, self.battle_sprites, outline_frames)
        
        # ui
        name_pos = monster_sprite.rect.midleft + vector(16, -70) if entity == 'player' else monster_sprite.rect.midright + vector(-40, -70)
        name_sprite = MonsterNameSprite(name_pos, monster_sprite, self.battle_sprites, self.fonts['regular'])
        level_pos = name_sprite.rect.bottomleft if entity == 'player' else name_sprite.rect.bottomright
        MonsterLevelSprite(entity, level_pos, monster_sprite, self.battle_sprites, self.fonts['small'])
        MonsterStatsSprite(monster_sprite.rect.midbottom + vector(0, 20), monster_sprite, (150, 48), self.battle_sprites, self.fonts['small'])
    
    def input(self):
        if self.selection_mode and self.current_monster:
            keys  = pygame.key.get_just_pressed()
            
            match self.selection_mode:
                case 'general': limiter = len(BATTLE_CHOICES['full'])
                case 'attacks': limiter = len(self.current_monster.monster.get_abilities())
                
            if keys[pygame.K_DOWN]:
                self.indexes[self.selection_mode] = (self.indexes['general'] + 1) % limiter
            if keys[pygame.K_UP]:
                self.indexes[self.selection_mode] = (self.indexes['general'] - 1) % limiter
            if keys[pygame.K_SPACE]:
                if self.selection_mode == 'general':
                    if self.indexes['general'] == 0:
                        self.selection_mode = 'attacks'
                        
                    if self.indexes['general'] == 1:
                        self.update_all_monsters('resume')
                        self.current_monster, self.selection_mode = None, None
                        self.indexes['general'] = 0
                        
                    if self.indexes['general'] == 2:
                        self.selection_mode = 'switch'
                        
                    if self.indexes['general'] == 3:
                        print('catch')
    
    # battle system
    def check_active(self):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if monster_sprite.monster.initiative >= 100:
                self.update_all_monsters('pause')
                monster_sprite.monster.initiative = 0
                monster_sprite.set_highlight(True)
                self.current_monster = monster_sprite
                if self.player_sprites in monster_sprite.groups():
                    self.selection_mode = 'general'
    
    def update_all_monsters(self, option):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            monster_sprite.monster.paused = True if option == 'pause' else False
    
    # ui
    def draw_ui(self):
        if self.current_monster:
            if self.selection_mode == 'general':
                self.draw_general()
            if self.selection_mode == 'attacks':
                self.draw_attacks()
            if self.selection_mode =='switch':
                self.draw_switch()
    
    def draw_general(self):
        for index, (option, data_dict) in enumerate(BATTLE_CHOICES['full'].items()):
            if index == self.indexes['general']:
                surf = self.monster_frames['ui'][f"{data_dict['icon']}_highlight"]
            else:
                surf = pygame.transform.grayscale(self.monster_frames['ui'][data_dict['icon']])
            rect = surf.get_frect(center = self.current_monster.rect.midright + data_dict['pos'])
            self.display_surf.blit(surf, rect)
       
    def draw_attacks(self):
        # data
        abilities = self.current_monster.monster.get_abilities()
        width, height = 150, 200
        visible_attacks = 4
        item_height = height / visible_attacks
        v_offset = 0
        
        # background
        bg_rect = pygame.FRect((0,0), (width,height)).move_to(midleft = self.current_monster.rect.midright + vector(20,0))
        pygame.draw.rect(self.display_surf, COLORS['white'], bg_rect, 0, 5)
        
        for index, ability in enumerate(abilities):
            selected = index == self.indexes['attacks']
            
            # text
            text_color = COLORS['light']
            text_surf = self.fonts['regular'].render(ability, False, text_color)
            
            # rect
            text_rect = text_surf.get_frect(center = bg_rect.midtop + vector(0, item_height / 2 + index * item_height + v_offset))
    
            # draw 
            self.display_surf.blit(text_surf, text_rect)
    
    def draw_switch(self):
        pass   
    
    def update(self, dt):
        # update
        self.input()
        self.battle_sprites.update(dt)
        self.check_active()
        
        # drawing 
        self.display_surf.blit(self.bg_surf, (0, 0))
        self.battle_sprites.draw(self.current_monster)
        self.draw_ui()