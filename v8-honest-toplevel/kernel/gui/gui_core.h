#ifndef GUI_CORE_H
#define GUI_CORE_H

#include <stdint.h>

// VBE Info Structure
typedef struct {
    uint32_t signature;
    uint16_t version;
    uint16_t oem_string_offset;
    uint32_t oem_string_seg;
    uint32_t capabilities[4];
    uint16_t video_mode_offset;
    uint16_t total_memory;
    uint16_t oem_software_rev;
    uint16_t vendor_name_offset;
    uint32_t vendor_name_seg;
    uint16_t product_name_offset;
    uint32_t product_name_seg;
} __attribute__((packed)) vbe_info_t;

// Drawing functions
void gui_init(void);
void gui_set_mode(uint16_t width, uint16_t height, uint8_t bpp);
void gui_clear(uint32_t color);
void gui_draw_pixel(uint16_t x, uint16_t y, uint32_t color);
void gui_draw_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint32_t color);
void gui_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint32_t color);
void gui_draw_text(uint16_t x, uint16_t y, const char* text, uint32_t color);

// Panel management
void panel_init(panel_t* p, uint16_t x, uint16_t y, uint16_t w, uint16_t h, const char* title);
void panel_draw(panel_t* p);
void panel_update(panel_t* p);

#endif
