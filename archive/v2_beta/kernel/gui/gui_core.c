#include ""gui_core.h""
#include ""../management/monitor.h""

static uint16_t screen_width = 1024;
static uint16_t screen_height = 768;
static uint32_t* framebuffer = (uint32_t*)0xFD000000; // VBE framebuffer
static uint8_t bpp = 32;

void gui_init(void) {
    // Query VBE info
    vbe_info_t* vbe_info = (vbe_info_t*)0x2000;
    
    // Set text mode as fallback
    // Would normally call VBE BIOS interrupt 0x10
    
    gui_clear(0x00000000); // Black background
}

void gui_set_mode(uint16_t width, uint16_t height, uint8_t b) {
    screen_width = width;
    screen_height = height;
    bpp = b;
    // Set video mode via BIOS
}

void gui_clear(uint32_t color) {
    for (uint32_t i = 0; i < screen_width * screen_height; i++) {
        framebuffer[i] = color;
    }
}

void gui_draw_pixel(uint16_t x, uint16_t y, uint32_t color) {
    if (x < screen_width && y < screen_height) {
        framebuffer[y * screen_width + x] = color;
    }
}

void gui_draw_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint32_t color) {
    for (uint16_t i = x; i < x + w && i < screen_width; i++) {
        gui_draw_pixel(i, y, color);
        gui_draw_pixel(i, y + h - 1, color);
    }
    for (uint16_t i = y; i < y + h && i < screen_height; i++) {
        gui_draw_pixel(x, i, color);
        gui_draw_pixel(x + w - 1, i, color);
    }
}

void gui_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint32_t color) {
    for (uint16_t i = y; i < y + h && i < screen_height; i++) {
        for (uint16_t j = x; j < x + w && j < screen_width; j++) {
            gui_draw_pixel(j, i, color);
        }
    }
}

void gui_draw_text(uint16_t x, uint16_t y, const char* text, uint32_t color) {
    // Simple text rendering - would use bitmap fonts
    // For now, just a placeholder
}

void panel_init(panel_t* p, uint16_t x, uint16_t y, uint16_t w, uint16_t h, const char* title) {
    p->x = x; p->y = y;
    p->width = w; p->height = h;
    p->color = 0x004488; // Panel blue
}

void panel_draw(panel_t* p) {
    gui_fill_rect(p->x, p->y, p->width, p->height, p->color);
    gui_draw_rect(p->x, p->y, p->width, p->height, 0x00FFFFFF);
}
