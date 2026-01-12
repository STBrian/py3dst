#pragma once

#ifndef __cplusplus
#include <stdbool.h>
#endif
#include <stdlib.h>
#include <stdint.h>

#define TEX3DST_RGBA8 0
#define TEX3DST_RGB8 1
#define TEX3DST_RGBA5551 2
#define TEX3DST_RGB565 3
#define TEX3DST_RGBA4 4
#define TEX3DST_LA8 5
#define TEX3DST_hilo8 6
#define TEX3DST_L8 7
#define TEX3DST_A8 8
#define TEX3DST_LA4 9

#ifdef _WIN32
  #define TEX3DSTAPI __declspec(dllexport)
#else
  #define TEX3DSTAPI
#endif

typedef struct _formatInfo {
    uint32_t id;
    bool supported;
    unsigned int pixel_size;
    unsigned int pixel_channels;
} Format3dstInfo;

typedef struct _pixelData {
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t a;
    uint8_t l;
} PixelData;

struct _size {
    uint32_t width;
    uint32_t height;
};

typedef struct _headerTexture3dst {
    uint32_t mode;
    uint32_t format;
    struct _size full_size;
    struct _size size;
    uint32_t mip_level;
} HeaderTexture3dst;

#ifndef __cplusplus
typedef struct Texture3dst Texture3dst;
#endif

#ifdef __cplusplus

#include <string>

class Texture3dst {
    private:
        HeaderTexture3dst header;
        uint8_t *textureData = NULL;
        uint8_t *np_data = NULL;
    public:
        struct _size size;

        enum Tex3dstState {
            SUCCESS,
            NOLOADED,
            FILEERROR,
            NOSIG,
            UNSUPPORTEDMODE,
            UNSUPPORTEDFORMAT,
            INVALIDSIZE,
            INVALIDMIPLEVEL,
            MEMORYERROR,
            UNEXPECTEDEOF,
            READERROR,
            INVALIDPOSITION,
            OTHER
        };

        Texture3dst::Tex3dstState texstate = Texture3dst::Tex3dstState::NOLOADED;
        Texture3dst::Tex3dstState opstate = Texture3dst::Tex3dstState::SUCCESS;

        enum Tex3dstFormats {
            RGBA8 = 0,
            RGB8 = 1,
            RGBA5551 = 2,
            RGB565 = 3,
            RGBA4 = 4,
            LA8 = 5,
            HILO8 = 6,
            L8 = 7,
            A8 = 8,
            LA4 = 9
        };

        Texture3dst() {};
        ~Texture3dst() {
            if (this->textureData)
                free(this->textureData);
            if (this->np_data)
                free(this->np_data);
        }

        HeaderTexture3dst& getHeader() {
            return this->header;
        }

        void open(const std::string &path);

        void create(uint32_t width, uint32_t height, uint32_t mip_level, Texture3dst::Tex3dstFormats format);

        void flipVertical();

        void setPixel(uint32_t x, uint32_t y, PixelData *pixel_data);

        void getPixel(uint32_t x, uint32_t y, PixelData *pixel_data);

        void crop(Texture3dst &dst, uint32_t x1, uint32_t y1, uint32_t x2, uint32_t y2);

        bool paste(uint32_t x, uint32_t y, Texture3dst &tex2);

        void getFormatInfo(Format3dstInfo *dst);

        bool compare(Texture3dst &tex2, bool ignore_alpha);

        void save(const std::string &path);

        /* The returned buffer is valid until next raw call or object destruction */
        uint8_t* to_raw();

        uint8_t* crop_to_raw(uint32_t x1, uint32_t y1, uint32_t x2, uint32_t y2);

        void create_formatint(uint32_t width, uint32_t height, uint32_t mip_level, int format);
    
    private:
        void _formatPixelData(uint8_t *out_data, Format3dstInfo *fmtInfo);

        void _processMipLevels(uint8_t *texdata, uint32_t texwidth, uint32_t texheight, Format3dstInfo *fmtInfo, uint8_t mip_level);
};

#endif

#ifdef __cplusplus
extern "C" {
#endif

TEX3DSTAPI Texture3dst* Tex3DSTNewObject();

TEX3DSTAPI void Tex3DSTGetHeader(Texture3dst* obj, HeaderTexture3dst* header);

TEX3DSTAPI void Tex3DSTOpen(Texture3dst* obj, const char *path);

TEX3DSTAPI void Tex3DSTCreate(Texture3dst* obj, uint32_t width, uint32_t height, uint32_t mip_level, uint32_t format);

TEX3DSTAPI void Tex3DSTFlipVertical(Texture3dst* obj);

TEX3DSTAPI void Tex3DSTSetPixel(Texture3dst* obj, uint32_t x, uint32_t y, PixelData *pixel_data);

TEX3DSTAPI void Tex3DSTGetPixel(Texture3dst* obj, uint32_t x, uint32_t y, PixelData *pixel_data);

TEX3DSTAPI void Tex3DSTCrop(Texture3dst* src, Texture3dst* dst, uint32_t x1, uint32_t y1, uint32_t x2, uint32_t y2);

/* The returned buffer is valid until next raw call or object destruction */
TEX3DSTAPI uint8_t* Tex3DSTGetRaw(Texture3dst* obj);

TEX3DSTAPI bool Tex3DSTPaste(Texture3dst* obj, Texture3dst* tex2, uint32_t x, uint32_t y);

TEX3DSTAPI void Tex3DSTGetFormatInfo(Texture3dst* obj, Format3dstInfo *dst);

TEX3DSTAPI bool Tex3DSTCompare(Texture3dst* obj, Texture3dst* tex2, bool ignore_alpha);

TEX3DSTAPI void Tex3DSTSave(Texture3dst* obj, const char *path);

TEX3DSTAPI void Tex3DSTFree(Texture3dst* obj);

#ifdef __cplusplus
}
#endif