from PIL import Image

from tools import pixel


def test_upscale_blocks_uniform():
    small = Image.new("RGB", (pixel.PW, pixel.PH))
    for y in range(pixel.PH):
        for x in range(pixel.PW):
            small.putpixel((x, y), ((x * 7) % 256, (y * 11) % 256, (x + y) % 256))
    big = pixel.upscale(small)
    assert big.size == (3840, 2160)
    for bx, by in ((0, 0), (17, 33), (479, 269), (240, 135)):
        block = big.crop((bx * 8, by * 8, bx * 8 + 8, by * 8 + 7))  # rows 0..6; row 7 is the scanline
        assert len(set(block.get_flattened_data())) == 1


def test_edge_shade_full_strength_in_zones():
    img = Image.new("RGB", (pixel.PW, pixel.PH), (255, 255, 255))
    pixel.edge_shade(img, strength=0.9)
    for box in ((0, 0, pixel.PW, 52), (0, 0, 118, pixel.PH), (0, 230, pixel.PW, pixel.PH)):
        worst = max(img.crop(box).get_flattened_data(), key=sum)
        bound = round(255 * 0.1 + max(pixel.SHADE) * 0.9)  # full strength: 10% of white + 90% shade colour
        assert max(worst) <= bound, (box, worst)


def test_edge_shade_leaves_the_centre_alone():
    img = Image.new("RGB", (pixel.PW, pixel.PH), (255, 255, 255))
    pixel.edge_shade(img, strength=0.9)
    assert img.getpixel((400, 150)) == (255, 255, 255)
